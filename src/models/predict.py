import argparse
from pathlib import Path

import joblib
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()

    model = joblib.load(Path(args.model_path))
    df = pd.read_csv(Path(args.input_csv))
    proba = model.predict_proba(df)[:, 1]
    pred = (proba >= 0.5).astype(int)

    out = df.copy()
    out["pred_class"] = pred
    out["pred_proba"] = proba
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(Path(args.output_csv), index=False)
    print(f"Saved predictions to {args.output_csv}")


if __name__ == "__main__":
    main()
