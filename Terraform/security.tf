resource "aws_security_group" "central" {
  count = var.deploy_central_server ? 1 : 0

  name        = "${local.name_prefix}-central-sg"
  description = "Security group for the central dispatcher"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-central-sg"
  }
}

resource "aws_vpc_security_group_egress_rule" "central_all" {
  count = var.deploy_central_server ? 1 : 0

  security_group_id = aws_security_group.central[0].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "central_api" {
  for_each = var.deploy_central_server ? toset(var.central_api_ingress_cidrs) : toset([])

  security_group_id = aws_security_group.central[0].id
  cidr_ipv4         = each.value
  from_port         = var.central_server_port
  ip_protocol       = "tcp"
  to_port           = var.central_server_port
}

resource "aws_vpc_security_group_ingress_rule" "central_ssh" {
  for_each = var.deploy_central_server ? toset(var.ssh_ingress_cidrs) : toset([])

  security_group_id = aws_security_group.central[0].id
  cidr_ipv4         = each.value
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

resource "aws_security_group" "worker" {
  name        = "${local.name_prefix}-worker-sg"
  description = "Security group for scraping worker nodes"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-worker-sg"
  }
}

resource "aws_vpc_security_group_egress_rule" "worker_all" {
  security_group_id = aws_security_group.worker.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "worker_from_central" {
  count = var.deploy_central_server ? 1 : 0

  security_group_id            = aws_security_group.worker.id
  referenced_security_group_id = aws_security_group.central[0].id
  from_port                    = var.worker_host_port
  ip_protocol                  = "tcp"
  to_port                      = var.worker_host_port
}

resource "aws_vpc_security_group_ingress_rule" "worker_public_api" {
  for_each = toset(var.worker_api_ingress_cidrs)

  security_group_id = aws_security_group.worker.id
  cidr_ipv4         = each.value
  from_port         = var.worker_host_port
  ip_protocol       = "tcp"
  to_port           = var.worker_host_port
}

resource "aws_vpc_security_group_ingress_rule" "worker_ssh" {
  for_each = toset(var.ssh_ingress_cidrs)

  security_group_id = aws_security_group.worker.id
  cidr_ipv4         = each.value
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}
