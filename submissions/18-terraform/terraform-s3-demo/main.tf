# Random suffix so the bucket name is globally unique.
resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "demo" {
  bucket = "${var.bucket_prefix}${random_id.suffix.hex}"

  # Lets terraform destroy remove the bucket even if it still has
  # objects or old versions inside it.
  force_destroy = true
}

# Block every kind of public access.
resource "aws_s3_bucket_public_access_block" "demo" {
  bucket = aws_s3_bucket.demo.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Disable ACLs, the bucket owner owns every object.
resource "aws_s3_bucket_ownership_controls" "demo" {
  bucket = aws_s3_bucket.demo.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "demo" {
  bucket = aws_s3_bucket.demo.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server side encryption with S3 managed keys (SSE-S3).
resource "aws_s3_bucket_server_side_encryption_configuration" "demo" {
  bucket = aws_s3_bucket.demo.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# A small text file to show uploads work.
resource "aws_s3_object" "hello" {
  bucket       = aws_s3_bucket.demo.id
  key          = "demo/hello.txt"
  content      = "Hello from Terraform - Srinidhi Narendran 24BCS10037"
  content_type = "text/plain"

  # Upload only after the bucket settings are in place.
  depends_on = [
    aws_s3_bucket_versioning.demo,
    aws_s3_bucket_server_side_encryption_configuration.demo,
    aws_s3_bucket_ownership_controls.demo,
    aws_s3_bucket_public_access_block.demo,
  ]
}
