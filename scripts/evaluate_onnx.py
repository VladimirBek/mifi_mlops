import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


CAT_COLS = {"SEX", "EDUCATION", "MARRIAGE", "AGE_BIN"}


def to_onnx_inputs(df: pd.DataFrame) -> dict:
    inputs = {}
    for c in df.columns:
        col = df[[c]]
        if c in CAT_COLS:
            inputs[c] = col.astype(str).values
        else:
            # skl2onnx обычно ожидает float32
            inputs[c] = col.astype(np.float32).values
    return inputs


def extract_proba(outputs) -> np.ndarray:
    probs = outputs[-1]

    # ZipMap: list[dict]
    if isinstance(probs, list) and len(probs) > 0 and isinstance(probs[0], dict):
        out = []
        for d in probs:
            if 1 in d:
                out.append(d[1])
            elif "1" in d:
                out.append(d["1"])
            else:
                out.append(max(d.values()))
        return np.asarray(out, dtype=float)

    probs = np.asarray(probs)
    if probs.ndim == 2 and probs.shape[1] == 2:
        return probs[:, 1].astype(float)
    return probs.reshape(-1).astype(float)


def eval_onnx(onnx_path: str, X: pd.DataFrame, y: pd.Series) -> float:
    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    proba = extract_proba(sess.run(None, to_onnx_inputs(X)))
    return float(roc_auc_score(y, proba))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="data/processed/credit.csv")
    parser.add_argument("--onnx-path", default="models/nn_model.onnx")
    parser.add_argument("--onnx-int8-path", default="models/nn_model_int8.onnx")
    parser.add_argument("--out-path", default="reports/onnx_eval.json")
    parser.add_argument("--target-col", default="default")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.data_path)
    y = df[args.target_col]
    X = df.drop(columns=[args.target_col])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed, stratify=y
    )

    auc_onnx = eval_onnx(args.onnx_path, X_test, y_test)
    auc_int8 = eval_onnx(args.onnx_int8_path, X_test, y_test)

    p1 = Path(args.onnx_path)
    p2 = Path(args.onnx_int8_path)
    out = {
        "onnx": {"path": str(p1), "size_bytes": p1.stat().st_size if p1.exists() else None, "roc_auc": auc_onnx},
        "onnx_int8": {
            "path": str(p2),
            "size_bytes": p2.stat().st_size if p2.exists() else None,
            "roc_auc": auc_int8,
        },
    }

    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("AUC ONNX     :", auc_onnx)
    print("AUC ONNX int8:", auc_int8)
    if out["onnx"]["size_bytes"] and out["onnx_int8"]["size_bytes"]:
        ratio = out["onnx"]["size_bytes"] / out["onnx_int8"]["size_bytes"]
        print(f"Size ratio (onnx/int8): {ratio:.2f}x")
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
