import numpy as np

from src.models.train import eval_metrics


def test_eval_metrics_keys():
    y_true = np.array([0, 1, 0, 1])
    y_proba = np.array([0.1, 0.9, 0.2, 0.8])
    y_pred = (y_proba >= 0.5).astype(int)

    m = eval_metrics(y_true, y_proba, y_pred)
    assert set(m.keys()) == {"roc_auc", "precision", "recall", "f1"}
