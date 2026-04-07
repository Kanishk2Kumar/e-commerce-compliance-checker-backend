# Terraform Stack

This folder codifies the infrastructure implied by the repo and your deployment notes:

- An S3 bucket for uploaded product images
- DynamoDB tables for extracted text and compliance summaries
- A Lambda function built from `../lambdaFunc_Backup.py` and triggered by S3 uploads
- A public EC2 worker fleet that runs the Docker image from your earlier deployment pattern
- An optional public central dispatcher EC2 instance that is rendered from the repo's `worker-node/central_server.py` logic and automatically points to the worker private IPs

## What changed from the old manual deployment

The PDF and `.env` showed static AWS access keys being placed inside worker instances. This Terraform setup intentionally uses IAM roles instead, so the workers and Lambda can access AWS services without baking credentials into EC2 user data.

## Files

- `networking.tf`: VPC, subnets, internet gateway, routing
- `security.tf`: Security groups and ingress/egress rules
- `storage.tf`: S3 bucket and DynamoDB tables
- `iam.tf`: IAM roles, instance profiles, and policies
- `lambda.tf`: Lambda packaging, permissions, and S3 notifications
- `compute.tf`: Worker EC2 instances and the optional central dispatcher
- `templates/`: EC2 bootstrapping and central server app templates

## Usage

```bash
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

Copy `terraform.tfvars.example` to `terraform.tfvars` and adjust values first if you want custom names, a key pair, or different ingress rules.

## Important assumptions

- The worker Docker image remains `kanishk2kumar/sih-worker:v2`.
- The Lambda code still expects the current table names unless you also update the Python source.
- Worker-to-central traffic is private inside the VPC by default.
- Direct public access to worker APIs is closed unless you populate `worker_api_ingress_cidrs`.
