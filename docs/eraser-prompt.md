# Eraser.io Prompt - AWS Cost Optimizer Architecture

Use this prompt in [Eraser.io](https://app.eraser.io) to generate the architecture diagram.

## Prompt

```
Create an AWS architecture diagram for a Cost Optimizer solution with the following components:

Title: AWS Cost Optimizer - Automated Resource Scheduling

Left side (Scheduling):
- EventBridge Scheduler icon with two schedules:
  - "Stop Schedule" (22:00 UTC / 19:00 BRT)
  - "Start Schedule" (11:00 UTC / 08:00 BRT)

Center (Processing):
- Two Lambda functions:
  - "Stop Lambda" (receives from Stop Schedule)
  - "Start Lambda" (receives from Start Schedule)
- Both Lambda functions connect to IAM Role
- CloudWatch Logs receiving logs from both Lambda functions

Right side (Target Resources):
- EC2 Instances group with Environment tag
- RDS Instances group with Environment tag
- Aurora Clusters group with Environment tag
- DocumentDB Clusters group with Environment tag
- ECS Services group with Environment tag

Flow arrows:
- Stop Schedule -> Stop Lambda -> All resource groups (with "Stop/Scale to 0" label)
- Start Schedule -> Start Lambda -> All resource groups (with "Start/Scale up" label)

Bottom section (CI/CD):
- GitHub icon connecting to:
  - Terraform Cloud (for infrastructure)
  - GitHub Actions (for Lambda deployment)
- Terraform Cloud -> AWS (IAM, Lambda, EventBridge)
- GitHub Actions -> Lambda functions

Color scheme:
- Use AWS official colors (orange for Lambda, blue for EC2, etc.)
- Green arrows for Start flow
- Red arrows for Stop flow

Add a legend showing:
- Target environments: dev, homolog, staging
- Schedule: Mon-Fri only
- Savings: Up to 65% cost reduction

Style: Clean, professional, AWS-native icons
```

## Alternative Simplified Prompt

```
AWS Cost Optimizer architecture:

EventBridge Scheduler (Stop 22:00 UTC, Start 11:00 UTC)
  |
  v
Lambda Functions (Stop/Start)
  |
  v
Tagged Resources (Environment: dev/homolog/staging):
- EC2 Instances
- RDS Instances
- Aurora Clusters
- DocumentDB Clusters
- ECS Services

CI/CD:
- Terraform Cloud -> Infrastructure
- GitHub Actions -> Lambda Code

Show flow with arrows, use AWS colors
```
