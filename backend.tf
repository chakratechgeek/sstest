terraform {
  backend "s3" {
    bucket         = "statefile-chaks"  # <--- Use the new bucket name!
    key            = "terraform-state/uat/terraform.tfstate"  # Or another unique path for this deployment
    region         = "ap-southeast-2"
  }
}
