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

variable "target_environments" {
  description = "Environments to stop/start"
  type        = list(string)
  default     = ["dev", "homolog", "staging"]
}

variable "stop_schedule" {
  description = "Cron expression for stopping resources (UTC)"
  type        = string
  default     = "cron(0 22 ? * MON-FRI *)" # 22:00 UTC = 19:00 BRT
}

variable "start_schedule" {
  description = "Cron expression for starting resources (UTC)"
  type        = string
  default     = "cron(0 11 ? * MON-FRI *)" # 11:00 UTC = 08:00 BRT
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
