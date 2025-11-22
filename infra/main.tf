terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.6.0"
}

provider "aws" {
  region = var.aws_region
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default_public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security groups for MySQL
resource "aws_security_group" "mysql_sg" {
  name        = "mysql-sg"
  description = "Internal MySQL cluster traffic"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "MySQL"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    security_groups = [aws_security_group.proxy_sg.id]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security group for proxy
resource "aws_security_group" "proxy_sg" {
  name        = "proxy-sg"
  description = "Allow gatekeeper to access proxy"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    security_groups = [aws_security_group.gatekeeper_sg.id]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security group for gatekeeper
resource "aws_security_group" "gatekeeper_sg" {
  name        = "gatekeeper-sg"
  description = "Public entry point"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Public HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # ubuntu publisher ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"] # ubuntu 22.04 (Jammy) images
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 instances
# MySQL instances
resource "aws_instance" "mysql_manager" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t2.micro"
  subnet_id                   = element(data.aws_subnets.default_public.ids, 0)
  vpc_security_group_ids      = [aws_security_group.mysql_sg.id]
  key_name                    = "LOG8415E"
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data/mysql_manager.sh.tpl", {
    mysql_password = var.mysql_password
  })

  tags = {
    Name = "mysql-manager"
    Role = "manager"
  }
}

resource "aws_instance" "mysql_worker" {
  count                       = 2
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t2.micro"
  subnet_id                   = element(data.aws_subnets.default_public.ids, count.index + 1)
  vpc_security_group_ids      = [aws_security_group.mysql_sg.id]
  key_name                    = "LOG8415E"
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data/mysql_worker.sh.tpl", {
    mysql_password = var.mysql_password
    manager_ip     = aws_instance.mysql_manager.public_ip
  })

  tags = {
    Name = "mysql-worker-${count.index + 1}"
    Role = "worker"
  }
}

# Proxy instance
resource "aws_instance" "proxy" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t2.large"
  subnet_id                   = element(data.aws_subnets.default_public.ids, 0)
  vpc_security_group_ids      = [aws_security_group.proxy_sg.id]
  key_name                    = "LOG8415E"
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data/proxy.sh.tpl", {
    manager_ip = aws_instance.mysql_manager.private_ip,
    worker_ips = join(",", aws_instance.mysql_worker[*].private_ip),
    mysql_password = var.mysql_password
  })

  tags = {
    Name = "proxy"
    Role = "proxy"
  }
}

# Gatekeeper instance
resource "aws_instance" "gatekeeper" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t2.large"
  subnet_id                   = element(data.aws_subnets.default_public.ids, 0)
  vpc_security_group_ids      = [aws_security_group.gatekeeper_sg.id]
  key_name                    = "LOG8415E"
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data/gatekeeper.sh.tpl", {
    proxy_ip = aws_instance.proxy.private_ip
  })

  tags = {
    Name = "gatekeeper"
    Role = "gatekeeper"
  }
}

