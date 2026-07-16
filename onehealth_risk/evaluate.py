from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from .config import project_path
from .features import prepare_training_frame
from .models import make_pipeline
from .security import assert_local_output


def classification_metrics(y_true: pd.Series, scores: np.ndarray) -> dict[str, float]:
    pred = (scores >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "auroc": float(roc_auc_score(y_true, scores)) if y_true.nunique() == 2 else float("nan"),
        "sensitivity": float(tp / (tp + fn)) if (tp + fn) else float("nan"),
        "specificity": float(tn / (tn + fp)) if (tn + fp) else float("nan"),
        "calibration_mean_predicted": float(np.mean(scores)),
        "calibration_observed": float(np.mean(y_true)),
        "true_positive": int(tp),
        "false_positive": int(fp),
        "true_negative": int(tn),
        "false_negative": int(fn),
    }


def evaluate_config(config: dict[str, Any]) -> Path:
    df, y, feature_sets = prepare_training_frame(config)
    cv = StratifiedKFold(n_splits=min(5, y.value_counts().min()), shuffle=True, random_state=42)
    rows = []
    for name, columns in feature_sets.items():
        if not columns:
            rows.append({"feature_set": name, "n_features": 0, "note": "no available columns"})
            continue
        x = df[columns]
        pipe = make_pipeline(x)
        try:
            scores = cross_val_predict(pipe, x, y, cv=cv, method="predict_proba")[:, 1]
            row = {"feature_set": name, "n_rows": len(x), "n_features": len(columns), "note": ""}
            row.update(classification_metrics(y, scores))
        except Exception as exc:
            row = {"feature_set": name, "n_rows": len(x), "n_features": len(columns), "note": str(exc)}
        rows.append(row)

    out_dir = project_path(config, "paths.reports", "outputs/reports")
    assert_local_output(config, out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "model_comparison.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out
