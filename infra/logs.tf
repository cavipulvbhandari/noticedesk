resource "aws_cloudwatch_log_group" "api" {
  name              = "/noticedesk/${var.environment}/api"
  retention_in_days = var.log_retention_days
}
