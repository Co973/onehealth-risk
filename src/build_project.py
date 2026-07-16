from __future__ import annotations

import matplotlib
from pathlib import Path

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.metrics import mean_poisson_deviance, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
FIGURES = Path("outputs/figures")
TABLES = Path("outputs/tables")


def ensure_dirs() -> None:
    for path in [PROCESSED, FIGURES, TABLES]:
        path.mkdir(parents=True, exist_ok=True)


def load_cases() -> pd.DataFrame:
    cases = pd.read_csv(RAW / "leptospirosis_surveillance_cases_semarang_2018_2023.csv")
    cases["registered_dt"] = pd.to_datetime(cases["registered_date"], format="%b/%Y")
    cases["year"] = cases["registered_dt"].dt.year
    cases["month"] = cases["registered_dt"].dt.month
    cases["month_start"] = cases["registered_dt"].dt.to_period("M").dt.to_timestamp()
    cases["kecamatan_code"] = cases["patient_loc_kelurahan_code"].astype(str).str.extract(
        r"^(33\.74\.\d{2})\."
    )
    lookup = pd.read_csv(RAW / "semarang_kecamatan_lookup.csv")
    cases = cases.merge(lookup, on="kecamatan_code", how="left")
    return cases


def load_weather_long() -> pd.DataFrame:
    weather = pd.read_csv(RAW / "semarang_monthly_weather_2018_2023.csv")
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
    rows = []
    for _, row in weather.iterrows():
        month = month_order[row["month_name"]]
        for suffix in range(18, 24):
            year = 2000 + suffix
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "month_start": pd.Timestamp(year=year, month=month, day=1),
                    "humidity": row[f"humidity_pctrh_{suffix}"],
                    "temperature_c": row[f"tempc_{suffix}"],
                    "rainfall_mm": row[f"rainfallmm_{suffix}"],
                }
            )
    return pd.DataFrame(rows)


def load_population_long() -> pd.DataFrame:
    population = pd.read_csv(RAW / "semarang_population_estimates_2018_2023.csv")
    long = population.melt(
        id_vars="kecamatan_name",
        var_name="year",
        value_name="population_field_value",
    )
    long["year"] = long["year"].str.replace("y", "", regex=False).astype(int)
    return long


def build_monthly_panel(cases: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    months = pd.DataFrame({"month_start": pd.date_range("2018-01-01", "2023-12-01", freq="MS")})
    months["year"] = months["month_start"].dt.year
    months["month"] = months["month_start"].dt.month
    counts = cases.groupby(["year", "month"]).size().reset_index(name="case_count")
    panel = months.merge(counts, on=["year", "month"], how="left")
    panel["case_count"] = panel["case_count"].fillna(0).astype(int)
    panel = panel.merge(weather, on=["year", "month", "month_start"], how="left")
    panel["rainfall_lag1_mm"] = panel["rainfall_mm"].shift(1)
    panel["rainfall_lag1_mm"] = panel["rainfall_lag1_mm"].fillna(panel["rainfall_mm"])
    panel.to_csv(PROCESSED / "monthly_ecological_panel.csv", index=False)
    return panel


def fit_ecological_model(panel: pd.DataFrame) -> pd.DataFrame:
    features = ["humidity", "temperature_c", "rainfall_mm", "rainfall_lag1_mm"]
    x = panel[features]
    y = panel["case_count"]
    pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", PoissonRegressor(alpha=0.1, max_iter=5000)),
        ]
    )
    pipe.fit(x, y)
    pred = pipe.predict(x)
    model = pipe.named_steps["model"]
    result = pd.DataFrame(
        {
            "feature": ["intercept"] + features,
            "coefficient": [model.intercept_] + list(model.coef_),
        }
    )
    result["mean_poisson_deviance"] = mean_poisson_deviance(y, np.clip(pred, 1e-9, None))
    result.to_csv(TABLES / "ecological_poisson_coefficients.csv", index=False)
    return result


