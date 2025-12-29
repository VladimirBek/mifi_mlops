from pathlib import Path

import joblib
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


def extract_proba_from_onnx_outputs(outputs) -> np.ndarray:
    # Обычно outputs = [labels, probabilities] или [probabilities] и т.п.
    probs = outputs[-1]

    # 1) ZipMap: список dict (или массив object с dict внутри)
    if isinstance(probs, list) and len(probs) > 0 and isinstance(probs[0], dict):
        # ключи могут быть int (0/1) или str ("0"/"1")
        out = []
        for d in probs:
            if 1 in d:
                out.append(d[1])
            elif "1" in d:
                out.append(d["1"])
            else:
                # fallback: берем максимум по значениям (на крайний случай)
                out.append(max(d.values()))
        return np.asarray(out, dtype=float)

    # Иногда probs приходит как np.ndarray(dtype=object) с dict
    if (
        isinstance(probs, np.ndarray)
        and probs.dtype == object
        and probs.size > 0
        and isinstance(probs.flat[0], dict)
    ):
        out = []
        for d in probs.ravel():
            if 1 in d:
                out.append(d[1])
            elif "1" in d:
                out.append(d["1"])
            else:
                out.append(max(d.values()))
        return np.asarray(out, dtype=float)

    # 2) Нормальный случай: numpy array shape (N,2)
    probs = np.asarray(probs)
    if probs.ndim == 2 and probs.shape[1] == 2:
        return probs[:, 1].astype(float)

    # 3) Если уже (N,)
    return probs.reshape(-1).astype(float)


def main() -> None:
    data_path = Path("data/processed/credit.csv")
    sk_path = Path("models/nn_model.joblib")
    onnx_path = Path("models/nn_model.onnx")

    if not data_path.exists():
        raise FileNotFoundError(f"Missing {data_path}. Run prepare step first.")
    if not sk_path.exists():
        raise FileNotFoundError(f"Missing {sk_path}. Train sklearn NN first.")
    if not onnx_path.exists():
        raise FileNotFoundError(f"Missing {onnx_path}. Convert to ONNX first.")

    df = pd.read_csv(data_path)
    X = df.drop(columns=["default"])

    # Берем небольшой батч для сравнения
    sample = X.sample(n=min(500, len(X)), random_state=7).reset_index(drop=True)

    # sklearn probabilities
    sk_model = joblib.load(sk_path)
    sk_proba = sk_model.predict_proba(sample)[:, 1].astype(float)

    # onnx probabilities
    sess = ort.InferenceSession(onnx_path.as_posix(), providers=["CPUExecutionProvider"])
    onnx_inputs = to_onnx_inputs(sample)
    out = sess.run(None, onnx_inputs)
    onnx_proba = extract_proba_from_onnx_outputs(out)

    # сравнение
    abs_diff = np.abs(sk_proba - onnx_proba)
    max_diff = float(abs_diff.max())
    mean_diff = float(abs_diff.mean())

    print(f"Validation batch size: {len(sample)}")
    print(f"Max abs diff : {max_diff:.6f}")
    print(f"Mean abs diff: {mean_diff:.6f}")

    # допуск: для float32 + разных реализаций математики небольшой diff нормален
    assert max_diff < 1e-3, "ONNX validation failed: max difference too large"
    assert mean_diff < 2e-4, "ONNX validation failed: mean difference too large"

    print("OK: ONNX conversion is correct within tolerance.")


if __name__ == "__main__":
    main()
