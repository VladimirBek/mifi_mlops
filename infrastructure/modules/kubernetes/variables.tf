variable "environment" { type = string }
variable "folder_id"   { type = string }
variable "zone"        { type = string }

variable "network_id" { type = string }
variable "subnet_id"  { type = string }

variable "nodes_security_group_id" { type = string }

variable "k8s_version" {
  type    = string
  default = "1.24"
}

# CPU node sizing
variable "node_cores"  { type = number, default = 4 }
variable "node_memory" { type = number, default = 8 }
variable "disk_size"   { type = number, default = 64 }

variable "scale_min"     { type = number, default = 2 }
variable "scale_max"     { type = number, default = 10 }
variable "scale_initial" { type = number, default = 2 }

# GPU node group (optional)
variable "enable_gpu_nodes" { type = bool, default = false }

# platform_id for GPU nodes can differ by region/account; override if needed
variable "gpu_platform_id" {
  type    = string
  default = "gpu-standard-v2"
}

variable "gpu_count" {
  type    = number
  default = 1
}

variable "gpu_environment" {
  type    = string
  default = "runc_drivers_cuda"
}

variable "gpu_node_cores"  { type = number, default = 8 }
variable "gpu_node_memory" { type = number, default = 32 }
variable "gpu_disk_size"   { type = number, default = 93 }

variable "gpu_scale_min"     { type = number, default = 0 }
variable "gpu_scale_max"     { type = number, default = 2 }
variable "gpu_scale_initial" { type = number, default = 0 }
