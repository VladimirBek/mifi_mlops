resource "yandex_vpc_network" "this" {
  name      = var.name
  folder_id = var.folder_id
}

resource "yandex_vpc_subnet" "this" {
  name           = "${var.name}-${var.zone}"
  folder_id      = var.folder_id
  zone           = var.zone
  network_id     = yandex_vpc_network.this.id
  v4_cidr_blocks = var.cidr
}

resource "yandex_vpc_security_group" "k8s_nodes" {
  name      = "${var.name}-k8s-nodes-sg"
  folder_id = var.folder_id
  network_id = yandex_vpc_network.this.id

  ingress {
    protocol       = "TCP"
    description    = "NodePort/HTTP demo"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 30000
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow SSH (optional)"
    v4_cidr_blocks = var.allowed_ssh_cidrs
    port           = 22
  }

  # Allow all inside SG (pod-to-pod/node-to-node)
  ingress {
    protocol          = "ANY"
    description       = "intra-cluster"
    security_group_id = yandex_vpc_security_group.k8s_nodes.id
  }

  egress {
    protocol       = "ANY"
    description    = "all egress"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}
