import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType, Int64TensorType, StringTensorType
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(cat_cols, num_cols) -> ColumnTransformer:
    num_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    cat_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(missing_values="nan", strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, num_cols),
            ("cat", cat_pipe, cat_cols),
        ],
        remainder="drop",
    )


def infer_types_from_df(df: pd.DataFrame, cat_cols):
    initial_types = []
    for c in df.columns:
        if c in cat_cols:
            initial_types.append((c, StringTensorType([None, 1])))
        else:
            initial_types.append((c, FloatTensorType([None, 1])))
    return initial_types


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="data/processed/credit.csv")
    parser.add_argument("--model-path", default="models/nn_model.joblib")
    parser.add_argument("--onnx-path", default="models/nn_model.onnx")
    args = parser.parse_args()

    df = pd.read_csv(args.data_path)

    target = "default"
    X = df.drop(columns=[target])

    for c in X.columns:
        if X[c].dtype == "object":
            X[c] = X[c].astype(str)
        else:
            X[c] = X[c].astype(np.float32)

    y = df[target].astype(int)

    cat_cols = ["SEX", "EDUCATION", "MARRIAGE", "AGE_BIN"]
    cat_cols = [c for c in cat_cols if c in X.columns]
    num_cols = [c for c in X.columns if c not in cat_cols]
    X = X.copy()

    # Категориальные -> строка (важно для ONNX)
    for c in cat_cols:
        X[c] = X[c].astype(str)

    # Остальные -> float32
    for c in num_cols:
        X[c] = X[c].astype(np.float32)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pre = build_preprocessor(cat_cols, num_cols)

    nn = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        solver="adam",
        max_iter=30,
        random_state=42,
    )

    pipe = Pipeline(steps=[("prep", pre), ("model", nn)])
    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    print(f"NN pipeline trained. ROC-AUC={auc:.4f}")

    model_path = Path(args.model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_path)
    print(f"Saved sklearn NN model: {model_path}")

    # Конвертация в ONNX
    initial_types = infer_types_from_df(X_train.iloc[:5].copy(), cat_cols=cat_cols)
    onnx_model = convert_sklearn(pipe, initial_types=initial_types, target_opset=12)

    onnx_path = Path(args.onnx_path)
    onnx_path.parent.mkdir(parents=True, exist_ok=True)
    onnx_path.write_bytes(onnx_model.SerializeToString())
    print(f"Saved ONNX model: {onnx_path}")


if __name__ == "__main__":
    main()
