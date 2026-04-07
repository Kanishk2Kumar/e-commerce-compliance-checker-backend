resource "aws_s3_bucket" "product_images" {
  bucket = local.effective_s3_bucket_name

  tags = {
    Name = local.effective_s3_bucket_name
  }
}

resource "aws_s3_bucket_versioning" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "textract_product_images" {
  name         = var.textract_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ProductID"
  range_key    = "ImageIndex"

  attribute {
    name = "ProductID"
    type = "S"
  }

  attribute {
    name = "ImageIndex"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = var.textract_table_name
  }
}

resource "aws_dynamodb_table" "product_compliance_summary" {
  name         = var.summary_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ProductID"

  attribute {
    name = "ProductID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = var.summary_table_name
  }
}
