provider "aws" {
  region = "ap-southeast-2" # Change to your desired AWS region
}

resource "aws_instance" "web" {
  ami           = "ami-093dc6859d9315726" # Example: Amazon Linux 2 ARM64 in ap-southeast-2 (Sydney). Update as needed!
  instance_type = "t4g.medium"

  tags = {
    Name = "DemoEC2"
  }
}
