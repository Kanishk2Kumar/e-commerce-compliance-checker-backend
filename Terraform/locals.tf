data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

locals {
  name_prefix              = "${var.project_name}-${var.environment}"
  selected_azs             = slice(data.aws_availability_zones.available.names, 0, length(var.public_subnet_cidrs))
  effective_s3_bucket_name = coalesce(var.s3_bucket_name, "${local.name_prefix}-${data.aws_caller_identity.current.account_id}")

  common_tags = merge(
    {
      Environment = var.environment
      ManagedBy   = "Terraform"
      Project     = var.project_name
    },
    var.tags
  )

  worker_name_map = {
    for idx in range(var.worker_count) :
    format("worker%d", idx + 1) => idx
  }

  worker_private_url_map = {
    for name, idx in local.worker_name_map :
    name => format("http://%s:%d", aws_instance.worker[idx].private_ip, var.worker_host_port)
  }

  worker_public_url_map = {
    for name, idx in local.worker_name_map :
    name => format("http://%s:%d", aws_instance.worker[idx].public_ip, var.worker_host_port)
  }
}
