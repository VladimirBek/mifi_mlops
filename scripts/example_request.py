import argparse

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict")
    args = parser.parse_args()

    payload = {
        "LIMIT_BAL": 200000,
        "SEX": 2,
        "EDUCATION": 2,
        "MARRIAGE": 1,
        "AGE": 35,
        "PAY_0": 0,
        "PAY_2": 0,
        "PAY_3": 0,
        "PAY_4": 0,
        "PAY_5": 0,
        "PAY_6": 0,
        "BILL_AMT1": 50000,
        "BILL_AMT2": 48000,
        "BILL_AMT3": 47000,
        "BILL_AMT4": 46000,
        "BILL_AMT5": 45000,
        "BILL_AMT6": 44000,
        "PAY_AMT1": 2000,
        "PAY_AMT2": 2000,
        "PAY_AMT3": 2000,
        "PAY_AMT4": 2000,
        "PAY_AMT5": 2000,
        "PAY_AMT6": 2000,
    }

    r = httpx.post(args.url, json=payload, timeout=30)
    r.raise_for_status()
    print(r.json())


if __name__ == "__main__":
    main()
