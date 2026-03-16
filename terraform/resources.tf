resource "aws_s3_bucket" "upload" {
  bucket = var.upload_bucket
  force_destroy = true
}

resource "aws_s3_bucket" "migrated" {
  bucket = var.migration_results
  force_destroy = true
}