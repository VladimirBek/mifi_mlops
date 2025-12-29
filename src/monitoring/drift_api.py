import json
import os
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest
from starlette.responses import Response

app = FastAPI(title="Credit Scoring Drift Monitor")

METRICS_PATH = Path(os.getenv("DRIFT_METRICS_PATH", "reports/evidently/drift_summary.json"))

g_drift_share = Gauge("credit_drift_share", "Доля дрейфующих признаков (Evidently)")
g_dataset_drift = Gauge("credit_dataset_drift", "Флаг dataset drift (Evidently, 0/1)")
g_perf_auc = Gauge("credit_model_roc_auc", "ROC-AUC на текущих данных (если есть target)")


def _load_metrics() -> Dict[str, float]:
    if not METRICS_PATH.exists():
        return {}
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


@app.get("/health")
def health():
    return {"status": "ok", "metrics_path": str(METRICS_PATH)}


@app.get("/metrics")
def metrics():
    m = _load_metrics()
    if "drift_share" in m:
        g_drift_share.set(float(m["drift_share"]))
    if "dataset_drift" in m:
        g_dataset_drift.set(float(m["dataset_drift"]))
    if "perf_roc_auc" in m:
        g_perf_auc.set(float(m["perf_roc_auc"]))
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
