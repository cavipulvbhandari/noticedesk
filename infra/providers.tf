// DPDP residency: ap-south-1 (Mumbai) only. Do not introduce regional
// aliases without explicit approval.

provider "aws" {
  region = "ap-south-1"

  default_tags {
    tags = {
      Project     = "noticedesk"
      Environment = var.environment
      ManagedBy   = "terraform"
      DataResidency = "in-mumbai"
    }
  }
}
