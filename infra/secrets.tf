// API key secrets created up-front so the API can read them at boot.
// Values are written outside Terraform (e.g. via the AWS console or CI).

resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name        = "noticedesk/${var.environment}/anthropic"
  description = "Anthropic API key (primary LLM)."
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "noticedesk/${var.environment}/openai"
  description = "OpenAI API key (secondary LLM)."
}

resource "aws_secretsmanager_secret" "sentry_dsn" {
  name        = "noticedesk/${var.environment}/sentry"
  description = "Sentry DSN."
}