def build_kecamatan_year_panel(cases: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    lookup = pd.read_csv(RAW / "semarang_kecamatan_lookup.csv")
    years = pd.DataFrame({"year": range(2018, 2024)})
    grid = lookup.merge(years, how="cross")
    counts = (
        cases.groupby(["kecamatan_code", "kecamatan_name", "year"])
        .size()
        .reset_index(name="case_count")
    )
    panel = grid.merge(counts, on=["kecamatan_code", "kecamatan_name", "year"], how="left")
    panel["case_count"] = panel["case_count"].fillna(0).astype(int)
    panel = panel.merge(population, on=["kecamatan_name", "year"], how="left")
    panel["case_rate_per_100k_population_field"] = (
        panel["case_count"] / panel["population_field_value"] * 100000
    )
    panel.to_csv(PROCESSED / "kecamatan_year_panel.csv", index=False)
    return panel


def plot_outputs(monthly: pd.DataFrame, kec_panel: pd.DataFrame) -> None:
    fig, ax1 = plt.subplots(figsize=(11, 5))
    ax1.plot(monthly["month_start"], monthly["case_count"], color="#1f77b4", marker="o")
    ax1.set_ylabel("Leptospirosis cases")
    ax2 = ax1.twinx()
    ax2.plot(monthly["month_start"], monthly["humidity"], color="#d62728", alpha=0.7)
    ax2.set_ylabel("Humidity")
    ax1.set_title("Monthly leptospirosis cases and humidity, Semarang")
    fig.tight_layout()
    fig.savefig(FIGURES / "monthly_cases_vs_humidity.png", dpi=180)
    plt.close(fig)

    by_kec = (
        kec_panel.groupby(["kecamatan_code", "kecamatan_name"], as_index=False)["case_count"]
        .sum()
        .sort_values("case_count", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(by_kec["kecamatan_name"], by_kec["case_count"], color="#4c78a8")
    ax.invert_yaxis()
    ax.set_xlabel("Cases, 2018-2023")
    ax.set_title("Leptospirosis cases by kecamatan")
    fig.tight_layout()
    fig.savefig(FIGURES / "cases_by_kecamatan_code.png", dpi=180)
    plt.close(fig)

    incidence = (
        kec_panel.groupby(["kecamatan_code", "kecamatan_name"], as_index=False)
        .agg(case_count=("case_count", "sum"), population_field_value=("population_field_value", "mean"))
    )
    incidence["case_rate_per_100k_population_field"] = (
        incidence["case_count"] / incidence["population_field_value"] * 100000
    )
    incidence = incidence.sort_values("case_rate_per_100k_population_field", ascending=False)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(incidence["kecamatan_name"], incidence["case_rate_per_100k_population_field"], color="#59a14f")
    ax.invert_yaxis()
    ax.set_xlabel("Cases per 100,000 population-field units")
    ax.set_title("Normalized leptospirosis hotspot ranking")
    fig.tight_layout()
    fig.savefig(FIGURES / "cases_by_kecamatan_normalized.png", dpi=180)
    plt.close(fig)


def make_preprocessor(x: pd.DataFrame) -> ColumnTransformer:
    numeric = [col for col in x.columns if pd.api.types.is_numeric_dtype(x[col])]
    categorical = [col for col in x.columns if col not in numeric]
    return ColumnTransformer(
        [
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            (
                "cat",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=2)),
                    ]
                ),
                categorical,
            ),
        ]
    )


