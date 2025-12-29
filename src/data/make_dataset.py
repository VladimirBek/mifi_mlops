import argparse
from pathlib import Path

import pandas as pd
import requests
import yaml

from src.features.build_features import build_features

UCI_XLS_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00350/"
    "default%20of%20credit%20card%20clients.xls"
)


def load_params() -> dict:
    with open("params.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def download_xls(dst_path: Path) -> None:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    if dst_path.exists():
        return
    resp = requests.get(UCI_XLS_URL, timeout=60)
    resp.raise_for_status()
    dst_path.write_bytes(resp.content)


def read_raw_xls(xls_path: Path) -> pd.DataFrame:
    # In UCI file first row is a title, header starts at row 2
    df = pd.read_excel(xls_path, header=1)
    df = df.rename(columns={"default payment next month": "default"})
    df = df.drop(columns=["ID"], errors="ignore")
    return df


def clean_and_prepare(df: pd.DataFrame, sample_rows: int = 0) -> pd.DataFrame:
    if sample_rows and sample_rows > 0:
        df = df.sample(n=min(sample_rows, len(df)), random_state=42)

    df.columns = [c.strip() for c in df.columns]
    df = df.dropna(subset=["default"])

    # Feature engineering
    df = build_features(df)

    # Keep stable column order for GE suite
    ordered_cols = [
        "LIMIT_BAL",
        "SEX",
        "EDUCATION",
        "MARRIAGE",
        "AGE",
        "PAY_0",
        "PAY_2",
        "PAY_3",
        "PAY_4",
        "PAY_5",
        "PAY_6",
        "BILL_AMT1",
        "BILL_AMT2",
        "BILL_AMT3",
        "BILL_AMT4",
        "BILL_AMT5",
        "BILL_AMT6",
        "PAY_AMT1",
        "PAY_AMT2",
        "PAY_AMT3",
        "PAY_AMT4",
        "PAY_AMT5",
        "PAY_AMT6",
        "default",
        "BILL_AMT_SUM",
        "PAY_AMT_SUM",
        "PAY_RATIO",
        "AGE_BIN",
    ]
    df = df[ordered_cols]
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-path", required=True)
    parser.add_argument("--processed-path", required=True)
    args = parser.parse_args()

    params = load_params()
    sample_rows = int(params.get("prepare", {}).get("sample_rows", 0))

    raw_path = Path(args.raw_path)
    processed_path = Path(args.processed_path)

    download_xls(raw_path)
    df_raw = read_raw_xls(raw_path)
    df = clean_and_prepare(df_raw, sample_rows=sample_rows)

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_path, index=False)
    print(f"Saved processed data: {processed_path} (rows={len(df)})")


if __name__ == "__main__":
    main()
