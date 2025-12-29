import argparse
import json
from pathlib import Path

import pandas as pd


try:
    import great_expectations as ge  # type: ignore

    _GE_AVAILABLE = True
except Exception:  # pragma: no cover
    ge = None  # type: ignore
    _GE_AVAILABLE = False


def load_suite(suite_path: Path) -> dict:
    with open(suite_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_dataframe(df: pd.DataFrame, suite_dict: dict) -> dict:
    if _GE_AVAILABLE:
        validator = ge.from_pandas(df)
        return validator.validate(expectation_suite=suite_dict)

    expectations = suite_dict.get("expectations", []) or []
    results = []
    success_count = 0

    for exp in expectations:
        exp_type = exp.get("expectation_type")
        kwargs = exp.get("kwargs", {}) or {}
        ok = True

        if exp_type == "expect_column_values_to_be_in_set":
            col = kwargs.get("column")
            allowed = set(kwargs.get("value_set", []) or [])
            if col not in df.columns:
                ok = False
            else:
                ok = bool(df[col].isin(list(allowed)).all())

        elif exp_type == "expect_column_values_to_not_be_null":
            col = kwargs.get("column")
            ok = bool(col in df.columns and df[col].notna().all())

        elif exp_type == "expect_column_values_to_be_between":
            col = kwargs.get("column")
            min_v = kwargs.get("min_value")
            max_v = kwargs.get("max_value")
            if col not in df.columns:
                ok = False
            else:
                s = df[col]
                if min_v is not None:
                    ok = ok and bool((s >= min_v).all())
                if max_v is not None:
                    ok = ok and bool((s <= max_v).all())

        else:
            # Unknown expectation type in fallback mode
            ok = False

        results.append({"expectation_config": exp, "success": bool(ok)})
        success_count += int(bool(ok))

    evaluated = len(results)
    overall_success = success_count == evaluated
    return {
        "success": bool(overall_success),
        "statistics": {
            "evaluated_expectations": evaluated,
            "successful_expectations": success_count,
            "unsuccessful_expectations": evaluated - success_count,
        },
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--suite-path", required=True)
    args = parser.parse_args()

    df = pd.read_csv(Path(args.data_path))
    suite = load_suite(Path(args.suite_path))
    result = validate_dataframe(df, suite)

    ok = bool(result.get("success", False))
    stats = result.get("statistics", {})
    print(f"GE validation success={ok}; evaluated={stats.get('evaluated_expectations')}")

    if not ok:
        failed = [r for r in result.get("results", []) if not r.get("success", True)]
        print(f"Failed expectations: {len(failed)}")
        for r in failed[:5]:
            print("-", r.get("expectation_config", {}).get("expectation_type"))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
