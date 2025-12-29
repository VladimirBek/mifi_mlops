import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def inject_drift(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Небольшая искусственная имитация дрифта: сдвигаем несколько числовых признаков.
    Это нужно только для демонстрации в учебном проекте.
    """
    rng = np.random.default_rng(seed)
    out = df.copy()

    # Пример: увеличим AGE (если есть)
    if "AGE" in out.columns:
        out["AGE"] = (out["AGE"] + rng.integers(1, 6, size=len(out))).clip(18, 80)

    # Пример: сдвиг сумм по счетам
    bill_cols = [c for c in out.columns if c.startswith("BILL_AMT")]
    for c in bill_cols[:2]:
        out[c] = out[c] * rng.uniform(1.05, 1.15)

    # Пример: ухудшим PAY_0 / задержки
    pay_cols = [c for c in out.columns if c.startswith("PAY_")]
    for c in pay_cols[:2]:
        out[c] = out[c] + rng.integers(0, 2, size=len(out))

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Симуляция новых прод-данных для дрифт мониторинга")
    parser.add_argument("--data-path", default="data/processed/credit.csv")
    parser.add_argument("--out-path", default="data/drift/current.csv")
    parser.add_argument("--rows", type=int, default=2000)
    parser.add_argument("--inject-drift", action="store_true", help="Добавить искусственный дрейф")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.data_path)
    # Берём "тестовую" часть как псевдо-текущие данные
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=args.seed, stratify=df["default"] if "default" in df.columns else None
    )

    cur = test_df.sample(n=min(args.rows, len(test_df)), random_state=args.seed)

    if args.inject_drift:
        cur = inject_drift(cur, seed=args.seed)

    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cur.to_csv(out_path, index=False)
    print(f"Saved current data: {out_path} (rows={len(cur)})")


if __name__ == "__main__":
    main()
