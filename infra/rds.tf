resource "random_password" "rds_master" {
  length  = 32
  special = true
}

resource "aws_db_subnet_group" "main" {
  name       = "noticedesk-${var.environment}"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "noticedesk-${var.environment}"
  }
}

resource "aws_security_group" "rds" {
  name        = "noticedesk-${var.environment}-rds"
  description = "Allow Postgres only from within the VPC."
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "main" {
  identifier             = "noticedesk-${var.environment}"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = var.rds_instance_class
  allocated_storage      = var.rds_allocated_storage_gb
  storage_encrypted      = true
  db_name                = var.rds_db_name
  username               = var.rds_master_username
  password               = random_password.rds_master.result
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  skip_final_snapshot    = var.environment != "prod"
  deletion_protection    = var.environment == "prod"
  backup_retention_period = var.environment == "prod" ? 14 : 1
  apply_immediately      = true
}

resource "aws_secretsmanager_secret" "rds_credentials" {
  name        = "noticedesk/${var.environment}/rds"
  description = "RDS master credentials for noticedesk-${var.environment}."
}

resource "aws_secretsmanager_secret_version" "rds_credentials" {
  secret_id = aws_secretsmanager_secret.rds_credentials.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.rds_master.result
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    dbname   = aws_db_instance.main.db_name
  })
}
