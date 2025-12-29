resource "yandex_iam_service_account" "tf_state" {
  folder_id = var.folder_id
  name      = "sa-tf-state"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_storage_admin" {
  folder_id = var.folder_id
  role      = "storage.admin"
  member    = "serviceAccount:${yandex_iam_service_account.tf_state.id}"
}

resource "yandex_iam_access_key" "sa_access_key" {
  service_account_id = yandex_iam_service_account.tf_state.id
  description        = "access key for terraform remote state"
}

resource "yandex_storage_bucket" "tf_state" {
  bucket        = var.name
  force_destroy = var.force_destroy

  anonymous_access_flags {
    read = false
    list = false
  }
}
