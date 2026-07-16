from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import ensure_local_path, project_path
from .features import prepare_training_frame


def make_preprocessor(x: pd.DataFrame) -> ColumnTransformer:
    numeric = [col for col in x.columns if pd.api.types.is_numeric_dtype(x[col])]
    categorical = [col for col in x.columns if col not in numeric]
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=2, sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=2, sparse=False)
    try:
        num_imputer = SimpleImputer(strategy="median", keep_empty_features=True)
        cat_imputer = SimpleImputer(strategy="most_frequent", keep_empty_features=True)
    except TypeError:
        num_imputer = SimpleImputer(strategy="median")
        cat_imputer = SimpleImputer(strategy="most_frequent")
    return ColumnTransformer(
        [
            ("num", Pipeline([("impute", num_imputer), ("scale", StandardScaler())]), numeric),
            ("cat", Pipeline([("impute", cat_imputer), ("onehot", encoder)]), categorical),
        ],
        remainder="drop",
    )


def make_pipeline(x: pd.DataFrame) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", make_preprocessor(x)),
            ("model", LogisticRegression(max_iter=5000, class_weight="balanced")),
        ]
    )


def train_global(config: dict[str, Any]) -> Path:
    df, y, feature_sets = prepare_training_frame(config)
    root = Path(config.get("_project_root", "."))
    out_root = project_path(config, "paths.global_models", "models/global")
    ensure_local_path(out_root, root)
    run_dir = out_root / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "site_id": config.get("site_id", "unknown"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "target": config.get("target", {}),
        "models": {},
    }
    for name, columns in feature_sets.items():
        if not columns:
            continue
        x = df[columns]
        pipe = make_pipeline(x)
        pipe.fit(x, y)
        artifact = run_dir / f"{name}.joblib"
        joblib.dump({"pipeline": pipe, "columns": columns, "feature_set": name}, artifact)
        manifest["models"][name] = {"artifact": artifact.name, "n_features": len(columns), "n_rows": len(x)}

    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    latest = out_root / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    for item in latest.glob("*"):
        if item.is_file():
            item.unlink()
    for item in run_dir.iterdir():
        if item.is_file():
            latest.joinpath(item.name).write_bytes(item.read_bytes())
    return run_dir


def load_model_artifact(base_model: str | Path, feature_set: str = "clinical_environmental_animal") -> dict[str, Any]:
    path = Path(base_model)
    if path.is_dir():
        manifest = json.loads(path.joinpath("manifest.json").read_text(encoding="utf-8"))
        artifact_name = manifest["models"].get(feature_set, next(iter(manifest["models"].values())))["artifact"]
        path = path / artifact_name
    return joblib.load(path)


def train_local(config: dict[str, Any], base_model: str | Path) -> Path:
    from sklearn.linear_model import LogisticRegression

    artifact = load_model_artifact(base_model)
    df, y, _ = prepare_training_frame(config)
    x = df[artifact["columns"]]
    base_scores = artifact["pipeline"].predict_proba(x)[:, 1].reshape(-1, 1)
    calibrator = LogisticRegression(max_iter=1000).fit(base_scores, y)
    site_id = config.get("site_id", "site")
    out_dir = project_path(config, "paths.local_models", "models/local") / site_id
    ensure_local_path(out_dir, Path(config.get("_project_root", ".")))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "local_calibrator.joblib"
    joblib.dump({"calibrator": calibrator, "base_model": str(base_model), "feature_set": artifact["feature_set"]}, path)
    return path
