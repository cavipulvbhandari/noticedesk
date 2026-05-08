# Infrastructure

Terraform for AWS (Mumbai region — `ap-south-1`).

## Sprint 1 scope

The Sprint 1 infrastructure is a deployable skeleton:

- VPC with private + public subnets across two AZs.
- RDS PostgreSQL 16 (smallest viable instance for dev).
- S3 bucket with SSE-KMS encryption at rest, versioning, public access blocked.
- AWS Secrets Manager for API keys and DB credentials.
- CloudWatch log group `/noticedesk/api` with 30-day retention.

These are *stubs* — they describe the shape we want, parameterized for the
two early environments (`dev` and `staging`). Production hardening (multi-AZ
RDS, WAF, CloudFront, KMS CMKs per tenant, etc.) is Sprint N+ work and is
explicitly out of scope here.

## Layout

```
infra/
  versions.tf      # Terraform + provider versions
  providers.tf     # ap-south-1 provider config
  variables.tf     # environment / sizing knobs
  network.tf       # VPC, subnets, routing
  rds.tf           # PostgreSQL 16
  s3.tf            # encrypted bucket
  secrets.tf       # Secrets Manager
  logs.tf          # CloudWatch log group
  outputs.tf
  envs/
    dev.tfvars
    staging.tfvars
```

## Apply

```bash
cd infra
terraform init
terraform apply -var-file=envs/dev.tfvars
```

DPDP residency: every resource MUST stay in `ap-south-1`. The provider block
hard-codes the region; do not add aliases that point elsewhere without
explicit approval.
