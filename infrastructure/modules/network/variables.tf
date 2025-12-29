variable "name" {
  type = string
}

variable "folder_id" {
  type = string
}

variable "zone" {
  type = string
}

variable "cidr" {
  type    = list(string)
  default = ["10.10.0.0/24"]
}

variable "allowed_ssh_cidrs" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}
