output "vpc_id" {
  description = "ID of the VPC created for the stack."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs."
  value       = aws_subnet.public[*].id
}

output "s3_bucket_name" {
  description = "S3 bucket used for uploaded product images."
  value       = aws_s3_bucket.product_images.bucket
}

output "textract_table_name" {
  description = "DynamoDB table storing extracted text."
  value       = aws_dynamodb_table.textract_product_images.name
}

output "summary_table_name" {
  description = "DynamoDB table storing compliance summaries."
  value       = aws_dynamodb_table.product_compliance_summary.name
}

output "lambda_function_name" {
  description = "S3-triggered Textract Lambda function name."
  value       = aws_lambda_function.textract_processor.function_name
}

output "worker_private_api_urls" {
  description = "Private worker URLs used by the central dispatcher."
  value       = local.worker_private_url_map
}

output "worker_public_api_urls" {
  description = "Public worker URLs. These are only reachable if worker ingress is opened."
  value       = local.worker_public_url_map
}

output "central_server_public_ip" {
  description = "Elastic IP attached to the central dispatcher."
  value       = try(aws_eip.central[0].public_ip, null)
}

output "central_server_url" {
  description = "Public URL for the central dispatcher."
  value       = try(format("http://%s:%d", aws_eip.central[0].public_ip, var.central_server_port), null)
}

output "central_server_docs_url" {
  description = "Swagger docs URL for the central dispatcher."
  value       = try(format("http://%s:%d/docs", aws_eip.central[0].public_ip, var.central_server_port), null)
}
