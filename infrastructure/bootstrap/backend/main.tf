module "storage" {
  source    = "../../modules/storage"
  folder_id = var.folder_id
  name      = var.state_bucket_name
}
