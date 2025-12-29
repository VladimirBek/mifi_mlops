import argparse
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd


CAT_COLS = {"SEX", "EDUCATION", "MARRIAGE", "AGE_BIN"}


def to_onnx_inputs(df: pd.DataFrame) -> dict:
    inputs = {}
    for c in df.columns:
        col = df[[c]]
        if c in CAT_COLS:
            inputs[c] = col.astype(str).values
        else:
            inputs[c] = col.astype(np.float32).values
    return inputs


def bench(fn, warmup: int, n_runs: int) -> float:
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
    parser.add_argument("--onnx-orig", default="models/nn_model.onnx")
    parser.add_argument("--onnx-int8", default="models/nn_model_int8.onnx")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--warmup", type=int, default=30)
    parser.add_argument("--runs", type=int, default=300)
    args = parser.parse_args()

    df = pd.read_csv(args.data_path)
    X = df.drop(columns=["default"])
    batch = X.sample(n=min(args.batch_size, len(X)), random_state=1).reset_index(drop=True)
    inputs = to_onnx_inputs(batch)

    sess_orig = ort.InferenceSession(Path(args.onnx_orig).as_posix(), providers=["CPUExecutionProvider"])
    sess_int8 = ort.InferenceSession(Path(args.onnx_int8).as_posix(), providers=["CPUExecutionProvider"])

    def orig_call():
        _ = sess_orig.run(None, inputs)

    def int8_call():
        _ = sess_int8.run(None, inputs)

    t_orig = bench(orig_call, warmup=args.warmup, n_runs=args.runs)
    t_int8 = bench(int8_call, warmup=args.warmup, n_runs=args.runs)

    print(f"Batch size: {len(batch)}")
    print(f"ONNX original avg: {t_orig*1000:.3f} ms/run")
    print(f"ONNX INT8    avg: {t_int8*1000:.3f} ms/run")
    print(f"Speedup (orig/int8): {t_orig/t_int8:.2f}x")


if __name__ == "__main__":
    main()
