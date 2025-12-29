output "bucket_name" {
  value = yandex_storage_bucket.tf_state.bucket
}

output "access_key_id" {
  value     = yandex_iam_access_key.sa_access_key.key_id
  sensitive = true
}

output "secret_access_key" {
  value     = yandex_iam_access_key.sa_access_key.secret
  sensitive = true
}
