provider "aws" {
  region = "ap-southeast-2"
}

resource "aws_instance" "web" {
  ami           = "ami-093dc6859d9315726"   # Amazon Linux 2 ARM64 (Sydney)
  instance_type = "t4g.medium"

  # 1) CloudWatch detailed monitoring (billed per instance-hour)
  monitoring = true

  # 2) T-family unlimited bursting (extra charge if you exceed baseline credits)
  credit_specification {
    cpu_credits = "unlimited"
  }

  # 3) Public IPv4 address (AWS now charges per public IPv4 hour)
  associate_public_ip_address = true

  # 4) Root volume with higher size/IOPS/throughput (gp3 charges for size + extra IOPS/throughput)
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 50      # GiB
    iops                  = 6000    # > 3000 incurs extra gp3 IOPS cost
    throughput            = 500     # > 125 MB/s incurs extra gp3 throughput cost
    delete_on_termination = true
  }

  # 5) Extra attached data volume (more EBS cost)
  ebs_block_device {
    device_name           = "/dev/xvdb"
    volume_type           = "gp3"
    volume_size           = 100
    iops                  = 8000
    throughput            = 700
    delete_on_termination = true
  }

  tags = {
    Name = "DemoEC2"
  }
}
