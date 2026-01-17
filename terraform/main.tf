terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(var.tags, {
      Project   = var.project_name
      ManagedBy = "terraform"
    })
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${local.region}:${local.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:StartInstances",
          "ec2:StopInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "rds:ListTagsForResource",
          "rds:StartDBInstance",
          "rds:StopDBInstance",
          "rds:StartDBCluster",
          "rds:StopDBCluster"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "docdb:DescribeDBClusters",
          "docdb:ListTagsForResource",
          "docdb:StartDBCluster",
          "docdb:StopDBCluster"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:ListClusters",
          "ecs:ListServices",
          "ecs:DescribeServices",
          "ecs:UpdateService",
          "ecs:ListTagsForResource",
          "ecs:TagResource"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "sts:GetCallerIdentity"
        Resource = "*"
      }
    ]
  })
}

data "archive_file" "stop_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/stop/handler.py"
  output_path = "${path.module}/../lambda/stop/handler.zip"
}

data "archive_file" "start_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/start/handler.py"
  output_path = "${path.module}/../lambda/start/handler.zip"
}

resource "aws_lambda_function" "stop" {
  filename         = data.archive_file.stop_lambda.output_path
  function_name    = "${var.project_name}-stop"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.stop_lambda.output_base64sha256
  runtime          = "python3.12"
  timeout          = 300
  memory_size      = 256

  environment {
    variables = {
      TAG_KEY     = var.environment_tag_key
      TAG_VALUES  = jsonencode(var.target_environments)
      LOG_LEVEL   = "INFO"
    }
  }
}

resource "aws_lambda_function" "start" {
  filename         = data.archive_file.start_lambda.output_path
  function_name    = "${var.project_name}-start"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.start_lambda.output_base64sha256
  runtime          = "python3.12"
  timeout          = 300
  memory_size      = 256

  environment {
    variables = {
      TAG_KEY     = var.environment_tag_key
      TAG_VALUES  = jsonencode(var.target_environments)
      LOG_LEVEL   = "INFO"
    }
  }
}

resource "aws_cloudwatch_log_group" "stop" {
  name              = "/aws/lambda/${aws_lambda_function.stop.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "start" {
  name              = "/aws/lambda/${aws_lambda_function.start.function_name}"
  retention_in_days = 14
}

resource "aws_iam_role" "scheduler_role" {
  name = "${var.project_name}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "scheduler_policy" {
  name = "${var.project_name}-scheduler-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = [
          aws_lambda_function.stop.arn,
          aws_lambda_function.start.arn
        ]
      }
    ]
  })
}

resource "aws_scheduler_schedule" "stop" {
  count = var.enable_scheduler ? 1 : 0

  name       = "${var.project_name}-stop-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = var.stop_schedule

  target {
    arn      = aws_lambda_function.stop.arn
    role_arn = aws_iam_role.scheduler_role.arn

    input = jsonencode({
      tag_key    = var.environment_tag_key
      tag_values = var.target_environments
    })
  }
}

resource "aws_scheduler_schedule" "start" {
  count = var.enable_scheduler ? 1 : 0

  name       = "${var.project_name}-start-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = var.start_schedule

  target {
    arn      = aws_lambda_function.start.arn
    role_arn = aws_iam_role.scheduler_role.arn

    input = jsonencode({
      tag_key    = var.environment_tag_key
      tag_values = var.target_environments
    })
  }
}
