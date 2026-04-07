data "archive_file" "lambda_package" {
  type        = "zip"
  source_file = "${path.module}/../lambdaFunc_Backup.py"
  output_path = "${path.module}/lambdaFunc_Backup.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.lambda_log_retention_days
}

resource "aws_lambda_function" "textract_processor" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda.arn
  filename      = data.archive_file.lambda_package.output_path
  handler       = "lambdaFunc_Backup.lambda_handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  depends_on = [
    aws_cloudwatch_log_group.lambda
  ]

  tags = {
    Name = var.lambda_function_name
  }
}

resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.textract_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.product_images.arn
}

resource "aws_s3_bucket_notification" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.textract_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "product-images/"
    filter_suffix       = ".jpg"
  }

  depends_on = [
    aws_lambda_permission.allow_s3_invoke
  ]
}
