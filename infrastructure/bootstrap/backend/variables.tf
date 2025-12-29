variable "yc_token"  { type = string, sensitive = true }
variable "cloud_id"  { type = string }
variable "folder_id" { type = string }
variable "zone"      { type = string, default = "ru-central1-a" }

variable "state_bucket_name" {
  type = string
  description = "Globally unique bucket name, e.g. tfstate-<yourname>-<random>"
}
