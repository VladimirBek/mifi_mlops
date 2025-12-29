import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

from evidently import ColumnMapping, Report
from evidently.presets import DataDriftPreset, ClassificationPreset


@dataclass
class DriftConfig:
    target_col: str = "default"
    prediction_col: str = "prediction"
    proba_col: str = "prediction_proba"
    drift_share_threshold: float = 0.5
    perf_auc_threshold: float = 0.65


def _split_columns(
    df: pd.DataFrame, target_col: str, prediction_col: str, proba_col: str
) -> Tuple[List[str], List[str]]:
    drop_cols = {target_col, prediction_col, proba_col}
    features = [c for c in df.columns if c not in drop_cols]
    cat = [c for c in features if df[c].dtype == "object"]
    num = [c for c in features if c not in cat]
    return num, cat


def build_column_mapping(df: pd.DataFrame, cfg: DriftConfig) -> ColumnMapping:
    num, cat = _split_columns(df, cfg.target_col, cfg.prediction_col, cfg.proba_col)
    return ColumnMapping(
        target=cfg.target_col,
        prediction=cfg.prediction_col,
        numerical_features=num,
        categorical_features=cat,
    )


def add_model_predictions(df: pd.DataFrame, model_path: Path, cfg: DriftConfig) -> pd.DataFrame:
    """Добавляет prediction и prediction_proba в датасет (для performance decay / concept drift).
    Ожидается sklearn Pipeline (joblib).
    """
    pipe = joblib.load(model_path)
    X = df.drop(columns=[cfg.target_col], errors="ignore")
    proba = pipe.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)
    out = df.copy()
    out[cfg.proba_col] = proba.astype(float)
    out[cfg.prediction_col] = pred.astype(int)
    return out


def compute_perf_metrics(df: pd.DataFrame, cfg: DriftConfig) -> Dict[str, float]:
    if cfg.target_col not in df.columns:
        return {}

    y_true = df[cfg.target_col].astype(int).to_numpy()
    y_pred = df[cfg.prediction_col].astype(int).to_numpy()

    metrics: Dict[str, float] = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    if cfg.proba_col in df.columns:
        y_proba = df[cfg.proba_col].astype(float).to_numpy()
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        except Exception:
            metrics["roc_auc"] = float("nan")
    return metrics


def run_evidently_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    cfg: DriftConfig,
    out_dir: Path,
    name_prefix: str = "drift",
) -> Dict[str, float]:
    """Строит Evidently Report (DataDrift + Classification) и сохраняет HTML+JSON.
    Возвращает агрегированные метрики для CI/Airflow/алертов.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # ColumnMapping лучше строить по объединённому датасету (чтобы типы совпадали)
    combined = pd.concat([reference, current], ignore_index=True)
    cm = build_column_mapping(combined, cfg)

    report = Report(
        [
            DataDriftPreset(),
            ClassificationPreset(),
        ]
    )

    evaluation = report.run(current_data=current, reference_data=reference, column_mapping=cm)

    html_path = out_dir / f"{name_prefix}_report.html"
    json_path = out_dir / f"{name_prefix}_report.json"
    snapshot_path = out_dir / f"{name_prefix}_snapshot.json"

    # В новой API сохраняем через evaluation (см. официальные примеры)
    evaluation.save_html(str(html_path))
    evaluation.save_json(str(json_path))
    evaluation.save(str(snapshot_path))

    # Извлекаем агрегаты из dict-формата
    # Примечание: структура может меняться между версиями,
    # поэтому используем максимально устойчивый парсинг.
    d = evaluation.dict()

    drift_share = _safe_get(
        d,
        [
            ("metrics", 0, "result", "share_of_drifted_columns"),
            ("metrics", 0, "result", "drift_share"),
        ],
        default=None,
    )

    dataset_drift = _safe_get(
        d,
        [
            ("metrics", 0, "result", "dataset_drift"),
            ("metrics", 0, "result", "dataset_drift_detected"),
        ],
        default=None,
    )

    out_metrics: Dict[str, float] = {}

    if drift_share is not None:
        out_metrics["drift_share"] = float(drift_share)
    if dataset_drift is not None:
        out_metrics["dataset_drift"] = float(bool(dataset_drift))

    # Если ground truth есть — Evidently тоже считает performance.
    # Дополнительно считаем метрики самостоятельно.
    perf = compute_perf_metrics(current, cfg)
    out_metrics.update(
        {f"perf_{k}": float(v) for k, v in perf.items() if v == v}
    )  # v==v -> not NaN

    # Пишем удобный summary
    summary_path = out_dir / f"{name_prefix}_summary.json"
    summary_path.write_text(
        json.dumps(out_metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_metrics


def _safe_get(d: dict, paths: List[Tuple], default=None):
    for path in paths:
        cur = d
        ok = True
        for p in path:
            try:
                cur = cur[p]
            except Exception:
                ok = False
                break
        if ok:
            return cur
    return default
