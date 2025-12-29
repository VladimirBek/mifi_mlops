from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import onnxruntime as ort
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
import time

MODEL_PATH = Path("models/nn_model.onnx")
CAT_COLS = {"SEX", "EDUCATION", "MARRIAGE", "AGE_BIN"}

app = FastAPI(title="Credit Scoring PD API (ONNX)", version="0.1")

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "path", "status"),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency, seconds",
    labelnames=("method", "path"),
)

@app.middleware("http")
async def _metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    HTTP_REQUEST_DURATION_SECONDS.labels(request.method, request.url.path).observe(time.time() - start)
    HTTP_REQUESTS_TOTAL.labels(request.method, request.url.path, str(response.status_code)).inc()
    return response

@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class CreditFeatures(BaseModel):
    LIMIT_BAL: float
    SEX: int
    EDUCATION: int
    MARRIAGE: int
    AGE: int

    PAY_0: int
    PAY_2: int
    PAY_3: int
    PAY_4: int
    PAY_5: int
    PAY_6: int

    BILL_AMT1: float
    BILL_AMT2: float
    BILL_AMT3: float
    BILL_AMT4: float
    BILL_AMT5: float
    BILL_AMT6: float

    PAY_AMT1: float
    PAY_AMT2: float
    PAY_AMT3: float
    PAY_AMT4: float
    PAY_AMT5: float
    PAY_AMT6: float

    BILL_AMT_SUM: Optional[float] = None
    PAY_AMT_SUM: Optional[float] = None
    PAY_RATIO: Optional[float] = None
    AGE_BIN: Optional[str] = None


def compute_engineered(df: pd.DataFrame) -> pd.DataFrame:
    bill_cols = [c for c in df.columns if c.startswith("BILL_AMT")]
    pay_cols = [c for c in df.columns if c.startswith("PAY_AMT")]

    df = df.copy()
    df["BILL_AMT_SUM"] = df[bill_cols].sum(axis=1)
    df["PAY_AMT_SUM"] = df[pay_cols].sum(axis=1)

    denom = df["BILL_AMT_SUM"].replace(0, 1.0)
    df["PAY_RATIO"] = (df["PAY_AMT_SUM"] / denom).clip(lower=0.0)

    df["AGE_BIN"] = pd.cut(
        df["AGE"].astype(int),
        bins=[0, 25, 35, 45, 55, 65, 200],
        labels=["<25", "25-34", "35-44", "45-54", "55-64", "65+"],
        right=False,
    ).astype(str)
    return df


def to_onnx_inputs(df: pd.DataFrame) -> dict:
    inputs = {}
    for c in df.columns:
        col = df[[c]]
        if c in CAT_COLS:
            inputs[c] = col.astype(str).values
        else:
            inputs[c] = col.astype(np.float32).values
    return inputs


def extract_proba(outputs) -> float:
    probs = outputs[-1]

    # ZipMap: list[dict]
    if isinstance(probs, list) and len(probs) > 0 and isinstance(probs[0], dict):
        d = probs[0]
        if 1 in d:
            return float(d[1])
        if "1" in d:
            return float(d["1"])
        return float(max(d.values()))

    probs = np.asarray(probs)
    if probs.ndim == 2 and probs.shape[1] == 2:
        return float(probs[0, 1])
    return float(probs.reshape(-1)[0])


def load_session() -> ort.InferenceSession:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing {MODEL_PATH}. Train/convert ONNX first.")

    # ORT сам выберет доступный провайдер, но на GPU-хосте важно иметь CUDAExecutionProvider
    providers = ort.get_available_providers()
    return ort.InferenceSession(MODEL_PATH.as_posix(), providers=providers)


SESSION = None


@app.on_event("startup")
def startup():
    global SESSION
    SESSION = load_session()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "model_path": str(MODEL_PATH),
        "available_providers": ort.get_available_providers(),
    }


@app.post("/predict")
def predict(payload: CreditFeatures) -> Dict[str, Any]:
    global SESSION
    if SESSION is None:
        raise HTTPException(status_code=500, detail="ONNX session not initialized")

    df = pd.DataFrame([payload.model_dump()])
    df = compute_engineered(df)

    inputs = to_onnx_inputs(df)
    out = SESSION.run(None, inputs)
    proba = extract_proba(out)
    pred = int(proba >= 0.5)
    return {"pred_class": pred, "pred_proba": proba}
