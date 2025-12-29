from pathlib import Path
import numpy as np
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
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


def main() -> None:
    src = Path("models/nn_model.onnx")
    dst = Path("models/nn_model_int8.onnx")

    if not src.exists():
        raise FileNotFoundError(f"Missing {src}. Convert ONNX first.")

    dst.parent.mkdir(parents=True, exist_ok=True)

    # Dynamic quantization: weights -> INT8
    quantize_dynamic(
        model_input=src.as_posix(),
        model_output=dst.as_posix(),
        weight_type=QuantType.QInt8,
    )

    src_size = src.stat().st_size
    dst_size = dst.stat().st_size

    print(f"Original ONNX:  {src_size/1024:.1f} KB -> {src}")
    print(f"Quantized ONNX: {dst_size/1024:.1f} KB -> {dst}")
    print(f"Size reduction: {src_size/dst_size:.2f}x")

    # Быстрая sanity-check валидация на 200 строках (чтобы закрыть пункт качественно)
    df = pd.read_csv("data/processed/credit.csv")
    X = df.drop(columns=["default"]).sample(n=min(200, len(df)), random_state=3).reset_index(drop=True)

    sess_orig = ort.InferenceSession(src.as_posix(), providers=["CPUExecutionProvider"])
    sess_int8 = ort.InferenceSession(dst.as_posix(), providers=["CPUExecutionProvider"])

    inputs = to_onnx_inputs(X)
    p_orig = extract_proba(sess_orig.run(None, inputs))
    p_int8 = extract_proba(sess_int8.run(None, inputs))

    diff = np.abs(p_orig - p_int8)
    print(f"Sanity check (200 rows): max_abs_diff={diff.max():.6f}, mean_abs_diff={diff.mean():.6f}")

    # Для quantization допускаем маленькие отличия
    assert diff.max() < 0.05, "Quantized model deviates too much (max diff)."
    assert diff.mean() < 0.02, "Quantized model deviates too much (mean diff)."
    print("OK: quantized model outputs are close to original.")


if __name__ == "__main__":
    main()
