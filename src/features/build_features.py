import numpy as np
import pandas as pd


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Minimal feature engineering for a student project."""
    df = df.copy()

    bill_cols = [c for c in df.columns if c.startswith("BILL_AMT")]
    pay_cols = [c for c in df.columns if c.startswith("PAY_AMT")]

    df["BILL_AMT_SUM"] = df[bill_cols].sum(axis=1) if bill_cols else 0.0
    df["PAY_AMT_SUM"] = df[pay_cols].sum(axis=1) if pay_cols else 0.0

    denom = df["BILL_AMT_SUM"].replace(0, np.nan)
    df["PAY_RATIO"] = (df["PAY_AMT_SUM"] / denom).fillna(0.0).clip(lower=0.0)

    bins = [0, 25, 35, 45, 55, 65, 200]
    labels = ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]
    df["AGE_BIN"] = pd.cut(df["AGE"], bins=bins, labels=labels, right=False).astype(str)

    return df
