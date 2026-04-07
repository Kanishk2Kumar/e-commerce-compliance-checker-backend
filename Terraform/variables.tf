variable "aws_region" {
  description = "AWS region where the stack will be deployed."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used in resource naming."
  type        = string
  default     = "sih-25057"
}

variable "environment" {
  description = "Environment label used in resource naming and tags."
  type        = string
  default     = "prod"
}

variable "tags" {
  description = "Additional tags to apply to all resources."
  type        = map(string)
  default     = {}
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.57.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets used by the central server and worker nodes."
  type        = list(string)
  default     = ["10.57.1.0/24", "10.57.2.0/24"]

  validation {
    condition     = length(var.public_subnet_cidrs) > 0
    error_message = "At least one public subnet CIDR must be provided."
  }
}

variable "key_name" {
  description = "Optional EC2 key pair name for SSH access."
  type        = string
  default     = null
  nullable    = true
}

variable "ssh_ingress_cidrs" {
  description = "CIDR blocks allowed to SSH into EC2 instances."
  type        = list(string)
  default     = []
}

variable "central_api_ingress_cidrs" {
  description = "CIDR blocks allowed to reach the central dispatcher API."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "worker_api_ingress_cidrs" {
  description = "Optional CIDR blocks allowed to reach worker APIs directly. Keep empty for private-only worker access."
  type        = list(string)
  default     = []
}

variable "deploy_central_server" {
  description = "Whether to create the central dispatcher EC2 instance."
  type        = bool
  default     = true
}

variable "central_instance_type" {
  description = "Instance type for the central dispatcher."
  type        = string
  default     = "t3.micro"
}

variable "central_root_volume_size" {
  description = "Root volume size in GiB for the central dispatcher."
  type        = number
  default     = 8
}

variable "central_server_port" {
  description = "Port exposed by the central dispatcher API."
  type        = number
  default     = 8000
}

variable "worker_count" {
  description = "Number of scraping worker EC2 instances to create."
  type        = number
  default     = 5
}

variable "worker_instance_type" {
  description = "Instance type for each worker node."
  type        = string
  default     = "t3.micro"
}

variable "worker_root_volume_size" {
  description = "Root volume size in GiB for each worker node."
  type        = number
  default     = 8
}

variable "worker_host_port" {
  description = "Port opened on the worker EC2 host."
  type        = number
  default     = 8000
}

variable "worker_container_port" {
  description = "Port exposed by the worker container."
  type        = number
  default     = 8000
}

variable "worker_docker_image" {
  description = "Docker image for the worker service."
  type        = string
  default     = "kanishk2kumar/sih-worker:v2"
}

variable "s3_bucket_name" {
  description = "Optional explicit S3 bucket name. Leave null to auto-generate a unique name."
  type        = string
  default     = null
  nullable    = true
}

variable "textract_table_name" {
  description = "DynamoDB table name for extracted image text."
  type        = string
  default     = "TextractProductImages"
}

variable "summary_table_name" {
  description = "DynamoDB table name for compliance summaries."
  type        = string
  default     = "ProductComplianceSummary"
}

variable "lambda_function_name" {
  description = "Name of the S3-triggered Lambda function."
  type        = string
  default     = "product-image-textract-processor"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 120
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB."
  type        = number
  default     = 512
}

variable "lambda_log_retention_days" {
  description = "CloudWatch log retention for the Lambda function."
  type        = number
  default     = 14
}
