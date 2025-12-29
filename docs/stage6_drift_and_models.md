# Этап 6. Мониторинг дрифта и управление моделями (Evidently, A/B, shadow)

Этот проект — учебный. Поэтому мониторинг дрифта сделан максимально просто и воспроизводимо:
- «эталонные данные» = `data/processed/credit.csv` (после DVC prepare)
- «текущие данные» = `data/drift/current.csv` (генерируем скриптом-симулятором)
- для performance decay / concept drift добавляем предсказания из `models/model.joblib`

## 1) Сгенерировать текущие данные (псевдо-прод)

```bash
python scripts/drift/simulate_production_data.py --rows 2000 --inject-drift
```

Результат: `data/drift/current.csv`

## 2) Запустить Evidently отчёт

```bash
python -m src.monitoring.drift_job \
  --reference-path data/processed/credit.csv \
  --current-path data/drift/current.csv \
  --model-path models/model.joblib \
  --out-dir reports/evidently
```

Результат:
- HTML: `reports/evidently/drift_report.html`
- JSON: `reports/evidently/drift_report.json`
- Snapshot: `reports/evidently/drift_snapshot.json`
- Summary (для CI/Airflow/алертов): `reports/evidently/drift_summary.json`

## 3) A/B тестирование и shadow deployment (Istio)

В папке `k8s/istio/` уже есть 2 Deployment с разными `version` label: `stable` и `canary`.
Для A/B и shadow добавлены манифесты в `k8s/ab/`.

- A/B (50/50):
  ```bash
  kubectl apply -f k8s/ab/virtualservice-ab.yaml
  ```

- Shadow (основной трафик в stable, зеркалируем 100% запросов в canary):
  ```bash
  kubectl apply -f k8s/ab/virtualservice-shadow.yaml
  ```

Важно: shadow не влияет на ответы клиенту, но нагружает canary как «тень».
