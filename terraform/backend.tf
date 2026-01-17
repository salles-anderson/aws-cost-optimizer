terraform {
  cloud {
    organization = "your-organization"

    workspaces {
      name = "aws-cost-optimizer"
    }
  }
}
