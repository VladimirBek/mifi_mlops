# Observability in Kubernetes (Prometheus + Grafana + Loki)

В рамках учебного проекта мониторинг развёртывается через **Helm**.
Рекомендуемая связка:

- **kube-prometheus-stack** (Prometheus Operator, Alertmanager, Grafana)
- **loki-stack** (Loki + Promtail) для логов

В репозитории лежат примеры `values.yaml` и пример правил алертов.

## 1) Установка kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack   -n monitoring --create-namespace   -f k8s/monitoring/values-prometheus.yaml
```

Проверка:

```bash
kubectl -n monitoring get pods
kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80
# Grafana: http://127.0.0.1:3000
```

## 2) Установка Loki + Promtail

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install loki grafana/loki-stack   -n monitoring   -f k8s/monitoring/values-loki.yaml
```

## 3) Интеграция приложения

Backend (FastAPI) экспортирует метрики на `/metrics` (Prometheus client).
ServiceMonitor для backend лежит в `k8s/monitoring/servicemonitor-backend.yaml`.

## 4) Алерты и runbook

- пример правил: `k8s/monitoring/alert-rules.yaml`
- runbook: `docs/runbook.md`
