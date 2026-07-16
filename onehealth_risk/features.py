from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .data import load_cases, load_weather_long


def columns_by_prefix(df: pd.DataFrame, prefixes: list[str]) -> list[str]:
    return [col for col in df.columns if any(col.startswith(prefix) for prefix in prefixes)]


def feature_groups(df: pd.DataFrame, config: dict[str, Any]) -> dict[str, list[str]]:
    configured = config.get("feature_groups", {})
    groups: dict[str, list[str]] = {}
    for name, spec in configured.items():
        cols = list(spec.get("columns", []))
        cols.extend(columns_by_prefix(df, list(spec.get("prefixes", []))))
        groups[name] = [col for col in dict.fromkeys(cols) if col in df.columns]
    return groups


def nested_feature_sets(groups: dict[str, list[str]]) -> dict[str, list[str]]:
    clinical = groups.get("clinical", [])
    environmental = groups.get("environmental", [])
    animal = groups.get("animal", [])
    geography = groups.get("geography", [])
    return {
        "clinical": clinical,
        "clinical_environmental": clinical + environmental + geography,
        "clinical_environmental_animal": clinical + environmental + animal + geography,
    }


def prepare_training_frame(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.Series, dict[str, list[str]]]:
    df = load_cases(config)
    weather = load_weather_long(config)
    if {"year", "month"}.issubset(df.columns) and {"year", "month"}.issubset(weather.columns):
        keep = ["year", "month", "humidity", "temperature_c", "rainfall_mm"]
        df = df.merge(weather[keep], on=["year", "month"], how="left")

    target_col = config.get("target", {}).get("column", "patient_status")
    positive = config.get("target", {}).get("positive", "Deceased")
    negative = config.get("target", {}).get("negative", "Recovered")
    if target_col not in df.columns:
        raise ValueError(f"Target column is missing: {target_col}")

    df = df[df[target_col].isin([positive, negative])].copy()
    y = (df[target_col] == positive).astype(int)
    groups = feature_groups(df, config)
    sets = {}
    for name, cols in nested_feature_sets(groups).items():
        available = []
        for col in dict.fromkeys(cols):
            if col in df.columns and col != target_col and df[col].notna().any():
                available.append(col)
        sets[name] = available
    return df.replace("", np.nan), y, sets


def prepare_prediction_frame(config: dict[str, Any], input_path: str) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    if "registered_date" in df.columns and "year" not in df.columns:
        df["registered_dt"] = pd.to_datetime(df["registered_date"], format="%b/%Y", errors="coerce")
        df["year"] = df["registered_dt"].dt.year
        df["month"] = df["registered_dt"].dt.month
    weather = load_weather_long(config)
    if {"year", "month"}.issubset(df.columns) and {"year", "month"}.issubset(weather.columns):
        keep = ["year", "month", "humidity", "temperature_c", "rainfall_mm"]
        df = df.merge(weather[keep], on=["year", "month"], how="left")
    return df.replace("", np.nan)
