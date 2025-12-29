module "network" {
  source    = "../../modules/network"
  name      = "credit-scoring-production"
  folder_id = var.folder_id
  zone      = var.zone
  cidr      = var.vpc_cidr
  allowed_ssh_cidrs = var.allowed_ssh_cidrs
}

module "monitoring" {
  source      = "../../modules/monitoring"
  folder_id   = var.folder_id
  environment = "production"
}

module "kubernetes" {
  source      = "../../modules/kubernetes"
  environment = "production"
  folder_id   = var.folder_id
  zone        = var.zone

  network_id = module.network.network_id
  subnet_id  = module.network.subnet_id
  nodes_security_group_id = module.network.nodes_security_group_id

  k8s_version = var.k8s_version

  scale_min     = 2
  scale_max     = 10
  scale_initial = 2

  enable_gpu_nodes  = var.enable_gpu_nodes
  gpu_scale_min     = 0
  gpu_scale_max     = 2
  gpu_scale_initial = 0
}
