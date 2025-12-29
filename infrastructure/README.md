# Infrastructure (Terraform) — Yandex Cloud

Модульная Terraform-конфигурация для проекта (**VPC → Managed Kubernetes → Storage → Monitoring**).

## Структура

- `modules/network` — VPC network/subnet + security groups
- `modules/kubernetes` — Managed Kubernetes cluster + node groups (CPU/GPU) + Calico (NetworkPolicy)
- `modules/storage` — Object Storage bucket + access keys (для Terraform remote state)
- `modules/monitoring` — минимальный cloud monitoring (лог-группа; как доп. слой к Prometheus в k8s)
- `bootstrap/backend` — bootstrap для создания bucket + ключей (remote state)
- `environments/{staging,production}` — окружения

---

## 1) Bootstrap: создаём bucket для remote state

Terraform backend **не может** создать bucket сам, поэтому сначала выполняем bootstrap.

```bash
cd infrastructure/bootstrap/backend
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

После `apply` сохраните значения:

```bash
terraform output bucket_name
terraform output -raw access_key_id
terraform output -raw secret_access_key
```

---

## 2) Развёртывание окружения (staging / production)

Пример для staging:

```bash
cd infrastructure/environments/staging
cp terraform.tfvars.example terraform.tfvars
```

### Настройка backend (remote state)

В `backend.tf` заданы endpoint/region/key, а **bucket и ключи** передаются при `terraform init`:

```bash
terraform init   -backend-config="bucket=<BUCKET_NAME>"   -backend-config="access_key=<ACCESS_KEY_ID>"   -backend-config="secret_key=<SECRET_ACCESS_KEY>"
```

Далее:

```bash
terraform apply
```

---

## GPU node group

По умолчанию используется:
- `gpu_platform_id = "gpu-standard-v2"`
- `gpu_count = 1`

Если в вашем аккаунте/зоне другой `platform_id`, переопределите в `terraform.tfvars`, например:

```hcl
gpu_platform_id = "gpu-standard-v3"
```

---

## Kubernetes NetworkPolicy (пример)

В кластере включён провайдер сетевых политик Calico (`network_policy_provider = "CALICO"`).
Примеры манифестов лежат в `infrastructure/k8s/`.

Применить:

```bash
kubectl apply -f infrastructure/k8s/networkpolicy-default-deny.yaml
kubectl apply -f infrastructure/k8s/networkpolicy-allow-dns.yaml
```
