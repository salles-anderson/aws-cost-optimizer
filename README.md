# AWS Cost Optimizer

Automated cost reduction solution for AWS environments using Lambda functions and EventBridge Scheduler to stop/start resources based on schedules.

![AWS](https://img.shields.io/badge/AWS-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Supported Resources](#supported-resources)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup Guide](#setup-guide)
  - [Terraform Cloud Setup](#terraform-cloud-setup)
  - [GitHub Actions Setup](#github-actions-setup)
- [Usage](#usage)
- [Tag Your Resources](#tag-your-resources)
- [Schedule Configuration](#schedule-configuration)
- [Cost Savings Estimate](#cost-savings-estimate)
- [Manual Invocation](#manual-invocation)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Contributing](#contributing)
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

### Target Environments

| Environment | Use Case | Cost Optimization |
|-------------|----------|-------------------|
| **Development** | Daily development work | Stop outside business hours |
| **Homolog** | QA and integration testing | Stop outside business hours |
| **Staging** | Pre-production validation | Stop outside business hours |
| **Sandbox** | Experimentation and learning | Stop outside business hours |
| **Training** | Training and demos | Stop outside business hours |
| **Production** | Live customer-facing | **DO NOT STOP** |

### Services That Benefit from Scheduling

| Service | Why It Benefits | Typical Savings |
|---------|-----------------|-----------------|
| **EC2 Instances** | Pay per hour when running | 60-70% |
| **RDS Instances** | Pay per hour when running | 60-70% |
| **Aurora Clusters** | Pay per hour for instances | 60-70% |
| **DocumentDB** | Pay per hour for instances | 60-70% |
| **ECS (Fargate)** | Pay per vCPU/memory per hour | 60-70% |
| **ECS (EC2)** | Underlying EC2 still charged | 60-70% |

### Services NOT Recommended for Scheduling

| Service | Reason |
|---------|--------|
| **S3** | Storage charged regardless of access |
| **DynamoDB (On-Demand)** | Pay only for reads/writes |
| **Lambda** | Pay only for invocations |
| **CloudFront** | CDN needs to be always available |
| **Route 53** | DNS needs to be always available |
| **ElastiCache** | Long warm-up time, may lose data |

### Key Features

- **Multi-Resource Support**: EC2, RDS, Aurora, DocumentDB, ECS
- **Tag-Based Selection**: Target specific environments using tags
- **Flexible Scheduling**: Configurable cron expressions for stop/start times
- **State Preservation**: ECS services remember their original desired count
- **Infrastructure as Code**: Terraform with Terraform Cloud integration
- **CI/CD Ready**: GitHub Actions for Lambda deployment
- **Monitoring**: CloudWatch Logs integration

## Architecture

<div align="center">
  <img src="docs/AWS Cost Optimizer - Automated Resource Scheduling.png" alt="Architecture Diagram" width="800"/>
</div>

### Components

| Component | Description |
|-----------|-------------|
| **EventBridge Scheduler** | Triggers Lambda functions based on cron schedule |
| **Stop Lambda** | Identifies and stops tagged resources |
| **Start Lambda** | Identifies and starts previously stopped resources |
| **IAM Role** | Provides necessary permissions for Lambda functions |
| **CloudWatch Logs** | Stores execution logs for monitoring |

### Flow Description

1. **Stop Flow (19:00 BRT)**
   - EventBridge Scheduler triggers Stop Lambda
   - Lambda queries resources with `Environment` tag
   - For each resource type:
     - EC2: Stop running instances
     - RDS: Stop available instances
     - Aurora: Stop available clusters
     - DocumentDB: Stop available clusters
     - ECS: Scale services to 0 (save original count in tags)

2. **Start Flow (08:00 BRT)**
   - EventBridge Scheduler triggers Start Lambda
   - Lambda queries stopped resources with `Environment` tag
   - For each resource type:
     - EC2: Start stopped instances
     - RDS: Start stopped instances
     - Aurora: Start stopped clusters
     - DocumentDB: Start stopped clusters
     - ECS: Restore services to original desired count

## Supported Resources

| Resource | Stop Action | Start Action | Status Check |
|----------|-------------|--------------|--------------|
| EC2 Instances | `stop_instances()` | `start_instances()` | `instance-state-name: running/stopped` |
| RDS Instances | `stop_db_instance()` | `start_db_instance()` | `DBInstanceStatus: available/stopped` |
| Aurora Clusters | `stop_db_cluster()` | `start_db_cluster()` | `Status: available/stopped` |
| DocumentDB Clusters | `stop_db_cluster()` | `start_db_cluster()` | `Status: available/stopped` |
| ECS Services | `update_service(desiredCount=0)` | `update_service(desiredCount=N)` | `desiredCount: 0/>0` |

### Important Notes

- **RDS**: Only standalone instances are stopped (not Aurora cluster members)
- **ECS**: Original desired count is stored in the `OriginalDesiredCount` tag
- **Aurora/DocumentDB**: Clusters are stopped, which stops all member instances

## How It Works

### Stop Process

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EventBridge   │───►│  Stop Lambda    │───►│ AWS Resources   │
│   Scheduler     │    │                 │    │ (EC2,RDS,ECS...)│
│ (22:00 UTC)     │    │ - Query by tag  │    │                 │
└─────────────────┘    │ - Stop each     │    │ Status: STOPPED │
                       └─────────────────┘    └─────────────────┘
```

### Start Process

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EventBridge   │───►│  Start Lambda   │───►│ AWS Resources   │
│   Scheduler     │    │                 │    │ (EC2,RDS,ECS...)│
│ (11:00 UTC)     │    │ - Query stopped │    │                 │
└─────────────────┘    │ - Start each    │    │ Status: RUNNING │
                       └─────────────────┘    └─────────────────┘
```

## Project Structure

```
aws-cost-optimizer/
├── .github/
│   └── workflows/
│       └── lambda-deploy.yml      # CI/CD for Lambda deployment
├── lambda/
│   ├── start/
│   │   └── handler.py             # Start Lambda function
│   └── stop/
│       └── handler.py             # Stop Lambda function
├── terraform/
│   ├── backend.tf                 # Terraform Cloud backend config
│   ├── main.tf                    # Main infrastructure definition
│   ├── outputs.tf                 # Output values
│   ├── variables.tf               # Input variables
│   └── terraform.tfvars.example   # Example variable values
├── docs/
│   └── architecture.png           # Architecture diagram
├── .gitignore
└── README.md
```

### File Descriptions

| File | Purpose |
|------|---------|
| `lambda/stop/handler.py` | Python function that stops resources based on tags |
| `lambda/start/handler.py` | Python function that starts stopped resources |
| `terraform/main.tf` | Lambda functions, IAM roles, EventBridge Scheduler |
| `terraform/backend.tf` | Terraform Cloud workspace configuration |
| `terraform/variables.tf` | Configurable parameters (schedules, environments, tags) |
| `.github/workflows/lambda-deploy.yml` | GitHub Actions workflow for Lambda deployment |

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0 installed locally
- Terraform Cloud account (free tier available)
- GitHub repository
- AWS CLI configured (for local testing)

### Required AWS Permissions

The Lambda function requires permissions for:

- EC2: `DescribeInstances`, `StartInstances`, `StopInstances`
- RDS: `DescribeDBInstances`, `DescribeDBClusters`, `ListTagsForResource`, `StartDBInstance`, `StopDBInstance`, `StartDBCluster`, `StopDBCluster`
- DocumentDB: `DescribeDBClusters`, `ListTagsForResource`, `StartDBCluster`, `StopDBCluster`
- ECS: `ListClusters`, `ListServices`, `DescribeServices`, `UpdateService`, `ListTagsForResource`, `TagResource`
- CloudWatch Logs: `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`
- STS: `GetCallerIdentity`

## Setup Guide

### Terraform Cloud Setup

#### Step 1: Create Terraform Cloud Account

1. Go to [Terraform Cloud](https://app.terraform.io)
2. Sign up for a free account
3. Create an organization or use existing

#### Step 2: Create Workspace

1. Click **New Workspace**
2. Select **CLI-driven workflow**
3. Name it `aws-cost-optimizer`
4. Click **Create workspace**

#### Step 3: Configure AWS Credentials

Navigate to your workspace **Settings > Variables**

##### Add Environment Variables

Click **+ Add variable** for each:

| Key | Value | Category | Sensitive |
|-----|-------|----------|-----------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key | Environment variable | ✅ Yes |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Key | Environment variable | ✅ Yes |
| `AWS_REGION` | `us-east-1` (or your region) | Environment variable | ❌ No |

**Detailed Steps:**

1. Go to your workspace > **Variables** tab
2. Under **Environment Variables**, click **+ Add variable**
3. Enter the key: `AWS_ACCESS_KEY_ID`
4. Enter your AWS Access Key ID as the value
5. Check the **Sensitive** checkbox (IMPORTANT!)
6. Click **Save variable**
7. Repeat for `AWS_SECRET_ACCESS_KEY` and `AWS_REGION`

##### Add Terraform Variables (Optional)

You can override default values by adding Terraform variables:

| Key | Value | Category | Sensitive |
|-----|-------|----------|-----------|
| `project_name` | `aws-cost-optimizer` | Terraform variable | ❌ No |
| `target_environments` | `["dev", "homolog", "staging"]` | Terraform variable | ❌ No |
| `stop_schedule` | `cron(0 22 ? * MON-FRI *)` | Terraform variable | ❌ No |
| `start_schedule` | `cron(0 11 ? * MON-FRI *)` | Terraform variable | ❌ No |
| `enable_scheduler` | `true` | Terraform variable | ❌ No |

**Note:** For list variables like `target_environments`, use JSON format: `["dev", "homolog", "staging"]`

#### Step 4: Configure Backend

Update `terraform/backend.tf` with your organization name:

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

#### Step 5: Initialize and Apply

```bash
# Navigate to terraform directory
cd terraform

# Login to Terraform Cloud
terraform login

# Initialize (connects to Terraform Cloud)
terraform init

# Plan changes
terraform plan

# Apply infrastructure
terraform apply
```

### GitHub Actions Setup

GitHub Actions is used to deploy Lambda code changes separately from infrastructure.

#### Step 1: Configure Repository Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings > Secrets and variables > Actions**
3. Click **New repository secret**
4. Add the following secrets:

| Secret Name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Access Key |

#### Step 2: Verify Workflow

The workflow file `.github/workflows/lambda-deploy.yml` will:

1. Trigger on push to `main` branch when `lambda/` files change
2. Package Lambda functions as ZIP files
3. Deploy to AWS Lambda using `aws lambda update-function-code`

#### Step 3: Test Deployment

1. Make a change to `lambda/stop/handler.py` or `lambda/start/handler.py`
2. Commit and push to `main` branch
3. Check **Actions** tab for workflow execution

## Usage

### Deploy Infrastructure (Terraform Cloud)

Infrastructure changes are deployed through Terraform Cloud:

1. Make changes to files in `terraform/` directory
2. Commit and push to repository
3. Terraform Cloud automatically triggers a run (if VCS connected)
   - Or run `terraform apply` locally
4. Review the plan in Terraform Cloud UI
5. Confirm and apply

### Deploy Lambda Code (GitHub Actions)

Lambda code changes are deployed through GitHub Actions:

1. Make changes to files in `lambda/` directory
2. Commit and push to `main` branch
3. GitHub Actions automatically deploys the Lambda

### Local Testing

You can test Lambda functions locally:

```bash
# Install boto3
pip install boto3

# Test stop function
cd lambda/stop
python -c "
import handler
event = {'tag_key': 'Environment', 'tag_values': ['dev']}
result = handler.lambda_handler(event, None)
print(result)
"
```

## Tag Your Resources

For resources to be managed by this solution, add the following tag:

```
Key: Environment
Value: dev | homolog | staging
```

### Tagging Examples

#### EC2 Instance

**AWS Console:**
1. Go to EC2 > Instances
2. Select instance
3. Tags tab > Manage tags
4. Add tag: `Environment` = `dev`

**Terraform:**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-dev"
    Environment = "dev"  # This tag enables cost optimization
  }
}
```

**AWS CLI:**
```bash
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=Environment,Value=dev
```

#### RDS Instance

**Terraform:**
```hcl
resource "aws_db_instance" "database" {
  identifier     = "mydb-dev"
  engine         = "postgres"
  instance_class = "db.t3.micro"
  # ... other config

  tags = {
    Name        = "mydb-dev"
    Environment = "dev"
  }
}
```

#### Aurora Cluster

**Terraform:**
```hcl
resource "aws_rds_cluster" "aurora" {
  cluster_identifier = "aurora-dev"
  engine             = "aurora-postgresql"
  # ... other config

  tags = {
    Name        = "aurora-dev"
    Environment = "homolog"
  }
}
```

#### ECS Service

**Terraform:**
```hcl
resource "aws_ecs_service" "api" {
  name            = "api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2

  tags = {
    Name        = "api-service"
    Environment = "staging"
  }
}
```

#### DocumentDB Cluster

**Terraform:**
```hcl
resource "aws_docdb_cluster" "docdb" {
  cluster_identifier = "docdb-dev"
  engine             = "docdb"
  # ... other config

  tags = {
    Name        = "docdb-dev"
    Environment = "dev"
  }
}
```

## Schedule Configuration

### Default Schedules

| Action | Brazil Time (BRT) | UTC | Cron Expression |
|--------|-------------------|-----|-----------------|
| Stop | 19:00 (7 PM) | 22:00 | `cron(0 22 ? * MON-FRI *)` |
| Start | 08:00 (8 AM) | 11:00 | `cron(0 11 ? * MON-FRI *)` |

### Understanding Cron Expressions

AWS EventBridge uses the following cron format:

```
cron(minutes hours day-of-month month day-of-week year)
```

| Field | Values | Wildcards |
|-------|--------|-----------|
| Minutes | 0-59 | , - * / |
| Hours | 0-23 | , - * / |
| Day of month | 1-31 | , - * ? / L W |
| Month | 1-12 or JAN-DEC | , - * / |
| Day of week | 1-7 or SUN-SAT | , - * ? L # |
| Year | 1970-2199 | , - * / |

### Custom Schedule Examples

**Stop at 6 PM BRT (21:00 UTC), Monday to Friday:**
```hcl
stop_schedule = "cron(0 21 ? * MON-FRI *)"
```

**Start at 7 AM BRT (10:00 UTC), Monday to Friday:**
```hcl
start_schedule = "cron(0 10 ? * MON-FRI *)"
```

**Stop at 8 PM BRT (23:00 UTC), every day:**
```hcl
stop_schedule = "cron(0 23 ? * * *)"
```

**Start at 9 AM BRT (12:00 UTC), only weekdays:**
```hcl
start_schedule = "cron(0 12 ? * MON-FRI *)"
```

### Configuring in Terraform Cloud

1. Go to your workspace > **Variables**
2. Add or update Terraform variable:
   - Key: `stop_schedule` or `start_schedule`
   - Value: Your cron expression
   - Category: Terraform variable
3. Run `terraform apply`

## Cost Savings Estimate

### Calculation Method

Savings are calculated based on:
- 22 business days per month
- 13 hours off-time per day (19:00 to 08:00)
- Resources only pay when running

### Estimated Savings by Resource Type

| Resource Type | Instance Size | Hourly Cost | Daily Savings | Monthly Savings |
|---------------|---------------|-------------|---------------|-----------------|
| EC2 | t3.micro | $0.0104 | $0.14 | $2.97 |
| EC2 | t3.small | $0.0208 | $0.27 | $5.94 |
| EC2 | t3.medium | $0.0416 | $0.54 | $11.88 |
| EC2 | t3.large | $0.0832 | $1.08 | $23.76 |
| RDS | db.t3.micro | $0.017 | $0.22 | $4.84 |
| RDS | db.t3.small | $0.034 | $0.44 | $9.68 |
| RDS | db.t3.medium | $0.068 | $0.88 | $19.36 |
| ECS Fargate | 0.25 vCPU | $0.01012 | $0.13 | $2.88 |
| ECS Fargate | 0.5 vCPU | $0.02024 | $0.26 | $5.77 |
| ECS Fargate | 1 vCPU | $0.04048 | $0.53 | $11.53 |

*Prices based on us-east-1 region. Actual costs may vary.*

### Example Scenario

A typical development environment with:
- 5x t3.medium EC2 instances
- 2x db.t3.medium RDS instances
- 3x ECS services (1 vCPU each)

**Monthly Savings:**
- EC2: 5 × $11.88 = $59.40
- RDS: 2 × $19.36 = $38.72
- ECS: 3 × $11.53 = $34.59
- **Total: $132.71/month**

**Annual Savings: ~$1,592**

## Manual Invocation

### Using AWS CLI

**Stop specific environment:**
```bash
aws lambda invoke \
  --function-name aws-cost-optimizer-stop \
  --payload '{"tag_key": "Environment", "tag_values": ["dev"]}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

**Start specific environment:**
```bash
aws lambda invoke \
  --function-name aws-cost-optimizer-start \
  --payload '{"tag_key": "Environment", "tag_values": ["dev"]}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

**Stop multiple environments:**
```bash
aws lambda invoke \
  --function-name aws-cost-optimizer-stop \
  --payload '{"tag_key": "Environment", "tag_values": ["dev", "homolog"]}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Using AWS Console

1. Go to AWS Lambda Console
2. Select `aws-cost-optimizer-stop` or `aws-cost-optimizer-start`
3. Click **Test** tab
4. Create test event with payload:
   ```json
   {
     "tag_key": "Environment",
     "tag_values": ["dev"]
   }
   ```
5. Click **Test**

## Monitoring

### CloudWatch Logs

Lambda execution logs are stored in CloudWatch Log Groups:

- `/aws/lambda/aws-cost-optimizer-stop`
- `/aws/lambda/aws-cost-optimizer-start`

**View logs via AWS CLI:**
```bash
# View recent stop Lambda logs
aws logs tail /aws/lambda/aws-cost-optimizer-stop --follow

# View recent start Lambda logs
aws logs tail /aws/lambda/aws-cost-optimizer-start --follow
```

### CloudWatch Metrics

Monitor these Lambda metrics:

| Metric | Description |
|--------|-------------|
| Invocations | Number of times Lambda was triggered |
| Errors | Number of failed executions |
| Duration | Execution time in milliseconds |
| Throttles | Number of throttled invocations |

### Setting Up Alarms

**Create alarm for Lambda errors:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "CostOptimizer-Stop-Errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=aws-cost-optimizer-stop \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:alerts
```

## Troubleshooting

### Resources Not Stopping

1. **Check tags are correctly applied:**
   ```bash
   # EC2
   aws ec2 describe-instances \
     --filters "Name=tag:Environment,Values=dev" \
     --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name}'

   # RDS
   aws rds describe-db-instances \
     --query 'DBInstances[].{ID:DBInstanceIdentifier,Status:DBInstanceStatus}'
   ```

2. **Check Lambda execution logs:**
   ```bash
   aws logs tail /aws/lambda/aws-cost-optimizer-stop --since 1h
   ```

3. **Verify scheduler is enabled:**
   ```bash
   aws scheduler list-schedules \
     --query 'Schedules[?contains(Name, `cost-optimizer`)]'
   ```

### Resources Not Starting

1. **Check resources are in stopped state:**
   ```bash
   aws ec2 describe-instances \
     --filters "Name=instance-state-name,Values=stopped" \
     --query 'Reservations[].Instances[].InstanceId'
   ```

2. **For ECS, check OriginalDesiredCount tag:**
   ```bash
   aws ecs list-tags-for-resource \
     --resource-arn arn:aws:ecs:us-east-1:123456789:service/cluster/service
   ```

### Permission Errors

1. **Check Lambda role has required permissions:**
   ```bash
   aws iam get-role-policy \
     --role-name aws-cost-optimizer-lambda-role \
     --policy-name aws-cost-optimizer-lambda-policy
   ```

2. **Test specific permission:**
   ```bash
   aws ec2 describe-instances --dry-run
   ```

### Scheduler Not Triggering

1. **Check schedule state:**
   ```bash
   aws scheduler get-schedule --name aws-cost-optimizer-stop-schedule
   ```

2. **Verify cron expression:**
   - Use [cron expression generator](https://crontab.guru/) to validate

## Security

### Best Practices Implemented

- **Least Privilege**: Lambda IAM role has only required permissions
- **No Hardcoded Credentials**: All credentials stored in Terraform Cloud/GitHub Secrets
- **Sensitive Variables**: AWS credentials marked as sensitive in Terraform Cloud
- **Log Retention**: CloudWatch logs retained for 14 days only
- **No Public Endpoints**: Lambda functions are not publicly accessible

### Recommendations

1. **Use IAM Roles for EC2** instead of access keys when possible
2. **Enable MFA** on AWS accounts
3. **Rotate credentials** regularly
4. **Use AWS Organizations** SCPs to restrict actions
5. **Enable CloudTrail** for audit logging

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Open Pull Request

## Author

**Anderson Sales** - DevOps Cloud Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/salesanderson)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/salles-anderson)
