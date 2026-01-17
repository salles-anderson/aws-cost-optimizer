output "stop_lambda_arn" {
  description = "ARN of the Stop Lambda function"
  value       = aws_lambda_function.stop.arn
}

output "start_lambda_arn" {
  description = "ARN of the Start Lambda function"
  value       = aws_lambda_function.start.arn
}

output "stop_lambda_name" {
  description = "Name of the Stop Lambda function"
  value       = aws_lambda_function.stop.function_name
}

output "start_lambda_name" {
  description = "Name of the Start Lambda function"
  value       = aws_lambda_function.start.function_name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = aws_iam_role.lambda_role.arn
}

output "scheduler_role_arn" {
  description = "ARN of the EventBridge Scheduler IAM role"
  value       = aws_iam_role.scheduler_role.arn
}

output "stop_schedule_arn" {
  description = "ARN of the Stop schedule"
  value       = var.enable_scheduler ? aws_scheduler_schedule.stop[0].arn : null
}

output "start_schedule_arn" {
  description = "ARN of the Start schedule"
  value       = var.enable_scheduler ? aws_scheduler_schedule.start[0].arn : null
}

output "target_environments" {
  description = "Environments being managed"
  value       = var.target_environments
}

output "schedules" {
  description = "Configured schedules"
  value = {
    stop  = var.stop_schedule
    start = var.start_schedule
  }
}
