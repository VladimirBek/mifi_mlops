from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass(frozen=True)
class Schema:
    target: str = "default"
    categorical: Tuple[str, ...] = ("SEX", "EDUCATION", "MARRIAGE", "AGE_BIN")
    numeric_prefixes: Tuple[str, ...] = ("PAY_", "BILL_AMT", "PAY_AMT")
    numeric_always: Tuple[str, ...] = ("LIMIT_BAL", "AGE", "BILL_AMT_SUM", "PAY_AMT_SUM", "PAY_RATIO")


def split_xy(df: pd.DataFrame, schema: Schema) -> Tuple[pd.DataFrame, pd.Series]:
    X = df.drop(columns=[schema.target])
    y = df[schema.target].astype(int)
    return X, y


def get_feature_lists(df: pd.DataFrame, schema: Schema) -> Tuple[List[str], List[str]]:
    cat_cols = [c for c in schema.categorical if c in df.columns]

    num_cols: List[str] = []
    for c in df.columns:
        if c == schema.target or c in cat_cols:
            continue
        if c in schema.numeric_always or any(c.startswith(pfx) for pfx in schema.numeric_prefixes):
            num_cols.append(c)

    # stable ordering
    num_cols = sorted(set(num_cols), key=lambda x: list(df.columns).index(x))
    return cat_cols, num_cols


def build_preprocessor(cat_cols: List[str], num_cols: List[str]) -> ColumnTransformer:
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, num_cols),
            ("cat", categorical_pipe, cat_cols),
        ],
        remainder="drop",
    )
