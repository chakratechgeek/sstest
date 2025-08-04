provider "aws" {
  region = "ap-southeast-2"
}

resource "aws_instance" "web" {
  ami           = "ami-093dc6859d9315726"  # Amazon Linux 2 ARM64 (Sydney)
  instance_type = "t4g.medium"             # unchanged to avoid arch replace

  # NEW: enable detailed monitoring
  monitoring = true

  # NEW: enforce IMDSv2 + keep endpoint enabled
  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  # NEW: burst credits config (valid for T-family incl. t4g)
  credit_specification {
    cpu_credits = "unlimited"
  }

  # NEW/CHANGED: root volume settings (will show in plan; may replace the instance)
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30   # was implicit default ~8; bump to 30 GiB
    iops                  = 3000 # gp3 baseline
    throughput            = 125  # gp3 baseline
    delete_on_termination = true
  }

  tags = {
    Name        = "DemoEC2"   # existing
    Environment = "dev"       # NEW
    Owner       = "platform"  # NEW
  }
}
