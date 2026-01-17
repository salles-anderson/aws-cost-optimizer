# AWS Cost Optimizer

Automated cost reduction solution for AWS environments using reusable Terraform modules to stop/start resources based on schedules.

![AWS](https://img.shields.io/badge/AWS-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Terraform Cloud](https://img.shields.io/badge/Terraform_Cloud-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Modules Used](#modules-used)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup Guide](#setup-guide)
- [Usage](#usage)
- [Tag Your Resources](#tag-your-resources)
- [Schedule Configuration](#schedule-configuration)
- [Cost Savings Estimate](#cost-savings-estimate)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Related Resources](#related-resources)
- [Author](#author)

## Overview

This solution automatically stops AWS resources in non-production environments (dev, homolog, staging) outside business hours, reducing infrastructure costs by up to 65%.

### Why Cost Optimization?

In many organizations, non-production environments run 24/7 even when they're not being used. This leads to unnecessary costs:

- **Development environments** are typically used only during business hours (8-10 hours/day)
- **Homolog/QA environments** are used for testing during business hours
- **Staging environments** are used for final validation before production
- **Production environments** must remain running 24/7 (NOT targeted by this solution)

By stopping resources during off-hours (nights and weekends), you can reduce costs by up to **65%** on non-production infrastructure.

### Why Stop/Start Instead of Destroy?

For RDS and DocumentDB, **destroy/recreate is not viable**:

- Snapshots generation takes time and costs money
- Restore process is slow and error-prone
- Database configurations and parameters need to be recreated
- Endpoints change, requiring application updates
- **Total cost of destroy/recreate exceeds 24/7 running costs**

**Stop/Start is the optimal solution**: maintains data, configurations, and endpoints while eliminating compute costs.

### Target Environments

| Environment | Use Case | Cost Optimization |
|-------------|----------|-------------------|
| **Development** | Daily development work | Stop outside business hours |
| **Homolog** | QA and integration testing | Stop outside business hours |
| **Staging** | Pre-production validation | Stop outside business hours |
| **Sandbox** | Experimentation and learning | Stop outside business hours |
| **Production** | Live customer-facing | **DO NOT STOP** |

## Architecture

<div align="center">
  <img src="docs/AWS Cost Optimizer - Automated Resource Scheduling.png" alt="Architecture Diagram" width="800"/>
</div>

### Components

| Component | Description |
|-----------|-------------|
| **Terraform Modules** | Reusable modules from [modules-aws-tf](https://github.com/salles-anderson/modules-aws-tf) |
| **EventBridge Scheduler** | Triggers Lambda functions based on cron schedule |
| **Lambda Functions** | Stop/Start resources (one per resource type) |
| **IAM Roles** | Least-privilege permissions for each Lambda |
| **CloudWatch Logs** | Execution logs for monitoring |

## Modules Used

This project uses modules from [modules-aws-tf](https://github.com/salles-anderson/modules-aws-tf):

| Module | Path | Description |
|--------|------|-------------|
| **ec2-scheduler** | `modules/cost-optimization/ec2-scheduler` | Stop/Start EC2 instances |
| **rds-scheduler** | `modules/cost-optimization/rds-scheduler` | Stop/Start RDS instances and Aurora clusters |
| **documentdb-scheduler** | `modules/cost-optimization/documentdb-scheduler` | Stop/Start DocumentDB clusters |

### Module Features

- **Tag-based discovery**: Automatically finds resources by tag
- **Timezone support**: Configure schedules in your local timezone
- **Re-stop feature**: Handles RDS/DocumentDB 7-day auto-start limitation
- **CloudWatch Logs**: Built-in logging with configurable retention

## How It Works

### Stop Flow (19:00 BRT)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EventBridge   │───►│  Lambda (Stop)  │───►│ Tagged Resources│
│   Scheduler     │    │                 │    │                 │
│ cron(0 19 *)    │    │ - Query by tag  │    │ EC2, RDS,       │
└─────────────────┘    │ - Stop each     │    │ DocumentDB      │
                       └─────────────────┘    └─────────────────┘
```

### Start Flow (08:00 BRT)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EventBridge   │───►│  Lambda (Start) │───►│ Tagged Resources│
│   Scheduler     │    │                 │    │                 │
│ cron(0 8 *)     │    │ - Query stopped │    │ EC2, RDS,       │
└─────────────────┘    │ - Start each    │    │ DocumentDB      │
                       └─────────────────┘    └─────────────────┘
```

## Project Structure

```
aws-cost-optimizer/
├── terraform/
│   ├── backend.tf                 # Terraform Cloud configuration
│   ├── main.tf                    # Module calls
│   ├── outputs.tf                 # Output values
│   ├── variables.tf               # Input variables
│   └── terraform.tfvars.example   # Example values
├── docs/
│   ├── architecture.png           # Architecture diagram
│   └── eraser-prompt.md           # Diagram generation prompt
├── .gitignore
└── README.md
```

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0 installed locally
- Terraform Cloud account (free tier available)

## Setup Guide

### Terraform Cloud Setup

#### Step 1: Create Workspace

1. Log in to [Terraform Cloud](https://app.terraform.io)
2. Create a new workspace named `aws-cost-optimizer`
3. Select **CLI-driven workflow**

#### Step 2: Configure AWS Credentials

Navigate to your workspace **Settings > Variables** and add:

| Key | Value | Category | Sensitive |
|-----|-------|----------|-----------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key | Environment variable | ✅ Yes |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Key | Environment variable | ✅ Yes |
| `AWS_REGION` | `us-east-1` (or your region) | Environment variable | ❌ No |

**Steps:**
1. Go to workspace > **Variables** tab
2. Under **Environment Variables**, click **+ Add variable**
3. Enter `AWS_ACCESS_KEY_ID` as key
4. Enter your AWS Access Key as value
5. Check **Sensitive** checkbox
6. Click **Save variable**
7. Repeat for `AWS_SECRET_ACCESS_KEY`

#### Step 3: Configure Terraform Variables (Optional)

| Key | Value | Category |
|-----|-------|----------|
| `target_environment` | `dev` | Terraform variable |
| `schedule_timezone` | `America/Sao_Paulo` | Terraform variable |
| `stop_schedule` | `cron(0 19 ? * MON-FRI *)` | Terraform variable |
| `start_schedule` | `cron(0 8 ? * MON-FRI *)` | Terraform variable |

#### Step 4: Update Backend Configuration

Update `terraform/backend.tf` with your organization:

```hcl
terraform {
  cloud {
    organization = "your-organization-name"  # <-- Change this

    workspaces {
      name = "aws-cost-optimizer"
    }
  }
}
```

#### Step 5: Deploy

```bash
cd terraform

# Login to Terraform Cloud
terraform login

# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply
```

## Usage

### Deploy for Multiple Environments

Create separate workspaces for each environment:

**Development:**
```hcl
target_environment = "dev"
```

**Homolog:**
```hcl
target_environment = "homolog"
```

**Staging:**
```hcl
target_environment = "staging"
```

## Tag Your Resources

For resources to be managed, add the following tag:

```
Key: Environment
Value: dev | homolog | staging
```

### Terraform Examples

**EC2 Instance:**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-dev"
    Environment = "dev"
  }
}
```

**RDS Instance:**
```hcl
resource "aws_db_instance" "database" {
  identifier     = "mydb-dev"
  engine         = "postgres"
  instance_class = "db.t3.micro"

  tags = {
    Name        = "mydb-dev"
    Environment = "dev"
  }
}
```

**DocumentDB Cluster:**
```hcl
resource "aws_docdb_cluster" "docdb" {
  cluster_identifier = "docdb-dev"
  engine             = "docdb"

  tags = {
    Name        = "docdb-dev"
    Environment = "dev"
  }
}
```

## Schedule Configuration

### Default Schedules (São Paulo timezone)

| Action | Time | Cron Expression |
|--------|------|-----------------|
| Stop | 19:00 | `cron(0 19 ? * MON-FRI *)` |
| Start | 08:00 | `cron(0 8 ? * MON-FRI *)` |

### Custom Schedules

Configure in Terraform Cloud variables:

```hcl
schedule_timezone = "America/Sao_Paulo"
stop_schedule     = "cron(0 18 ? * MON-FRI *)"  # 18:00
start_schedule    = "cron(0 9 ? * MON-FRI *)"   # 09:00
```

## Cost Savings Estimate

| Resource Type | Instance Size | Hourly Cost | Daily Savings (13h) | Monthly Savings |
|---------------|---------------|-------------|---------------------|-----------------|
| EC2 | t3.medium | $0.0416 | $0.54 | ~$11.88 |
| RDS | db.t3.medium | $0.068 | $0.88 | ~$19.36 |
| DocumentDB | db.t3.medium | $0.078 | $1.01 | ~$22.22 |

*Savings calculated for 22 business days/month, 13 hours off-time per day*

### Example: Typical Dev Environment

- 5x t3.medium EC2: **$59.40/month**
- 2x db.t3.medium RDS: **$38.72/month**
- 1x db.t3.medium DocumentDB: **$22.22/month**
- **Total Savings: ~$120/month (~$1,440/year)**

## Monitoring

### CloudWatch Logs

Lambda execution logs are available in CloudWatch:

- `/aws/lambda/{project_name}-ec2-scheduler`
- `/aws/lambda/{project_name}-rds-scheduler`
- `/aws/lambda/{project_name}-documentdb-scheduler`

## Troubleshooting

### Resources Not Stopping

1. Verify tags are correctly applied
2. Check Lambda execution logs in CloudWatch
3. Verify scheduler is enabled (`enable_scheduler = true`)

### RDS Auto-Start After 7 Days

RDS and DocumentDB automatically start after 7 days when stopped. The modules include a **re-stop** feature to handle this:

```hcl
enable_restop_schedule = true
```

## Related Resources

- [AWS Instance Scheduler](https://aws.amazon.com/solutions/implementations/instance-scheduler-on-aws/) - AWS official solution
- [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) - Analyze AWS costs
- [AWS Trusted Advisor](https://aws.amazon.com/premiumsupport/technology/trusted-advisor/) - Cost optimization recommendations
- [Terraform Modules Repository](https://github.com/salles-anderson/modules-aws-tf) - Reusable Terraform modules

## Author

**Anderson Sales** - DevOps Cloud Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/salesanderson)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/salles-anderson)
