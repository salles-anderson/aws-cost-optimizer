variable "project_name" {
  description = "Project name"
  type        = string
  default     = "aws-cost-optimizer"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment_tag_key" {
  description = "Tag key to identify environments"
  type        = string
  default     = "Environment"
}

variable "target_environment" {
  description = "Environment tag value to target (e.g., dev, homolog, staging)"
  type        = string
  default     = "dev"
}

variable "schedule_timezone" {
  description = "Timezone for schedules"
  type        = string
  default     = "America/Sao_Paulo"
}

variable "stop_schedule" {
  description = "Cron expression for stopping resources"
  type        = string
  default     = "cron(0 19 ? * MON-FRI *)"
}

variable "start_schedule" {
  description = "Cron expression for starting resources"
  type        = string
  default     = "cron(0 8 ? * MON-FRI *)"
}

variable "enable_scheduler" {
  description = "Enable/disable the scheduler"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
