# Drift мониторинг в Kubernetes (CronJob + сервис метрик)

Манифесты в этой папке — учебный пример:
- `CronJob` периодически пересчитывает Evidently отчёт и пишет summary в PVC.
- `Deployment` `credit-drift-api` отдаёт summary как Prometheus-метрики на `/metrics`.

## Применение
```bash
kubectl apply -f k8s/drift/10-drift-pvc.yaml
kubectl apply -f k8s/drift/20-drift-cronjob.yaml
kubectl apply -f k8s/drift/30-drift-api-deployment.yaml
kubectl apply -f k8s/drift/31-drift-api-service.yaml
```

Проверка:
```bash
kubectl -n credit-scoring port-forward svc/credit-drift-svc 8001:8001
curl http://127.0.0.1:8001/metrics
```
