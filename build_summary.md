# Build Summary

## Data now in the build

- Patient-level leptospirosis surveillance cases: 182 rows, 2018-2023.
- Severity ML subset: 90 rows.
- Monthly ecological panel: 72 month rows, zero-filled from 2018-01 to 2023-12.
- Kecamatan-year panel: 96 rows across 16 kecamatan and 6 years.
- Public LEKMINKES aggregates: scraped 936 monthly rows across 4 conditions.

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
feature_set,algorithm,n_rows,n_features,auroc,note
Model 1 - Clinical,Logistic Regression,90,35,0.72,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
Model 1 - Clinical,Random Forest,90,35,0.801,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
Model 1 - Clinical,Gradient Boosting,90,35,0.785,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
Model 2 - Clinical + Environmental,Logistic Regression,90,78,0.678,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
Model 2 - Clinical + Environmental,Random Forest,90,78,0.797,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
Model 2 - Clinical + Environmental,Gradient Boosting,90,78,0.767,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
Model 3 - Clinical + Environmental + Animal,Logistic Regression,90,100,0.667,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
Model 3 - Clinical + Environmental + Animal,Random Forest,90,100,0.798,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
Model 3 - Clinical + Environmental + Animal,Gradient Boosting,90,100,0.775,placeholder target: Deceased vs Recovered; replace with is_case if controls arrive
```

## Remaining data gaps

- The public LEKMINKES dashboard gives aggregate DBD/leptospirosis trends and puskesmas totals, not patient-level controls.
- Controls are still needed for the original case-control target. If they arrive, add a merged file with `is_case` and reuse the existing feature groups.
- Livestock density and daily BMKG weather are still optional upgrades for stronger One Health and rainfall-lag analyses.
- The population file is treated as `population_field_value`; confirm whether it is raw population, density, or another estimate before interpreting normalized incidence.
