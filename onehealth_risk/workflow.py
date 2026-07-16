from __future__ import annotations

import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .config import project_path
from .data import validate_config
from .evaluate import evaluate_config
from .features import prepare_training_frame
from .models import train_global
from .predict import predict_csv
from .reports import write_model_card
from .security import audit_local, assert_configured_outputs_local, write_audit_report


def write_feature_availability(config: dict[str, Any]) -> Path:
    validation = validate_config(config)
    out_dir = project_path(config, "paths.reports", "outputs/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {"feature": key, "available_rows": value, "total_rows": validation.row_count}
        for key, value in validation.feature_availability.items()
    ]
    out = out_dir / "feature_availability.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def write_reproducibility_report(
    config: dict[str, Any],
    commands: list[str],
    artifacts: dict[str, str],
    audit: dict[str, Any],
) -> Path:
    validation = validate_config(config)
    _, _, feature_sets = prepare_training_frame(config)
    out_dir = project_path(config, "paths.reports", "outputs/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    command_lines = "\n".join(f"- `{command}`" for command in commands)
    feature_lines = "\n".join(f"- `{name}`: {len(columns)} features" for name, columns in feature_sets.items())
    artifact_lines = "\n".join(f"- {name}: `{path}`" for name, path in artifacts.items())
    text = f"""# Reproducibility Report

- Generated at: {datetime.now().isoformat(timespec="seconds")}
- Package version: 0.1.0
- Python version: {sys.version.split()[0]}
- Platform: {platform.platform()}
- Site ID: `{config.get("site_id", "unknown")}`
- Rows: {validation.row_count}
- Target counts: {validation.target_counts}
- Security audit status: `{audit["ok"]}`
- Network required for core workflow: `False`

## Commands

{command_lines}

## Feature Sets

{feature_lines}

## Artifacts

{artifact_lines}

## Security Notes

Warnings: {audit["warnings"] or "none"}

This software artifact is research-oriented and local-first. It is not a clinical validation claim, diagnostic model, deployment-ready decision support system, or regulatory compliance certification.
"""
    path = out_dir / "reproducibility_report.md"
    path.write_text(text, encoding="utf-8")
    return path


def write_local_workflow_summary(config: dict[str, Any], audit: dict[str, Any]) -> Path:
    out_dir = project_path(config, "paths.reports", "outputs/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {"control": "Local-only processing", "status": "enabled", "note": "Core workflow requires no network access."},
        {"control": "Project-root output guard", "status": "pass" if audit["ok"] else "fail", "note": "Configured artifact paths are audited."},
        {"control": "Identifier warnings", "status": "enabled", "note": "Configured and heuristic identifier columns are reported."},
        {"control": "Synthetic public demo", "status": "available", "note": "Reviewers can run without private patient data."},
    ]
    out = out_dir / "security_controls.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def run_all(config: dict[str, Any]) -> dict[str, Path]:
    assert_configured_outputs_local(config)
    validation = validate_config(config)
    if not validation.ok:
        raise ValueError(f"Config validation failed: {validation.missing_required_columns}")
    audit = audit_local(config)
    if not audit["ok"]:
        raise ValueError(f"Security audit failed: {audit['errors']}")

    audit_json, audit_md = write_audit_report(config, audit)
    model_dir = train_global(config)
    comparison = evaluate_config(config)
    model_card = write_model_card(config, comparison)
    feature_availability = write_feature_availability(config)
    controls = write_local_workflow_summary(config, audit)

    pred_dir = project_path(config, "paths.predictions", "outputs/predictions")
    pred_dir.mkdir(parents=True, exist_ok=True)
    pred_name = "demo_predictions.csv" if config.get("site_id") == "synthetic" else f"{config.get('site_id', 'site')}_predictions.csv"
    predictions = predict_csv(
        config,
        str(project_path(config, "data.cases")),
        str(pred_dir / pred_name),
        model_dir,
    )
    commands = [
        f"onehealth-risk validate --config {config['_config_path']}",
        f"onehealth-risk audit-local --config {config['_config_path']}",
        f"onehealth-risk train --config {config['_config_path']}",
        f"onehealth-risk evaluate --config {config['_config_path']}",
        f"onehealth-risk report --config {config['_config_path']}",
        f"onehealth-risk predict --config {config['_config_path']} --input {project_path(config, 'data.cases')} --output {predictions}",
    ]
    artifacts = {
        "security_audit_json": str(audit_json),
        "security_audit_md": str(audit_md),
        "model_dir": str(model_dir),
        "model_comparison": str(comparison),
        "model_card": str(model_card),
        "feature_availability": str(feature_availability),
        "security_controls": str(controls),
        "predictions": str(predictions),
    }
    report = write_reproducibility_report(config, commands, artifacts, audit)
    artifacts["reproducibility_report"] = str(report)
    return {key: Path(value) for key, value in artifacts.items()}
