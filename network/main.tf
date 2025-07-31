provider "aws" {
  region = "ap-southeast-2"
}

resource "aws_s3_bucket" "backend_bucket" {
  bucket = "resource1-30072029999"  # MUST be globally unique!
  acl    = "private"
  tags = {
    Name        = "SeparateStateBucket"
    Environment = "uat"
  }
}
