# Service accounts for cluster and nodes
resource "yandex_iam_service_account" "cluster" {
  folder_id = var.folder_id
  name      = "sa-k8s-cluster-${var.environment}"
}

resource "yandex_iam_service_account" "nodes" {
  folder_id = var.folder_id
  name      = "sa-k8s-nodes-${var.environment}"
}

# Minimal roles (student-level)
resource "yandex_resourcemanager_folder_iam_member" "cluster_admin" {
  folder_id = var.folder_id
  role      = "k8s.clusters.agent"
  member    = "serviceAccount:${yandex_iam_service_account.cluster.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "cluster_vpc" {
  folder_id = var.folder_id
  role      = "vpc.publicAdmin"
  member    = "serviceAccount:${yandex_iam_service_account.cluster.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "nodes_agent" {
  folder_id = var.folder_id
  role      = "k8s.tunnelClusters.agent"
  member    = "serviceAccount:${yandex_iam_service_account.nodes.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "nodes_pull_images" {
  folder_id = var.folder_id
  role      = "container-registry.images.puller"
  member    = "serviceAccount:${yandex_iam_service_account.nodes.id}"
}

# KMS key for k8s secrets encryption
resource "yandex_kms_symmetric_key" "kms_key" {
  name              = "kms-k8s-${var.environment}"
  folder_id         = var.folder_id
  default_algorithm = "AES_256"
  rotation_period   = "8760h" # 1 year
}

# Managed Kubernetes cluster
resource "yandex_kubernetes_cluster" "credit_scoring" {
  name       = "credit-scoring-${var.environment}"
  folder_id  = var.folder_id
  network_id = var.network_id

  master {
    version   = var.k8s_version
    public_ip = true

    master_location {
      zone      = var.zone
      subnet_id = var.subnet_id
    }
  }

  # Enable network policies (Calico)
  network_policy_provider = "CALICO"

  service_account_id      = yandex_iam_service_account.cluster.id
  node_service_account_id = yandex_iam_service_account.nodes.id

  kms_provider {
    key_id = yandex_kms_symmetric_key.kms_key.id
  }
}

# CPU node group
resource "yandex_kubernetes_node_group" "cpu_nodes" {
  cluster_id = yandex_kubernetes_cluster.credit_scoring.id
  name       = "cpu-nodes-${var.environment}"

  instance_template {
    platform_id = "standard-v2"

    resources {
      memory = var.node_memory
      cores  = var.node_cores
    }

    boot_disk {
      type = "network-ssd"
      size = var.disk_size
    }

    scheduling_policy {
      preemptible = var.environment != "production"
    }

    network_interface {
      subnet_ids         = [var.subnet_id]
      nat                = true
      security_group_ids = [var.nodes_security_group_id]
    }
  }

  scale_policy {
    auto_scale {
      min     = var.scale_min
      max     = var.scale_max
      initial = var.scale_initial
    }
  }
}

# GPU node group (optional)
# NOTE: platform_id / availability depends on region/account; override gpu_platform_id if needed.
resource "yandex_kubernetes_node_group" "gpu_nodes" {
  count      = var.enable_gpu_nodes ? 1 : 0
  cluster_id = yandex_kubernetes_cluster.credit_scoring.id
  name       = "gpu-nodes-${var.environment}"

  instance_template {
    platform_id = var.gpu_platform_id

    resources {
      memory = var.gpu_node_memory
      cores  = var.gpu_node_cores
      gpus   = var.gpu_count
    }

    gpu_settings {
      gpu_environment = var.gpu_environment
    }

    boot_disk {
      type = "network-ssd"
      size = var.gpu_disk_size
    }

    scheduling_policy {
      preemptible = var.environment != "production"
    }

    network_interface {
      subnet_ids         = [var.subnet_id]
      nat                = true
      security_group_ids = [var.nodes_security_group_id]
    }

    labels = {
      "node-type" = "gpu"
    }
  }

  scale_policy {
    auto_scale {
      min     = var.gpu_scale_min
      max     = var.gpu_scale_max
      initial = var.gpu_scale_initial
    }
  }
}
