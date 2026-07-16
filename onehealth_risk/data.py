from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import project_path


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    row_count: int
    missing_required_columns: list[str]
    missing_optional_columns: list[str]
    target_counts: dict[str, int]
    feature_availability: dict[str, int]


def load_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def load_cases(config: dict[str, Any]) -> pd.DataFrame:
    cases = load_table(project_path(config, "data.cases"))
    date_col = config.get("columns", {}).get("registered_date", "registered_date")
    if date_col in cases.columns:
        cases["registered_dt"] = pd.to_datetime(cases[date_col], format="%b/%Y", errors="coerce")
        cases["year"] = cases["registered_dt"].dt.year
        cases["month"] = cases["registered_dt"].dt.month
        cases["month_start"] = cases["registered_dt"].dt.to_period("M").dt.to_timestamp()
    geo_col = config.get("columns", {}).get("geo_code", "patient_loc_kelurahan_code")
    if geo_col in cases.columns and "kecamatan_code" not in cases.columns:
        cases["kecamatan_code"] = cases[geo_col].astype(str).str.extract(r"^(33\.74\.\d{2})\.")
    lookup_path = config.get("data", {}).get("lookup")
    if lookup_path and "kecamatan_code" in cases.columns:
        lookup = load_table(project_path(config, "data.lookup"))
        cases = cases.merge(lookup, on="kecamatan_code", how="left")
    return cases


def load_weather_long(config: dict[str, Any]) -> pd.DataFrame:
    weather = load_table(project_path(config, "data.weather"))
    if {"year", "month", "humidity", "temperature_c", "rainfall_mm"}.issubset(weather.columns):
        weather["month_start"] = pd.to_datetime(
            weather[["year", "month"]].assign(day=1), errors="coerce"
        )
        return weather

    month_order = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }
    rows: list[dict[str, Any]] = []
    for _, row in weather.iterrows():
        month = month_order[row["month_name"]]
        for suffix in range(18, 24):
            year = 2000 + suffix
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "month_start": pd.Timestamp(year=year, month=month, day=1),
                    "humidity": row.get(f"humidity_pctrh_{suffix}"),
                    "temperature_c": row.get(f"tempc_{suffix}"),
                    "rainfall_mm": row.get(f"rainfallmm_{suffix}"),
                }
            )
    return pd.DataFrame(rows)


def load_population_long(config: dict[str, Any]) -> pd.DataFrame:
    population = load_table(project_path(config, "data.population"))
    if {"kecamatan_name", "year", "population_field_value"}.issubset(population.columns):
        return population
    long = population.melt(
        id_vars="kecamatan_name",
        var_name="year",
        value_name="population_field_value",
    )
    long["year"] = long["year"].astype(str).str.replace("y", "", regex=False).astype(int)
    return long


def validate_config(config: dict[str, Any]) -> ValidationResult:
    cases = load_cases(config)
    target_col = config.get("target", {}).get("column", "patient_status")
    required = list(config.get("required_columns", [])) + [target_col]
    missing_required = [col for col in dict.fromkeys(required) if col not in cases.columns]

    optional = []
    for group in config.get("feature_groups", {}).values():
        optional.extend(group.get("columns", []))
    missing_optional = [col for col in dict.fromkeys(optional) if col not in cases.columns]

    target_counts: dict[str, int] = {}
    if target_col in cases.columns:
        target_counts = {
            str(key): int(value)
            for key, value in cases[target_col].fillna("<missing>").value_counts().items()
        }

    availability = {
        col: int(cases[col].notna().sum())
        for col in optional
        if col in cases.columns
    }
    return ValidationResult(
        ok=not missing_required,
        row_count=len(cases),
        missing_required_columns=missing_required,
        missing_optional_columns=missing_optional,
        target_counts=target_counts,
        feature_availability=availability,
    )
