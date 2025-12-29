# Этап 7. Пайплайн переобучения и автоматизация (Airflow)

В учебном проекте цель — показать:
- регулярное переобучение по расписанию,
- триггер переобучения по дрифту (Evidently),
- базовую автоматическую проверку качества новой модели.

## Запуск Airflow локально (Docker Compose)

Из корня проекта:

```bash
docker compose -f airflow/docker-compose.yml up --build
```

Открыть UI:
- http://localhost:8081
- логин/пароль: `admin / admin`

## DAG: `retrain_pd_model`

Что делает:
1. Генерирует текущие данные `data/drift/current.csv` (с опцией искусственного дрейфа).
2. Считает Evidently отчёт и пишет summary в `reports/evidently/drift_summary.json`.
3. Если `drift_share >= DRIFT_THRESHOLD` **или** включён флаг `FORCE_RETRAIN=1` — запускает переобучение.
4. После обучения проверяет метрики (ROC-AUC) и, если всё ок, отмечает модель как “готовую”.

Настройки (через переменные окружения Airflow / Compose):
- `DRIFT_THRESHOLD` (по умолчанию 0.5)
- `AUC_MIN` (по умолчанию 0.65)
- `INJECT_DRIFT` (0/1; по умолчанию 1 — чтобы на демо был дрейф)
- `FORCE_RETRAIN` (0/1; по умолчанию 0)

### Триггер по данным

Если в `data/drift/` появляется файл `new_data.flag`, DAG воспримет это как сигнал «пришёл новый батч данных» и запустит переобучение.

```bash
touch data/drift/new_data.flag
```
