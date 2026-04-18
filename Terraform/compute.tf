data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["137112412989"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "worker" {
  count = var.worker_count

  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.worker_instance_type
  subnet_id                   = aws_subnet.public[count.index % length(aws_subnet.public)].id
  vpc_security_group_ids      = [aws_security_group.worker.id]
  iam_instance_profile        = aws_iam_instance_profile.worker.name
  associate_public_ip_address = true
  key_name                    = var.key_name
  user_data_replace_on_change = true

  user_data = templatefile("${path.module}/templates/worker_user_data.sh.tftpl", {
    aws_region     = var.aws_region
    bucket_name    = aws_s3_bucket.product_images.bucket
    container_port = var.worker_container_port
    docker_image   = var.worker_docker_image
    dynamodb_table = aws_dynamodb_table.textract_product_images.name
    host_port      = var.worker_host_port
  })

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_size           = var.worker_root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = "${local.name_prefix}-worker-${count.index + 1}"
    Role = "worker"
  }
}

resource "aws_instance" "central" {
  count = var.deploy_central_server ? 1 : 0

  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.central_instance_type
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.central[0].id]
  iam_instance_profile        = aws_iam_instance_profile.central[0].name
  associate_public_ip_address = true
  key_name                    = var.key_name
  user_data_replace_on_change = true

  user_data = templatefile("${path.module}/templates/central_user_data.sh.tftpl", {
    central_port      = var.central_server_port
    central_server_py = templatefile("${path.module}/templates/central_server.py.tftpl", {
      worker_urls_json = jsonencode(local.central_worker_url_map)
    })
  })

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_size           = var.central_root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = "${local.name_prefix}-central"
    Role = "central"
  }
}

resource "aws_eip" "central" {
  count = var.deploy_central_server ? 1 : 0

  domain   = "vpc"
  instance = aws_instance.central[0].id

  tags = {
    Name = "${local.name_prefix}-central-eip"
  }
}
