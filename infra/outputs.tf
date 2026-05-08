output "vpc_id" {
  value = aws_vpc.main.id
}

output "rds_endpoint" {
  value     = aws_db_instance.main.address
  sensitive = true
}

output "documents_bucket" {
  value = aws_s3_bucket.documents.bucket
}

output "rds_credentials_secret_arn" {
  value = aws_secretsmanager_secret.rds_credentials.arn
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.api.name
}
