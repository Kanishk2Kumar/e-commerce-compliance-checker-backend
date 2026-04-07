data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      identifiers = ["ec2.amazonaws.com"]
      type        = "Service"
    }
  }
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "worker" {
  name               = "${local.name_prefix}-worker-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "worker_ssm" {
  role       = aws_iam_role.worker.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_iam_policy_document" "worker_access" {
  statement {
    actions = [
      "dynamodb:GetItem"
    ]

    resources = [
      aws_dynamodb_table.textract_product_images.arn
    ]
  }

  statement {
    actions = [
      "s3:PutObject"
    ]

    resources = [
      "${aws_s3_bucket.product_images.arn}/*"
    ]
  }
}

resource "aws_iam_role_policy" "worker_access" {
  name   = "${local.name_prefix}-worker-access"
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.worker_access.json
}

resource "aws_iam_instance_profile" "worker" {
  name = "${local.name_prefix}-worker-profile"
  role = aws_iam_role.worker.name
}

resource "aws_iam_role" "central" {
  count = var.deploy_central_server ? 1 : 0

  name               = "${local.name_prefix}-central-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "central_ssm" {
  count = var.deploy_central_server ? 1 : 0

  role       = aws_iam_role.central[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "central" {
  count = var.deploy_central_server ? 1 : 0

  name = "${local.name_prefix}-central-profile"
  role = aws_iam_role.central[0].name
}

resource "aws_iam_role" "lambda" {
  name               = "${local.name_prefix}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_access" {
  statement {
    actions = [
      "textract:DetectDocumentText"
    ]

    resources = ["*"]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:Query"
    ]

    resources = [
      aws_dynamodb_table.textract_product_images.arn,
      aws_dynamodb_table.product_compliance_summary.arn
    ]
  }

  statement {
    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.product_images.arn}/*"
    ]
  }

  statement {
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.product_images.arn
    ]
  }
}

resource "aws_iam_role_policy" "lambda_access" {
  name   = "${local.name_prefix}-lambda-access"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_access.json
}
