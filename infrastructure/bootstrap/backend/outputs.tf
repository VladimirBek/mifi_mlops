output "bucket_name" {
  value = module.storage.bucket_name
}

output "access_key_id" {
  value     = module.storage.access_key_id
  sensitive = true
}

output "secret_access_key" {
  value     = module.storage.secret_access_key
  sensitive = true
}
