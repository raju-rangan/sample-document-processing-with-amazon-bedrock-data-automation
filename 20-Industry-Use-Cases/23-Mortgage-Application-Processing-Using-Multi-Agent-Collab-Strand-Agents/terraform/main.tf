terraform {
 backend "local" {
   path = "terraform.tfstate"
 }
}

resource "aws_s3_bucket" "spacelift-test1-s3" {
   bucket = "spacelift-test1-s3"
}