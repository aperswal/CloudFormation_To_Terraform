# Variables
variable "BucketName" {
  description = "Name of the S3 bucket to create"
  type        = string
}

# Resources
resource "aws_s3_bucket" "MyS3Bucket" {
  bucket = "${BucketName}"
}
resource "aws_s3_bucket_acl" "MyS3Bucket_acl" {
  bucket = aws_s3_bucket.MyS3Bucket.id
  acl    = "Private"
}
resource "aws_s3_bucket_versioning" "MyS3Bucket_versioning" {
  bucket = aws_s3_bucket.MyS3Bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Outputs
output "BucketName" {
  description = "Name of the S3 bucket"
  value       = "${MyS3Bucket}"
}

output "BucketARN" {
  description = "ARN of the S3 bucket"
  value       = "${MyS3Bucket.Arn}"
}
