# Этап 5. Мониторинг и observability

## Что реализовано

1) **Метрики приложения**
- FastAPI backend экспортирует Prometheus-метрики на `/metrics` (счётчик запросов и latency histogram).
- В Kubernetes можно подключить сбор через `ServiceMonitor` (`k8s/monitoring/servicemonitor-backend.yaml`).

2) **Дашборды**
- Используется `kube-prometheus-stack` (Grafana + Prometheus Operator).
- Для учебных целей достаточно встроенных дашбордов; далее можно добавить custom dashboard для `/predict`.

3) **Логи**
- Рекомендуемая связка Loki + Promtail (`k8s/monitoring/values-loki.yaml`).
- Для продакшена можно заменить на ELK/Opensearch, но для проекта Loki достаточно.

4) **Алертинг**
- Пример правил алертов: `k8s/monitoring/alert-rules.yaml`.
- Runbook: `docs/runbook.md`.

## Как развернуть

См. `k8s/monitoring/README.md` (Helm команды).
