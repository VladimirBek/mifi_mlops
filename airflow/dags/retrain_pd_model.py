from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator


PROJECT_DIR = os.environ.get("PROJECT_DIR", "/opt/project")
DRIFT_THRESHOLD = float(os.environ.get("DRIFT_THRESHOLD", "0.5"))
AUC_MIN = float(os.environ.get("AUC_MIN", "0.65"))
INJECT_DRIFT = os.environ.get("INJECT_DRIFT", "1") == "1"
FORCE_RETRAIN = os.environ.get("FORCE_RETRAIN", "0") == "1"
DATA_TRIGGER_PATH = os.environ.get("DATA_TRIGGER_PATH", f"{PROJECT_DIR}/data/drift/new_data.flag")


def _read_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def decide_retrain() -> str:
    # 1) Явный принудительный флаг
    if FORCE_RETRAIN:
        return "retrain_model"

    # 2) Триггер по данным: если появился флаг-файл (например, внешний загрузчик положил новый батч)
    try:
        if Path(DATA_TRIGGER_PATH).exists():
            return "retrain_model"
    except Exception:
        pass

    # 3) Триггер по дрифту
    summary = _read_json(f"{PROJECT_DIR}/reports/evidently/drift_summary.json")
    drift_share = float(summary.get("drift_share", 0.0))
    dataset_drift = int(summary.get("dataset_drift", 0))

    if dataset_drift == 1 or drift_share >= DRIFT_THRESHOLD:
        return "retrain_model"
    return "skip_retrain"


def check_auc() -> None:
    metrics = _read_json(f"{PROJECT_DIR}/reports/model_eval.json")
    auc = float(metrics.get("roc_auc", 0.0))
    if auc < AUC_MIN:
        raise ValueError(f"ROC-AUC ниже порога: {auc:.4f} < {AUC_MIN:.4f}")


default_args = {
    "owner": "mlops-student",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="retrain_pd_model",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["mlops", "drift", "retrain"],
) as dag:

    start = EmptyOperator(task_id="start")

    simulate_current = BashOperator(
        task_id="simulate_current_data",
        bash_command=(
            "cd $PROJECT_DIR && "
            "python scripts/drift/simulate_production_data.py --rows 2000 "
            + ("--inject-drift " if INJECT_DRIFT else "")
        ),
    )

    drift_report = BashOperator(
        task_id="compute_drift_report",
        bash_command=(
            "cd $PROJECT_DIR && "
            "python -m src.monitoring.drift_job "
            "--reference-path data/processed/credit.csv "
            "--current-path data/drift/current.csv "
            "--model-path models/model.joblib "
            "--out-dir reports/evidently "
        ),
    )

    branch = BranchPythonOperator(
        task_id="branch_retrain",
        python_callable=decide_retrain,
    )

    retrain = BashOperator(
        task_id="retrain_model",
        bash_command=(
            "cd $PROJECT_DIR && "
            "dvc repro --no-scm train && "
            "python -m src.models.train_nn_onnx --data-path data/processed/credit.csv "
            "--model-path models/nn_model.joblib --onnx-path models/nn_model.onnx "
            "&& rm -f data/drift/new_data.flag"
        ),
    )

    skip = EmptyOperator(task_id="skip_retrain")

    evaluate = BashOperator(
        task_id="evaluate_new_model",
        bash_command="cd $PROJECT_DIR && python scripts/evaluate_latest.py",
    )

    quality_gate = PythonOperator(
        task_id="quality_gate",
        python_callable=check_auc,
    )

    mark_ready = BashOperator(
        task_id="mark_model_ready",
        bash_command=(
            "cd $PROJECT_DIR && "
            "mkdir -p reports && "
            'echo "$(date -Iseconds) model_ready" >> reports/retrain_log.txt'
        ),
    )

    end = EmptyOperator(task_id="end")

    start >> simulate_current >> drift_report >> branch
    branch >> retrain >> evaluate >> quality_gate >> mark_ready >> end
    branch >> skip >> end
