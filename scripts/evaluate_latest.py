import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="data/processed/credit.csv")
    parser.add_argument("--model-path", default="models/model.joblib")
    parser.add_argument("--out-path", default="reports/model_eval.json")
    parser.add_argument("--target-col", default="default")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.data_path)
    X = df.drop(columns=[args.target_col])
    y = df[args.target_col].astype(int)

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, stratify=y
    )

    model = joblib.load(args.model_path)
    proba = model.predict_proba(X_test)[:, 1]
    auc = float(roc_auc_score(y_test, proba))

    out = {"roc_auc": auc}
    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ROC-AUC:", auc)
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
