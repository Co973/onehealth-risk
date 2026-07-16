from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    config["_config_path"] = str(path)
    config["_project_root"] = str(Path.cwd())
    return config


def project_path(config: dict[str, Any], key_path: str, default: str | None = None) -> Path:
    current: Any = config
    for key in key_path.split("."):
        if not isinstance(current, dict) or key not in current:
            if default is None:
                raise KeyError(f"Missing config key: {key_path}")
            current = default
            break
        current = current[key]
    path = Path(str(current))
    if path.is_absolute():
        return path
    return project_root(config).joinpath(path)


def project_root(config: dict[str, Any]) -> Path:
    security = config.get("security", {})
    root = security.get("project_root") or config.get("_project_root", ".")
    path = Path(str(root))
    if path.is_absolute():
        return path
    return Path(config.get("_project_root", ".")).joinpath(path)


def ensure_local_path(path: Path, project_root: Path) -> None:
    resolved = path.resolve()
    root = project_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"Refusing to use non-local project path: {path}")
