FROM apache/airflow:2.10.4-python3.9

USER root
# минимальный набор системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

USER airflow

# Устанавливаем зависимости проекта + Evidently + DVC внутри Airflow образа
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Airflow extras для Postgres уже есть в базовом образе.
