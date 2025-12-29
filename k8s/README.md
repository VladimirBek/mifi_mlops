# Kubernetes manifests (что это и как запускать)
## 1) Соберите Docker-образы

В корне репозитория:

```bash
docker build -t credit-backend:latest .
docker build -t credit-frontend:latest -f frontend/Dockerfile frontend
```

> Backend образ во время сборки запускает `dvc repro` — он скачает UCI dataset и обучит модель.

## 2) Установите nginx ingress controller (один раз на кластер)

Если Ingress Controller ещё не установлен:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.2/deploy/static/provider/cloud/deploy.yaml
```

## 3) Примените манифесты

```bash
kubectl apply -f 00-namespace.yaml
kubectl apply -f 10-backend-configmap.yaml
kubectl apply -f 11-backend-secret.yaml
kubectl apply -f 20-backend-deployment.yaml
kubectl apply -f 21-backend-service.yaml
kubectl apply -f 22-backend-ingress.yaml

kubectl apply -f 30-frontend-deployment.yaml
kubectl apply -f 31-frontend-service.yaml
kubectl apply -f 32-frontend-ingress.yaml
```

## 4) Проверка

```bash
kubectl -n credit-scoring get pods
kubectl -n credit-scoring get svc
kubectl -n credit-scoring get ingress
```

По умолчанию в Ingress прописан host `credit.local`. Для теста можно:

1) Узнать внешний IP ingress-nginx:
```bash
kubectl -n ingress-nginx get svc
```

2) Вписать его в `/etc/hosts`:
```
<EXTERNAL_IP> credit.local
```

После этого:
- `http://credit.local/` (frontend)
- `http://credit.local/api/health` (backend)
- `POST http://credit.local/api/predict`

> Если ты деплоишь в Yandex Managed Kubernetes, вместо локальных образов обычно нужно загрузить их в registry (YCR) и заменить `image:` в Deployment.
