variable "yc_token"  { type = string, sensitive = true }
variable "cloud_id"  { type = string }
variable "folder_id" { type = string }
variable "zone"      { type = string, default = "ru-central1-a" }

variable "vpc_cidr" {
  type    = list(string)
  default = ["10.20.0.0/24"]
}

variable "k8s_version" {
  type    = string
  default = "1.24"
}

variable "allowed_ssh_cidrs" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}

variable "enable_gpu_nodes" {
  type    = bool
  default = false
}
