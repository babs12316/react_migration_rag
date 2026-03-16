# prod
#terraform apply -var-file="terraform.prod.tfvars"
region              = "us-east-1"
upload_bucket       = "migration-uploads"
force_destroy = false
is_local = false
