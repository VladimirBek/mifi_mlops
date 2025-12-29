import argparse
import time
from pathlib import Path

import joblib
import numpy as np
import onnxruntime as ort
import pandas as pd


CAT_COLS = {"SEX", "EDUCATION", "MARRIAGE", "AGE_BIN"}


def to_onnx_inputs(df: pd.DataFrame) -> dict:
    """
    skl2onnx для sklearn-пайплайнов часто ожидает отдельный input на каждый столбец.
    Категориальные -> string, числовые -> float32.
    """
    inputs = {}
    for c in df.columns:
        col = df[[c]]
        if c in CAT_COLS:
            inputs[c] = col.astype(str).values
        else:
            inputs[c] = col.astype(np.float32).values
    return inputs


def bench(fn, warmup: int, n_runs: int) -> float:
    # warmup
    for _ in range(warmup):
        fn()
    t0 = time.perf_counter()
    for _ in range(n_runs):
        fn()
    t1 = time.perf_counter()
    return (t1 - t0) / n_runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="data/processed/credit.csv")
    parser.add_argument("--sk-model", default="models/nn_model.joblib")
    parser.add_argument("--onnx-model", default="models/nn_model.onnx")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--warmup", type=int, default=30)
    parser.add_argument("--runs", type=int, default=200)
    args = parser.parse_args()

    data_path = Path(args.data_path)
    sk_path = Path(args.sk_model)
    onnx_path = Path(args.onnx_model)

    df = pd.read_csv(data_path)
    X = df.drop(columns=["default"])

    # Берем один и тот же батч
    batch = X.sample(n=min(args.batch_size, len(X)), random_state=1).reset_index(drop=True)

    # sklearn
    sk_model = joblib.load(sk_path)

    # onnxruntime
    sess = ort.InferenceSession(onnx_path.as_posix(), providers=["CPUExecutionProvider"])
    onnx_inputs = to_onnx_inputs(batch)

    def sklearn_call():
        _ = sk_model.predict_proba(batch)

    def onnx_call():
        _ = sess.run(None, onnx_inputs)

    sk_t = bench(sklearn_call, warmup=args.warmup, n_runs=args.runs)
    onnx_t = bench(onnx_call, warmup=args.warmup, n_runs=args.runs)

    print(f"Batch size: {len(batch)}")
    print(f"Sklearn avg: {sk_t*1000:.3f} ms/run")
    print(f"ONNX    avg: {onnx_t*1000:.3f} ms/run")
    print(f"Speedup: {sk_t/onnx_t:.2f}x")


if __name__ == "__main__":
    main()
