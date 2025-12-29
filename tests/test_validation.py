import pandas as pd

from src.data.validation import validate_dataframe


def test_validation_fails_on_bad_target():
    df = pd.DataFrame(
        {
            "default": [0, 2],
        }
    )
    suite = {
        "expectation_suite_name": "tmp",
        "expectations": [
            {
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {"column": "default", "value_set": [0, 1]},
            }
        ],
    }
    res = validate_dataframe(df, suite)
    assert res["success"] is False
