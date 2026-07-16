from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ensure_local_path, project_path, project_root
from .data import load_table


SENSITIVE_NAME_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bname\b",
        r"address",
        r"phone|mobile|whatsapp|tel",
        r"email",
        r"national.?id|nik|ktp|ssn|passport",
        r"note|free.?text|comment|narrative",
    ]
]


def security_settings(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_root": str(project_root(config)),
        "allow_external_paths": bool(config.get("security", {}).get("allow_external_paths", False)),
        "require_local_outputs": bool(config.get("security", {}).get("require_local_outputs", True)),
        "identifier_columns": list(config.get("security", {}).get("identifier_columns", [])),
        "hash_identifier_columns": list(config.get("security", {}).get("hash_identifier_columns", [])),
        "drop_identifier_columns": list(config.get("security", {}).get("drop_identifier_columns", [])),
        "free_text_columns": list(config.get("security", {}).get("free_text_columns", [])),
    }


def assert_local_output(config: dict[str, Any], path: Path) -> None:
    settings = security_settings(config)
    if settings["require_local_outputs"] and not settings["allow_external_paths"]:
        ensure_local_path(path, Path(settings["project_root"]))


def assert_configured_outputs_local(config: dict[str, Any]) -> list[str]:
    checked: list[str] = []
    for key in ["paths.processed", "paths.global_models", "paths.local_models", "paths.reports", "paths.predictions"]:
        path = project_path(config, key, "")
        if str(path):
            assert_local_output(config, path)
            checked.append(str(path))
    return checked


def detect_identifier_columns(columns: list[str], config: dict[str, Any]) -> list[str]:
    configured = set(security_settings(config)["identifier_columns"])
    configured.update(security_settings(config)["free_text_columns"])
    detected: list[str] = []
    for column in columns:
        if column in configured or any(pattern.search(column) for pattern in SENSITIVE_NAME_PATTERNS):
            detected.append(column)
    return detected


def audit_local(config: dict[str, Any]) -> dict[str, Any]:
    settings = security_settings(config)
    paths: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    for section, values in config.items():
        if section.startswith("_") or section not in {"data", "paths"} or not isinstance(values, dict):
            continue
        for key, value in values.items():
            path = project_path(config, f"{section}.{key}")
            status = "ok"
            message = ""
            try:
                if section in {"data", "paths"} and not settings["allow_external_paths"]:
                    ensure_local_path(path, Path(settings["project_root"]))
                if section == "paths":
                    assert_local_output(config, path)
            except ValueError as exc:
                status = "fail"
                message = str(exc)
                errors.append(message)
            paths.append(
                {
                    "key": f"{section}.{key}",
                    "path": str(path),
                    "exists": path.exists(),
                    "status": status,
                    "message": message,
                }
            )

    cases_path = project_path(config, "data.cases")
    if cases_path.exists():
        columns = list(load_table(cases_path).columns)
        identifiers = detect_identifier_columns(columns, config)
        if identifiers:
            warnings.append(f"Potential identifier or free-text columns detected: {', '.join(identifiers)}")

    return {
        "ok": not errors,
        "site_id": config.get("site_id", "unknown"),
        "settings": settings,
        "paths": paths,
        "warnings": warnings,
        "errors": errors,
        "network_required": False,
    }


def write_audit_report(config: dict[str, Any], audit: dict[str, Any] | None = None) -> tuple[Path, Path]:
    audit = audit or audit_local(config)
    out_dir = project_path(config, "paths.reports", "outputs/reports")
    assert_local_output(config, out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "security_audit.json"
    md_path = out_dir / "security_audit.md"
    json_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    path_rows = "\n".join(
        f"| `{row['key']}` | `{row['path']}` | {row['exists']} | {row['status']} | {row['message']} |"
        for row in audit["paths"]
    )
    text = f"""# Security and Locality Audit

- Site ID: `{audit['site_id']}`
- Overall status: `{audit['ok']}`
- Network required for core workflow: `{audit['network_required']}`
- Warnings: {audit['warnings'] or "none"}
- Errors: {audit['errors'] or "none"}

| Key | Path | Exists | Status | Message |
| --- | --- | --- | --- | --- |
{path_rows}
"""
    md_path.write_text(text, encoding="utf-8")
    return json_path, md_path


def deidentify_csv(config: dict[str, Any], input_path: str | Path, output_path: str | Path) -> Path:
    df = pd.read_csv(input_path)
    settings = security_settings(config)
    for column in settings["drop_identifier_columns"]:
        if column in df.columns:
            df = df.drop(columns=[column])
    for column in settings["hash_identifier_columns"]:
        if column in df.columns:
            df[column] = df[column].astype(str).map(
                lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
            )
    out = Path(output_path)
    assert_local_output(config, out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out
