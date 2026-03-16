output "S3_upload_bucket" {
  value = aws_s3_bucket.upload.bucket
}

output "S3_migrated_bucket" {
  value = aws_s3_bucket.migrated.bucket
}
