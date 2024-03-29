provider "aws" {
  region = var.aws_region
}

# TODO: Create VPC+subnet

resource "aws_security_group" "spark" {

  description = "Standalone Spark cluster"
  vpc_id      = var.aws_vpc_id

  # TODO: What should the cidr blocks be?
  ingress {
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # All ports open intra-group, for Spark random assignment.
  ingress {
    from_port = 0
    to_port   = 65535
    self      = true
    protocol  = "tcp"
  }

  egress {
    from_port = 0
    to_port   = 65535
    self      = true
    protocol  = "tcp"
  }

  # TODO: Don't open to the public web.
  # Spark UI
  ingress {
    from_port        = 8080
    to_port          = 8081
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # Spark UI "Application detail"
  ingress {
    from_port        = 4040
    to_port          = 4040
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

resource "aws_key_pair" "spark" {
  public_key = file(var.public_key_path)
}

# TODO: Provision the subnet directly?
resource "aws_network_interface" "master" {
  subnet_id       = var.aws_subnet_id
  security_groups = [aws_security_group.spark.id]
}

locals {
  user_data_vars = {
    ecr_server             = var.ecr_server
    ecr_repo               = var.ecr_repo
    aws_access_key_id      = var.aws_access_key_id
    aws_secret_access_key  = var.aws_secret_access_key
    huggingface_token      = var.huggingface_token
    driver_memory          = var.driver_memory
    executor_memory        = var.executor_memory
    gpu_workers            = var.gpu_workers
    max_driver_result_size = var.max_driver_result_size
    data_dir               = var.data_dir
    spark_packages         = var.spark_packages
    master_private_ip      = aws_network_interface.master.private_ip
  }
}

locals {
  master_user_data = templatefile(
    "cloud-config.yaml.tftpl",
    merge(local.user_data_vars, { master = true })
  )
  worker_user_data = templatefile(
    "cloud-config.yaml.tftpl",
    merge(local.user_data_vars, { master = false })
  )
}

resource "aws_instance" "master" {
  ami           = var.aws_ami
  instance_type = var.master_instance_type
  key_name      = aws_key_pair.spark.key_name
  user_data     = local.master_user_data

  network_interface {
    network_interface_id = aws_network_interface.master.id
    device_index         = 0
  }

  root_block_device {
    volume_size = var.root_vol_size
  }

  tags = {
    Name = "spark-master"
  }
}

# TODO: Name tags on the workers.

resource "aws_instance" "workers" {
  ami                         = var.aws_ami
  instance_type               = var.worker_instance_type
  subnet_id                   = var.aws_subnet_id
  vpc_security_group_ids      = [aws_security_group.spark.id]
  key_name                    = aws_key_pair.spark.key_name
  associate_public_ip_address = true
  count                       = var.on_demand_worker_count
  user_data                   = local.worker_user_data

  root_block_device {
    volume_size = var.root_vol_size
  }
}

resource "aws_spot_instance_request" "workers" {
  ami                         = var.aws_ami
  instance_type               = var.worker_instance_type
  subnet_id                   = var.aws_subnet_id
  vpc_security_group_ids      = [aws_security_group.spark.id]
  key_name                    = aws_key_pair.spark.key_name
  associate_public_ip_address = true
  wait_for_fulfillment        = true
  count                       = var.spot_worker_count
  user_data                   = local.worker_user_data

  root_block_device {
    volume_size = var.root_vol_size
  }
}

data "aws_instance" "master" {
  instance_id = aws_instance.master.id
}

# XXX: Pull from the "data" source, which will read the (possibly new) DNS
# after the plan is applied.
output "master_dns" {
  value = data.aws_instance.master.public_dns
}