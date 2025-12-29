import pandas as pd

from src.features.build_features import build_features


def test_build_features_adds_columns():
    df = pd.DataFrame(
        {
            "AGE": [30, 50],
            "BILL_AMT1": [100.0, 200.0],
            "BILL_AMT2": [0.0, 100.0],
            "PAY_AMT1": [10.0, 20.0],
            "PAY_AMT2": [0.0, 10.0],
        }
    )
    out = build_features(df)
    assert "BILL_AMT_SUM" in out.columns
    assert "PAY_AMT_SUM" in out.columns
    assert "PAY_RATIO" in out.columns
    assert "AGE_BIN" in out.columns
    assert out["PAY_RATIO"].min() >= 0.0
