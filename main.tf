provider "aws" {
  region = "ap-southeast-2"
}

resource "aws_s3_bucket" "my_bucket" {
  bucket = "statefile"   # Bucket name must be globally unique (change if "statefile" is taken)
  acl    = "private"
  tags = {
    Name        = "MyBucket"
    Environment = "Dev"
  }
}