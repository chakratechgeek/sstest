terraform {
  backend "s3" {
    bucket         = "statefile_uniq"  # Your bucket name
    key            = "terraform-state/dev/terraform.tfstate"  # Any unique path/key per environment/module
    region         = "ap-southeast-2"
    encrypt        = true
    # Optional: Enable state locking (recommended in production)
    # dynamodb_table = "my-tf-lock-table"
  }
}
