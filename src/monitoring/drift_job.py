import argparse
from pathlib import Path

import pandas as pd

from src.monitoring.drift import DriftConfig, add_model_predictions, run_evidently_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evidently: data drift + performance decay мониторинг"
    )
    parser.add_argument(
        "--reference-path",
        default="data/processed/credit.csv",
        help="Эталонный датасет (обычно train)",
    )
    parser.add_argument(
        "--current-path", default="data/drift/current.csv", help="Текущий датасет (псевдо-прод)"
    )
    parser.add_argument(
        "--model-path",
        default="models/model.joblib",
        help="Sklearn Pipeline (joblib) для предсказаний",
    )
    parser.add_argument("--out-dir", default="reports/evidently", help="Куда сохранять HTML/JSON")
    parser.add_argument("--target-col", default="default")
    parser.add_argument(
        "--drift-threshold",
        type=float,
        default=0.5,
        help="Порог доли дрейфующих фич для флага dataset drift",
    )
    parser.add_argument(
        "--auc-threshold",
        type=float,
        default=0.65,
        help="Порог ROC-AUC для флага performance decay",
    )
    args = parser.parse_args()

    ref_path = Path(args.reference_path)
    cur_path = Path(args.current_path)

    if not cur_path.exists():
        raise FileNotFoundError(
            f"Нет current данных: {cur_path}. "
            "Сначала сгенерируй их (scripts/drift/simulate_production_data.py)"
        )

    reference = pd.read_csv(ref_path)
    current = pd.read_csv(cur_path)

    cfg = DriftConfig(
        target_col=args.target_col,
        drift_share_threshold=args.drift_threshold,
        perf_auc_threshold=args.auc_threshold,
    )

    # Добавляем prediction / proba (для concept drift + performance decay)
    model_path = Path(args.model_path)
    if model_path.exists():
        current = add_model_predictions(current, model_path, cfg)
        reference = add_model_predictions(reference, model_path, cfg)

    out_dir = Path(args.out_dir)
    metrics = run_evidently_report(reference=reference, current=current, cfg=cfg, out_dir=out_dir)

    print("Evidently report saved to:", out_dir.resolve())
    print("Summary metrics:", metrics)


if __name__ == "__main__":
    main()
