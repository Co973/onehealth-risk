from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import project_path
from .data import validate_config
from .security import assert_local_output


LOCAL_WARNING = (
    "This tool is local-only. Users remain responsible for consent, de-identification, "
    "storage security, access control, and local clinical/research approvals."
)


def write_model_card(config: dict[str, Any], evaluation_csv: Path | None = None) -> Path:
    validation = validate_config(config)
    out_dir = project_path(config, "paths.reports", "outputs/reports")
    assert_local_output(config, out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = ""
    if evaluation_csv and evaluation_csv.exists():
        metrics_df = pd.read_csv(evaluation_csv).round(3).fillna("")
        headers = list(metrics_df.columns)
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for _, row in metrics_df.iterrows():
            lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
        metrics = "\n".join(lines)
    text = f"""# One Health Risk Model Card

## Site

- Site ID: `{config.get("site_id", "unknown")}`
- Rows available: {validation.row_count}
- Local-only warning: {LOCAL_WARNING}

## Target

- Column: `{config.get("target", {}).get("column", "patient_status")}`
- Positive class: `{config.get("target", {}).get("positive", "Deceased")}`
- Negative class: `{config.get("target", {}).get("negative", "Recovered")}`

## Validation

- Missing required columns: {validation.missing_required_columns or "none"}
- Missing optional feature columns: {validation.missing_optional_columns or "none"}
- Target counts: {validation.target_counts}

## Metrics

{metrics or "Run `onehealth-risk evaluate` to populate model metrics."}

## Limitations

- Current Semarang demo uses severity (`Deceased` vs `Recovered`) as a placeholder target.
- Patient-level non-leptospirosis controls are still needed for true case-control risk modelling.
- Livestock density and daily weather lag features are not yet present.
- Outputs support research validation and are not a standalone clinical decision system.
"""
    path = out_dir / "model_card.md"
    path.write_text(text, encoding="utf-8")
    return path
