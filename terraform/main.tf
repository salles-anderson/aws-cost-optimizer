terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
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

module "ec2_scheduler" {
  source = "github.com/salles-anderson/modules-aws-tf//modules/cost-optimization/ec2-scheduler"

  project_name       = var.project_name
  resource_tag_key   = var.environment_tag_key
  resource_tag_value = var.target_environment
  enable_schedule    = var.enable_scheduler
  schedule_timezone  = var.schedule_timezone
  stop_schedule      = var.stop_schedule
  start_schedule     = var.start_schedule
  log_retention_in_days = 14

  tags = var.tags
}

module "rds_scheduler" {
  source = "github.com/salles-anderson/modules-aws-tf//modules/cost-optimization/rds-scheduler"

  project_name       = var.project_name
  resource_tag_key   = var.environment_tag_key
  resource_tag_value = var.target_environment
  enable_schedule    = var.enable_scheduler
  schedule_timezone  = var.schedule_timezone
  stop_schedule      = var.stop_schedule
  start_schedule     = var.start_schedule
  enable_restop_schedule = true
  log_retention_in_days  = 14

  tags = var.tags
}

module "documentdb_scheduler" {
  source = "github.com/salles-anderson/modules-aws-tf//modules/cost-optimization/documentdb-scheduler"

  project_name       = var.project_name
  resource_tag_key   = var.environment_tag_key
  resource_tag_value = var.target_environment
  enable_schedule    = var.enable_scheduler
  schedule_timezone  = var.schedule_timezone
  stop_schedule      = var.stop_schedule
  start_schedule     = var.start_schedule
  log_retention_in_days = 14

  tags = var.tags
}
