import argparse
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, roc_curve
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from src.models.pipeline import Schema, build_preprocessor, get_feature_lists, split_xy


try:
    import mlflow  # type: ignore

    _MLFLOW_AVAILABLE = True
except Exception:  # pragma: no cover
    # MLflow is optional: model training and evaluation can run without experiment tracking.
    mlflow = None  # type: ignore
    _MLFLOW_AVAILABLE = False


def load_params() -> dict:
    with open("params.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def eval_metrics(y_true, y_proba, y_pred) -> dict:
    return {
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "precision": float(precision_score(y_true, y_pred)),
        "recall": float(recall_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred)),
    }


def save_roc_curve(y_true, y_proba, out_path: Path) -> None:
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    plt.figure()
    plt.plot(fpr, tpr)
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def run_one_experiment(
    name: str,
    estimator,
    X_train,
    y_train,
    X_test,
    y_test,
    tune: bool,
    n_iter: int,
):
    schema = Schema()
    cat_cols, num_cols = get_feature_lists(pd.concat([X_train, X_test], axis=0), schema)
    preprocessor = build_preprocessor(cat_cols, num_cols)

    pipe = Pipeline(steps=[("prep", preprocessor), ("model", estimator)])

    run_name = f"{name}{'_tuned' if tune else ''}"

    final_model = pipe

    if tune:
        param_distributions = {}
        if isinstance(estimator, LogisticRegression):
            param_distributions = {
                "model__C": np.logspace(-3, 1, 20),
                "model__solver": ["lbfgs", "liblinear"],
                "model__max_iter": [500],
            }
        elif isinstance(estimator, RandomForestClassifier):
            param_distributions = {
                "model__n_estimators": [200, 400, 600],
                "model__max_depth": [None, 5, 10, 15],
                "model__min_samples_split": [2, 5, 10],
            }
        elif isinstance(estimator, GradientBoostingClassifier):
            param_distributions = {
                "model__n_estimators": [100, 200, 400],
                "model__learning_rate": [0.03, 0.05, 0.1],
                "model__max_depth": [2, 3, 4],
            }
        elif isinstance(estimator, SVC):
            param_distributions = {
                "model__C": np.logspace(-2, 2, 10),
                "model__gamma": ["scale", "auto"],
                "model__kernel": ["rbf"],
            }

        search = RandomizedSearchCV(
            estimator=pipe,
            param_distributions=param_distributions,
            n_iter=n_iter,
            scoring="roc_auc",
            cv=3,
            n_jobs=-1,
            random_state=42,
        )
        search.fit(X_train, y_train)
        final_model = search.best_estimator_
        best_params = search.best_params_
        cv_best = float(search.best_score_)
    else:
        final_model.fit(X_train, y_train)
        best_params = {}
        cv_best = None

    y_proba = final_model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)
    metrics = eval_metrics(y_test, y_proba, y_pred)

    roc_path = Path("artifacts") / f"roc_{run_name}.png"
    save_roc_curve(y_test, y_proba, roc_path)

    if not _MLFLOW_AVAILABLE:
        return metrics, final_model

    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("model_name", name)
        mlflow.log_param("tuned", tune)
        mlflow.log_param("cat_cols", ",".join(cat_cols))
        mlflow.log_param("num_cols_count", len(num_cols))
        if best_params:
            mlflow.log_params(best_params)
        if cv_best is not None:
            mlflow.log_metric("cv_best_score", cv_best)

        mlflow.log_metrics(metrics)
        mlflow.log_artifact(str(roc_path))
        mlflow.sklearn.log_model(final_model, artifact_path="model")

    return metrics, final_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--model-path", required=True)
    args = parser.parse_args()

    params = load_params()
    test_size = float(params.get("train", {}).get("test_size", 0.2))
    random_state = int(params.get("train", {}).get("random_state", 42))
    n_iter = int(params.get("train", {}).get("n_iter_search", 10))

    df = pd.read_csv(args.data_path)
    schema = Schema()
    X, y = split_xy(df, schema)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    if _MLFLOW_AVAILABLE:
        mlflow.set_experiment("credit_scoring_pd")

    # >= 5 experiments total
    experiments = [
        ("logreg", LogisticRegression(max_iter=500), False),
        ("logreg", LogisticRegression(max_iter=500), True),
        ("rf", RandomForestClassifier(random_state=42), False),
        ("rf", RandomForestClassifier(random_state=42), True),
        ("gb", GradientBoostingClassifier(random_state=42), False),
        ("svc", SVC(probability=True, random_state=42), False),
    ]

    best_auc = -1.0
    best_model = None
    best_name = None

    for name, est, tune in experiments:
        metrics, model = run_one_experiment(
            name=name,
            estimator=est,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            tune=tune,
            n_iter=n_iter,
        )
        if metrics["roc_auc"] > best_auc:
            best_auc = metrics["roc_auc"]
            best_model = model
            best_name = f"{name}{'_tuned' if tune else ''}"

    out_path = Path(args.model_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, out_path)
    print(f"Saved best model: {out_path} (best={best_name}, roc_auc={best_auc:.4f})")


if __name__ == "__main__":
    main()
