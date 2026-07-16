from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from .features import prepare_prediction_frame
from .models import load_model_artifact
from .security import assert_local_output


def predict_csv(
    config: dict[str, Any],
    input_path: str,
    output_path: str,
    model_path: str | Path,
    local_calibrator: str | Path | None = None,
) -> Path:
    artifact = load_model_artifact(model_path)
    df = prepare_prediction_frame(config, input_path)
    x = df.reindex(columns=artifact["columns"])
    scores = artifact["pipeline"].predict_proba(x)[:, 1]
    out = df.copy()
    out["global_risk_score"] = scores
    if local_calibrator:
        local = joblib.load(local_calibrator)
        out["local_risk_score"] = local["calibrator"].predict_proba(scores.reshape(-1, 1))[:, 1]
    path = Path(output_path)
    assert_local_output(config, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    return path
