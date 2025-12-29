# Промышленное развертывание кредитной скоринговой системы с полным MLOps-циклом

Учебный итоговый проект по дисциплине **«Автоматизация процессов доставки и развертывания моделей машинного обучения»**.

Цель: показать **сквозной MLOps-цикл** для кредитного скоринга (PD-модель) — от подготовки модели (ONNX + оптимизация)
до инфраструктуры (Terraform + Kubernetes), CI/CD, мониторинга, мониторинга дрифта и переобучения.

Датасет: **UCI “Default of Credit Card Clients”** (загрузка выполняется в пайплайне подготовки данных).

---

## Состав решения по этапам

- **Этап 1 (модель):** `src/models/train_nn_onnx.py`, `scripts/validate_onnx.py`, `scripts/quantize_onnx.py`,
  `scripts/benchmark_onnx*.py`, `docs/stage1_model_preparation.md`
- **Этап 2 (IaC):** `infrastructure/` (Terraform: VPC, K8s, Storage, Monitoring) + remote state в Object Storage
- **Этап 3 (Docker + K8s):** `Dockerfile`, `frontend/Dockerfile`, `k8s/` (rolling update, ConfigMap/Secret, Service/Ingress)
- **Этап 4 (CI/CD):** `.github/workflows/` (build → test → scan → deploy → monitor; canary/rollback)
- **Этап 5 (observability):** `k8s/monitoring/`, `docs/stage5_observability.md`, `docs/runbook.md`
- **Этап 6 (drift):** `src/monitoring/`, `k8s/drift/`, `docs/stage6_drift_and_models.md`
- **Этап 7 (retrain):** `airflow/dags/retrain_pd_model.py`, `docs/stage7_retrain_airflow.md`

---

## Стек

- Python, scikit-learn (Pipeline + NN `MLPClassifier`)
- ONNX Runtime (+ INT8 quantization)
- DVC (версии данных/моделей)
- MLflow (треккинг экспериментов — учебно)
- FastAPI (REST API `/predict`)
- Docker (multi-stage; DVC внутри build)
- Kubernetes (Deployment/Service/Ingress; Istio canary/A-B/shadow — учебно)
- Prometheus/Grafana/Loki (через Helm)
- Evidently AI (мониторинг дрифта)
- Airflow (пайплайн переобучения)

---

## Быстрый старт (локально)

### 1) Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Подготовка данных

```bash
python -m src.data.make_dataset --raw-path data/raw/default_credit.xls --processed-path data/processed/credit.csv
python -m src.data.validation --data-path data/processed/credit.csv --suite-path data/expectations/credit_suite.json
```

### 3) Обучение и экспорт ONNX

```bash
python -m src.models.train_nn_onnx --data-path data/processed/credit.csv
python scripts/validate_onnx.py
python scripts/quantize_onnx.py
```

### 4) Запуск API

```bash
uvicorn src.api.app_onnx:app --host 0.0.0.0 --port 8000
# Health:  http://127.0.0.1:8000/health
# Metrics: http://127.0.0.1:8000/metrics
```

---

## Docker

Backend:

```bash
docker build -t credit-backend:local .
docker run -p 8000:8000 credit-backend:local
```

Frontend:

```bash
docker build -t credit-frontend:local frontend
docker run -p 3000:80 credit-frontend:local
```

---

## Kubernetes

Манифесты приложения: `k8s/`  
Мониторинг: `k8s/monitoring/`  
Дрифт: `k8s/drift/`

Пример:

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-backend-configmap.yaml
kubectl apply -f k8s/11-backend-secret.yaml
kubectl apply -f k8s/20-backend-deployment.yaml
kubectl apply -f k8s/21-backend-service.yaml
kubectl apply -f k8s/22-backend-ingress.yaml
```

---

## Terraform (Yandex Cloud)

См. `infrastructure/README.md`.

---

## CI/CD

GitHub Actions в `.github/workflows/`:
- Build/Test + security scan (Trivy)
- Deploy в staging/production
- Canary release + rollback (учебные сценарии)

---

## Документация

- `docs/stage1_model_preparation.md`
- `docs/stage5_observability.md`
- `docs/stage6_drift_and_models.md`
- `docs/stage7_retrain_airflow.md`
- `docs/runbook.md`
