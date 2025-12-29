# Этап 1. Подготовка модели к промышленной эксплуатации

## 1) Обучение NN-модели и конвертация в ONNX

Обучение нейронной сети (sklearn `MLPClassifier`) и конвертация пайплайна в ONNX:

```bash
python -m src.models.train_nn_onnx   --data-path data/processed/credit.csv   --model-path models/nn_model.joblib   --onnx-path models/nn_model.onnx
```

Валидация корректности конвертации (сравнение вероятностей sklearn vs ONNX на выборке):

```bash
python scripts/validate_onnx.py   --data-path data/processed/credit.csv   --model-path models/nn_model.joblib   --onnx-path models/nn_model.onnx
```

## 2) Benchmark inference (CPU)

Сравнение времени инференса sklearn vs ONNX (CPU):

```bash
python scripts/benchmark_onnx.py   --data-path data/processed/credit.csv   --model-path models/nn_model.joblib   --onnx-path models/nn_model.onnx   --batch-size 512
```

## 3) Оптимизация (quantization)

Динамическая INT8 quantization:

```bash
python scripts/quantize_onnx.py   --onnx-path models/nn_model.onnx   --out-path models/nn_model_int8.onnx   --data-path data/processed/credit.csv
```

Benchmark INT8 (CPU):

```bash
python scripts/benchmark_onnx_int8.py   --data-path data/processed/credit.csv   --onnx-path models/nn_model.onnx   --onnx-int8-path models/nn_model_int8.onnx
```

Метрики качества (ROC-AUC) для ONNX и ONNX INT8:

```bash
python scripts/evaluate_onnx.py   --data-path data/processed/credit.csv   --onnx-path models/nn_model.onnx   --onnx-int8-path models/nn_model_int8.onnx
```

## 4) Нагрузочное тестирование

Locust сценарий: `scripts/locustfile.py`.

Пример запуска (предполагая, что backend доступен на `http://localhost:8000`):

```bash
pip install -r requirements-dev.txt
locust -f scripts/locustfile.py --host http://localhost:8000
```

Рекомендуется прогнать тест на двух конфигурациях (например CPU-only и GPU node group) и зафиксировать:
- RPS при целевой латентности (P95)
- ошибки (5xx)
- потребление CPU/RAM/GPU

Итог оформить в таблицу и приложить в отчёт по проекту.
