# A/B тестирование и shadow deployment (Istio)

## Требования
- В кластере установлен Istio.
- Применены `DestinationRule` и два деплоймента `stable`/`canary` из `k8s/istio/`.

## A/B 50/50
```bash
kubectl apply -f k8s/ab/virtualservice-ab.yaml
```

## Shadow (100% трафика в stable + зеркалирование в canary)
```bash
kubectl apply -f k8s/ab/virtualservice-shadow.yaml
```
