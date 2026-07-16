from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd


BASE_URL = "https://lekminkes.dinkes.semarangkota.go.id"
YEARS = range(2019, 2027)
MONTHLY_VARIABLES = {
    "DBD": "dengue_dbd",
    "Leptospirosis": "leptospirosis",
    "kasus_malaria": "malaria",
    "kasus_tb_baru": "tb_new_cases",
}
WEEKLY_VARIABLES = {
    "dbd_mingguan": "dengue_dbd_weekly",
}
OUT = Path("data/processed")


def fetch_text(path: str, params: dict[str, str | int] | None = None) -> str:
    query = f"?{urlencode(params)}" if params else ""
    with urlopen(f"{BASE_URL}{path}{query}", timeout=30) as response:
        return response.read().decode("utf-8")


def fetch_json(path: str, params: dict[str, str | int] | None = None) -> dict:
    return json.loads(fetch_text(path, params))


def scrape_line(variable: str, clean_name: str, years: range, weekly: bool = False) -> pd.DataFrame:
    rows = []
    for year in years:
        payload = fetch_json(f"/graph/line/{variable}", {"tahun": year})
        if not payload.get("status"):
            continue

        categories = payload.get("mingguan") if weekly else list(range(1, 13))
        for series in payload["data"]:
            for i, value in enumerate(series["data"]):
                rows.append(
                    {
                        "source_variable": variable,
                        "condition": clean_name,
                        "year": year,
                        "period_type": "week" if weekly else "month",
                        "period": int(categories[i]) if i < len(categories) else i + 1,
                        "measure": series["name"],
                        "value": value,
                        "title": payload.get("title", ""),
                        "subtitle": payload.get("subtitle", ""),
                    }
                )
    return pd.DataFrame(rows)


def scrape_puskesmas(variable: str, clean_name: str, years: range) -> pd.DataFrame:
    rows = []
    pattern = re.compile(r"var dat = (\[.*?\]);", re.S)
    for year in years:
        html = fetch_text(f"/ajax/bar2/{variable}", {"tahun": year, "tingkat": "puskesmas"})
        match = pattern.search(html)
        if not match:
            continue
        for record in json.loads(match.group(1)):
            rows.append(
                {
                    "source_variable": variable,
                    "condition": clean_name,
                    "year": year,
                    "puskesmas": record["name"],
                    "female_cases": record["data"],
                    "male_cases": record["datal"],
                    "male_deaths": record["dataml"],
                    "female_deaths": record["datamp"],
                    "total_cases": record["data"] + record["datal"],
                    "total_deaths": record["dataml"] + record["datamp"],
                }
            )
    return pd.DataFrame(rows)


def scrape_map(variable: str, clean_name: str, years: range) -> pd.DataFrame:
    rows = []
    for year in years:
        payload = fetch_json(f"/graph/map/{variable}", {"tahun": year, "tingkat": "puskesmas"})
        if not payload.get("status"):
            continue
        for code, value in payload["data"]:
            rows.append(
                {
                    "source_variable": variable,
                    "condition": clean_name,
                    "year": year,
                    "puskesmas_code": code,
                    "value": value,
                    "geojson": payload.get("geojson", ""),
                    "title": payload.get("title", ""),
                    "subtitle": payload.get("subtitle", ""),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    monthly_frames = [
        scrape_line(variable, clean_name, YEARS)
        for variable, clean_name in MONTHLY_VARIABLES.items()
    ]
    pd.concat(monthly_frames, ignore_index=True).to_csv(
        OUT / "lekminkes_monthly_disease_aggregates.csv", index=False
    )

    weekly_frames = [
        scrape_line(variable, clean_name, YEARS, weekly=True)
        for variable, clean_name in WEEKLY_VARIABLES.items()
    ]
    pd.concat(weekly_frames, ignore_index=True).to_csv(
        OUT / "lekminkes_weekly_disease_aggregates.csv", index=False
    )

    puskesmas_frames = [
        scrape_puskesmas(variable, clean_name, YEARS)
        for variable, clean_name in {"DBD": "dengue_dbd", "Leptospirosis": "leptospirosis"}.items()
    ]
    pd.concat(puskesmas_frames, ignore_index=True).to_csv(
        OUT / "lekminkes_puskesmas_disease_totals.csv", index=False
    )

    map_frames = [
        scrape_map(variable, clean_name, YEARS)
        for variable, clean_name in {"DBD": "dengue_dbd", "Leptospirosis": "leptospirosis"}.items()
    ]
    pd.concat(map_frames, ignore_index=True).to_csv(
        OUT / "lekminkes_puskesmas_map_values.csv", index=False
    )


if __name__ == "__main__":
    main()
