from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from .config import project_path, project_root


def synthetic_config() -> dict[str, Any]:
    return {
        "site_id": "synthetic",
        "data": {
            "cases": "data/demo/synthetic_cases.csv",
            "weather": "data/demo/synthetic_weather.csv",
            "population": "data/demo/synthetic_population.csv",
            "lookup": "data/demo/synthetic_kecamatan_lookup.csv",
        },
        "paths": {
            "processed": "data/processed/synthetic",
            "global_models": "models/global",
            "local_models": "models/local",
            "reports": "outputs/reports",
            "predictions": "outputs/predictions",
        },
        "columns": {
            "registered_date": "registered_date",
            "geo_code": "patient_loc_kelurahan_code",
        },
        "target": {
            "column": "patient_status",
            "positive": "Deceased",
            "negative": "Recovered",
        },
        "required_columns": [
            "patient_id",
            "registered_date",
            "patient_age",
            "patient_gender",
            "patient_loc_kelurahan_code",
        ],
        "feature_groups": {
            "clinical": {
                "columns": [
                    "patient_age",
                    "patient_gender",
                    "patient_occupation",
                    "first_symptom_day_offset",
                    "hospitalised_day_offset",
                    "diag_confirmed_day_offset",
                ],
                "prefixes": ["symp_"],
            },
            "environmental": {
                "columns": ["humidity", "temperature_c", "rainfall_mm"],
                "prefixes": ["house_env_", "activity_", "bath_", "wound_"],
            },
            "animal": {
                "columns": ["house_env_rat_sighting"],
                "prefixes": ["animal_present_", "exposure_animal_"],
            },
            "geography": {
                "columns": ["kecamatan_code", "kecamatan_name"],
            },
        },
        "security": {
            "project_root": ".",
            "allow_external_paths": False,
            "require_local_outputs": True,
            "identifier_columns": ["patient_id"],
            "hash_identifier_columns": ["patient_id"],
            "drop_identifier_columns": [],
            "free_text_columns": [],
        },
    }


def write_synthetic_demo(config_path: str | Path = "configs/synthetic.yaml", n_rows: int = 240) -> Path:
    cfg_path = Path(config_path)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    config = synthetic_config()
    config["_project_root"] = str(Path.cwd())

    root = project_root(config)
    data_dir = root / "data" / "demo"
    data_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    months = pd.date_range("2020-01-01", "2023-12-01", freq="MS")
    kecamatan = [f"33.74.{idx:02d}" for idx in range(1, 7)]
    lookup = pd.DataFrame(
        {
            "kecamatan_code": kecamatan,
            "kecamatan_name": [f"Synthetic District {idx}" for idx in range(1, 7)],
        }
    )
    lookup.to_csv(data_dir / "synthetic_kecamatan_lookup.csv", index=False)

    weather_rows = []
    for month in months:
        seasonal = np.sin((month.month - 1) / 12 * 2 * np.pi)
        weather_rows.append(
            {
                "year": month.year,
                "month": month.month,
                "humidity": round(74 + 8 * seasonal + rng.normal(0, 3), 2),
                "temperature_c": round(28 + 1.5 * seasonal + rng.normal(0, 0.7), 2),
                "rainfall_mm": round(max(10, 180 + 80 * seasonal + rng.normal(0, 35)), 2),
            }
        )
    pd.DataFrame(weather_rows).to_csv(data_dir / "synthetic_weather.csv", index=False)

    population_rows = []
    for code, name in zip(lookup["kecamatan_code"], lookup["kecamatan_name"]):
        base = int(rng.integers(55000, 120000))
        for year in range(2020, 2024):
            population_rows.append(
                {
                    "kecamatan_code": code,
                    "kecamatan_name": name,
                    "year": year,
                    "population_field_value": base + (year - 2020) * int(rng.integers(500, 1800)),
                }
            )
    pd.DataFrame(population_rows).to_csv(data_dir / "synthetic_population.csv", index=False)

    rows = []
    for idx in range(n_rows):
        month = months[int(rng.integers(0, len(months)))]
        district_idx = int(rng.integers(0, len(kecamatan)))
        code = kecamatan[district_idx]
        age = int(np.clip(rng.normal(42, 19), 1, 92))
        fever = int(rng.random() < 0.82)
        jaundice = int(rng.random() < 0.18)
        renal = int(rng.random() < 0.09)
        rainfall = weather_rows[(month.year - 2020) * 12 + month.month - 1]["rainfall_mm"]
        rat = int(rng.random() < min(0.75, 0.25 + rainfall / 700))
        risk = -3.1 + 0.018 * age + 0.9 * jaundice + 1.1 * renal + 0.45 * rat + 0.002 * rainfall
        prob = 1 / (1 + np.exp(-risk))
        rows.append(
            {
                "patient_id": f"SYN-{idx + 1:04d}",
                "registered_date": month.strftime("%b/%Y"),
                "patient_age": age,
                "patient_gender": rng.choice(["Female", "Male"]),
                "patient_occupation": rng.choice(["Student", "Farmer", "Market worker", "Office worker"]),
                "patient_loc_kelurahan_code": f"{code}.{int(rng.integers(1, 8)):02d}",
                "first_symptom_day_offset": int(rng.integers(0, 8)),
                "hospitalised_day_offset": int(rng.integers(1, 12)),
                "diag_confirmed_day_offset": int(rng.integers(2, 15)),
                "symp_fever": fever,
                "symp_jaundice": jaundice,
                "symp_renal_signs": renal,
                "house_env_rat_sighting": rat,
                "house_env_flood_prone": int(rng.random() < min(0.8, rainfall / 500)),
                "activity_flood_cleanup": int(rng.random() < 0.22),
                "animal_present_livestock": int(rng.random() < 0.19),
                "exposure_animal_rodent": rat,
                "patient_status": "Deceased" if rng.random() < prob else "Recovered",
            }
        )
    pd.DataFrame(rows).to_csv(data_dir / "synthetic_cases.csv", index=False)

    public_config = synthetic_config()
    cfg_path.write_text(yaml.safe_dump(public_config, sort_keys=False), encoding="utf-8")
    return cfg_path