def run_ml(cases: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    df = cases[cases["patient_status"].isin(["Deceased", "Recovered"])].copy()
    df["target_deceased"] = (df["patient_status"] == "Deceased").astype(int)
    df = df.merge(weather[["year", "month", "humidity", "temperature_c", "rainfall_mm"]], on=["year", "month"], how="left")

    clinical = [
        "patient_age",
        "patient_gender",
        "patient_occupation",
        "patient_occu_mobility",
        "patient_occu_interaction_human",
        "patient_occu_interaction_waste",
        "patient_occu_interaction_animal",
        "patient_edu",
        "patient_marital",
        "first_symptom_day_offset",
        "hospitalised_day_offset",
        "diag_confirmed_day_offset",
    ] + [col for col in df.columns if col.startswith("symp_")]
    environmental = [
        "humidity",
        "temperature_c",
        "rainfall_mm",
    ] + [
        col
        for col in df.columns
        if col.startswith("house_env_")
        or col.startswith("activity_")
        or col.startswith("bath_")
        or col.startswith("wound_")
        or col.startswith("dirty_water_")
        or col.startswith("exposure_dirty_water_")
    ]
    animal = [
        col
        for col in df.columns
        if col.startswith("animal_present_")
        or col.startswith("exposure_animal_")
        or col.startswith("exposure_contact_")
        or col.startswith("host_contact_")
        or col == "house_env_rat_sighting"
    ]
    feature_sets = {
        "Model 1 - Clinical": clinical,
        "Model 2 - Clinical + Environmental": clinical + environmental,
        "Model 3 - Clinical + Environmental + Animal": clinical + environmental + animal,
    }
    estimators = {
        "Logistic Regression": LogisticRegression(max_iter=5000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=42, class_weight="balanced"),
        "Gradient Boosting": HistGradientBoostingClassifier(random_state=42),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rows = []
    for model_name, columns in feature_sets.items():
        columns = [col for col in dict.fromkeys(columns) if col in df.columns]
        x = df[columns].replace("", np.nan)
        y = df["target_deceased"]
        for estimator_name, estimator in estimators.items():
            pipe = Pipeline([("preprocess", make_preprocessor(x)), ("model", estimator)])
            try:
                if estimator_name == "Gradient Boosting":
                    pred = cross_val_predict(pipe, x, y, cv=cv, method="predict_proba")[:, 1]
                else:
                    pred = cross_val_predict(pipe, x, y, cv=cv, method="predict_proba")[:, 1]
                auc = roc_auc_score(y, pred)
            except Exception as exc:
                auc = np.nan
                rows.append(
                    {
                        "feature_set": model_name,
                        "algorithm": estimator_name,
                        "n_rows": len(df),
                        "n_features": len(columns),
                        "auroc": auc,
                        "note": str(exc),
                    }
                )
                continue
            rows.append(
                {
                    "feature_set": model_name,
                    "algorithm": estimator_name,
                    "n_rows": len(df),
                    "n_features": len(columns),
                    "auroc": auc,
                    "note": "placeholder target: Deceased vs Recovered; replace with is_case if controls arrive",
                }
            )
    results = pd.DataFrame(rows)
    results.to_csv(TABLES / "model_comparison_results.csv", index=False)
    return results


def write_summary(cases: pd.DataFrame, monthly: pd.DataFrame, kec_panel: pd.DataFrame, ml: pd.DataFrame) -> None:
    lekminkes_monthly = PROCESSED / "lekminkes_monthly_disease_aggregates.csv"
    lekminkes_note = "not scraped yet"
    if lekminkes_monthly.exists():
        agg = pd.read_csv(lekminkes_monthly)
        available = agg.groupby(["condition", "year"])["value"].sum().reset_index()
        lekminkes_note = f"scraped {len(agg):,} monthly rows across {available['condition'].nunique()} conditions"

    ml_preview = ml.round({"auroc": 3}).fillna("").to_csv(index=False)

    summary = f"""# Build Summary

## Data now in the build

- Patient-level leptospirosis surveillance cases: {len(cases):,} rows, 2018-2023.
- Severity ML subset: {(cases['patient_status'].isin(['Deceased', 'Recovered'])).sum():,} rows.
- Monthly ecological panel: {len(monthly):,} month rows, zero-filled from 2018-01 to 2023-12.
- Kecamatan-year panel: {len(kec_panel):,} rows across 16 kecamatan and 6 years.
- Public LEKMINKES aggregates: {lekminkes_note}.

## Current outputs

- `data/processed/monthly_ecological_panel.csv`
- `data/processed/kecamatan_year_panel.csv`
- `outputs/tables/ecological_poisson_coefficients.csv`
- `outputs/tables/model_comparison_results.csv`
- `outputs/figures/monthly_cases_vs_humidity.png`
- `outputs/figures/cases_by_kecamatan_code.png`
- `outputs/figures/cases_by_kecamatan_normalized.png`

## ML result snapshot

```csv
{ml_preview.strip()}
```

## Remaining data gaps

- The public LEKMINKES dashboard gives aggregate DBD/leptospirosis trends and puskesmas totals, not patient-level controls.
- Controls are still needed for the original case-control target. If they arrive, add a merged file with `is_case` and reuse the existing feature groups.
- Livestock density and daily BMKG weather are still optional upgrades for stronger One Health and rainfall-lag analyses.
- The population file is treated as `population_field_value`; confirm whether it is raw population, density, or another estimate before interpreting normalized incidence.
"""
    Path("build_summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    cases = load_cases()
    cases.to_csv(PROCESSED / "cases_with_kecamatan.csv", index=False)
    weather = load_weather_long()
    weather.to_csv(PROCESSED / "weather_monthly_long.csv", index=False)
    population = load_population_long()
    population.to_csv(PROCESSED / "population_long.csv", index=False)

    monthly = build_monthly_panel(cases, weather)
    ecological = fit_ecological_model(monthly)
    kec_panel = build_kecamatan_year_panel(cases, population)
    plot_outputs(monthly, kec_panel)
    ml = run_ml(cases, weather)
    write_summary(cases, monthly, kec_panel, ml)
    print("Build complete")
    print(ecological)
    print(ml)


if __name__ == "__main__":
    main()
