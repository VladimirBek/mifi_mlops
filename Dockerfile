# Backend image (FastAPI) with DVC inside build
# Multi-stage: builder -> dvc (dvc repro) -> runtime

# ---------- Build stage ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies into /root/.local so we can copy them into runtime image
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ---------- DVC stage ----------
FROM python:3.11-slim AS dvc

WORKDIR /app

# Reuse already installed deps
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends git \
  && rm -rf /var/lib/apt/lists/*

# Copy only what DVC needs for pipeline run
COPY dvc.yaml params.yaml pyproject.toml requirements.txt ./
COPY .dvc ./.dvc
COPY src ./src
COPY data/expectations ./data/expectations

# Create dirs expected by pipeline
RUN mkdir -p data/raw data/processed models


RUN dvc repro --no-commit

# ---------- Runtime stage ----------
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy only artifacts + app code (no DVC cache)
COPY --from=dvc /app/models ./models
COPY --from=dvc /app/data ./data
COPY --from=dvc /app/src ./src

EXPOSE 8000

CMD ["uvicorn", "src.api.app_onnx:app", "--host", "0.0.0.0", "--port", "8000"]
