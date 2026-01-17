output "ec2_scheduler" {
  description = "EC2 Scheduler module outputs"
  value = {
    lambda_function_name = module.ec2_scheduler.lambda_function_name
    lambda_function_arn  = module.ec2_scheduler.lambda_function_arn
  }
}

output "rds_scheduler" {
  description = "RDS Scheduler module outputs"
  value = {
    lambda_function_name = module.rds_scheduler.lambda_function_name
    lambda_function_arn  = module.rds_scheduler.lambda_function_arn
  }
}

output "documentdb_scheduler" {
  description = "DocumentDB Scheduler module outputs"
  value = {
    lambda_function_name = module.documentdb_scheduler.lambda_function_name
    lambda_function_arn  = module.documentdb_scheduler.lambda_function_arn
  }
}

output "target_environment" {
  description = "Environment being managed"
  value       = var.target_environment
}

output "schedules" {
  description = "Configured schedules"
  value = {
    timezone = var.schedule_timezone
    stop     = var.stop_schedule
    start    = var.start_schedule
  }
}
