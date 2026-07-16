# README — Leptospirosis One Health ML Project

**Project:** Development of a One Health Machine Learning Decision-Support Model for
Early Leptospirosis Risk Identification (Semarang, Indonesia)

This document is the working plan for the three build tracks, what's needed to advance
each one, and what to do whether or not the pending data requests come through.

---

## 1. Status Snapshot

| Item | Status |
|---|---|
| Leptospirosis case file (182 patients, 2018–2023) | In hand |
| Monthly weather (city-wide, 2018–2023) | In hand |
| Population estimates (by kecamatan, 2018–2023) | In hand — likely density, not raw counts (unconfirmed) |
| Febrile-illness control patients | **Pending** — outreach sent to surveillance office + Gasem et al. authors |
| Kecamatan code → name lookup table | **Pending** — needed to join case file to population/livestock data |
| Livestock population by kecamatan (multi-year) | **Pending manual download** — sandbox can't reach the portals directly |
| BMKG daily weather (longer/finer than current file) | **Pending manual download or registration** |

---

## 2. Track A — Ecological (Time-Based) Risk Model

**Goal:** Answer the secondary research question (which environmental/animal variables
matter most) using small-area or time-series methods, as a parallel track that doesn't
depend on getting patient-level controls.

**Step-by-step plan:**
1. ~~Build a full 72-month case-count panel (zero-filled), joined to monthly weather.~~ **Done.**
2. ~~Fit Poisson/negative-binomial GLM: case_count ~ rainfall + rainfall_lag1 + humidity + temp.~~ **Done.** Finding: humidity is the strongest, most robust predictor (p=0.001–0.04); rainfall was not significant at monthly resolution.
3. Resolve the kecamatan code → name mapping (see §6) so case counts can be joined to population and livestock data by district.
4. Rebuild the panel at **kecamatan × year** (or × month, if daily weather becomes available) resolution, with population as an offset (to get incidence rate, not raw counts) and livestock density as an added predictor.
5. Re-fit the nested comparison at this finer resolution: population/clinical baseline → + weather → + livestock density.
6. Sensitivity check: re-run with daily BMKG data once available, to test whether rainfall becomes significant at finer temporal resolution (monthly aggregation may be masking a real flood-pulse effect).

**Files produced so far:** `monthly_ecological_panel.csv`, `monthly_cases_vs_humidity.png`

---

## 3. Track B — Geographic Hotspot Visualization

**Goal:** Satisfy the "geographic distribution of cases" deliverable from the original proposal.

**Step-by-step plan:**
1. ~~Chart case counts by kecamatan code (unmapped).~~ **Done.**
2. Resolve kecamatan code → name mapping (§6).
3. Normalize case counts by population to get **incidence rate** per kecamatan (raw counts currently conflate disease risk with population size — code `10`'s high count may just mean it's a bigger district).
4. Layer in livestock density and rainfall by kecamatan once those datasets are joined, to visually cross-reference hotspots against environmental/animal exposure.
5. If a Semarang kecamatan boundary file (GeoJSON/shapefile) can be sourced, upgrade from a bar chart to an actual choropleth map. (Not yet located — see §6.)

**Files produced so far:** `cases_by_kecamatan_code.png`

---

## 4. Track C — ML Pipeline (Nested Model Comparison)

**Goal:** The core deliverable — Model 1 (Clinical) → Model 2 (+ Environmental) → Model 3
(+ One Health/Animal), compared via cross-validated AUROC across Logistic Regression,
Random Forest, and Gradient Boosting.

**Step-by-step plan:**
1. ~~Build the full pipeline scaffold using severity (Deceased vs. Recovered, N=90) as a placeholder target, since real controls aren't available yet.~~ **Done.**
2. ~~Run and validate: Model 1 → 0.52 AUROC, Model 2 → 0.63, Model 3 → 0.68 (Logistic Regression, 5-fold CV).~~ **Done.** Pattern matches the original hypothesis direction, though N is small and this is a placeholder outcome, not the real research question.
3. **Branches here — see §7 decision tree.**
4. Once real data is available (either controls, or a decision to permanently pivot the outcome), swap `TARGET_COL` and `build_target()` in `ml_pipeline_scaffold.py` and re-run — the rest of the pipeline (feature groups, CV, algorithms, evaluation) needs no changes.
5. Add SHAP-based feature importance once the final target is locked in (not built yet — deferred until the target is finalized, since importance rankings on a placeholder target aren't worth over-investing in).
6. Add calibration reporting (not just AUROC) once real data is in, since the eventual prototype needs to output a meaningful Low/Moderate/High probability, not just a rank-ordering.

**Files produced so far:** `ml_pipeline_scaffold.py`, `model_comparison_results.csv`

---

## 5. Outreach Tracker

| Recipient | Purpose | Status |
|---|---|---|
| Semarang surveillance office (Dinas Kesehatan) | Request febrile-illness (dengue/typhoid/etc.) control patient records, same fields/years as existing case file | Sent — awaiting reply |
| Gasem et al. (BMC Infect Dis, 2020) authors | Ask about data-sharing or access process for their Semarang febrile-illness cohort | Sent — awaiting reply |

---

## 6. Data Source Links (all found so far)

### Leptospirosis surveillance (aggregate case counts)
- data.go.id — Leptospirosis case data 2023: https://data.go.id/dataset/dataset/data-surveilans-penyakit-leptospirosis-tahun-2023
- data.go.id — Leptospirosis case data 2022: https://data.go.id/dataset/dataset/data-surveilans-penyakit-leptospirosis-tahun-2022
- Jakarta Satu Data portal (source for the above): https://satudata.jakarta.go.id/open-data/detail/data-surveilans-penyakit-leptospirosis-tahun-2022
- WHO Indonesia — Leptospirosis prevention and control overview: https://www.who.int/indonesia/news/detail/24-08-2020-leptospirosis-prevention-and-control-in-indonesia

### Dengue/febrile-illness surveillance (potential control source, aggregate only)
- data.go.id — Dengue (DBD) case data: https://data.go.id/dataset/dataset/2d7-sdjt-data-kasus-demam-berdarah
- Portal Data Jawa Tengah — DBD cases 2024: https://data.jatengprov.go.id/dataset/kasus-demam-berdarah-dengue-dbd-tahun-2024
- data.go.id — DBD incidence rate per 100,000 population: https://data.go.id/dataset/dataset/data-kasus-demam-berdarah-dengue-incidence-rate-per-100-000-penduduk
- Satu Data Indonesia catalog, filtered to DBD (many regions/years): https://katalog.data.go.id/dataset/?tags=DBD

### Published cohort/case-control studies (precedent — contact authors for data-sharing, not open raw data)
- Gasem et al. 2020, BMC Infectious Diseases — Semarang febrile cohort (leptospirosis vs. dengue/typhoid/other): https://doi.org/10.1186/s12879-020-4903-5 (full text: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7045408/)
- Lestari et al. 2025, African Journal of Infectious Diseases — Kebumen case-control study (53 cases/53 controls, CC-BY licensed): https://www.journals.athmsi.org/index.php/AJID/article/view/6211 (full text: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12102677/)
- PLOS NTD / medRxiv — Jakarta flood-outbreak leptospirosis surveillance analysis (2019–2020): https://journals.plos.org/plosntds/article?id=10.1371%2Fjournal.pntd.0014243 (preprint: https://www.medrxiv.org/content/10.1101/2025.10.14.25338029v1.full)

### Animal/livestock population data (open, multi-year)
- BPS Jawa Tengah — Livestock population by regency/kabupaten and species: https://jateng.bps.go.id/en/statistics-table/2/NzUjMg==/populasi-ternak-menurut-kabupaten-kota-dan-jenis-ternak-di-provinsi-jawa-tengah-ekor-.html
- BPS national — Livestock population by province and species: https://www.bps.go.id/en/statistics-table/3/UzJWaVUxZHdWVGxwU1hSd1UxTXZlbmRITjA1Q2R6MDkjMw==/populasi-ternak-menurut-provinsi-dan-jenis-ternak--ekor---2024.html
- Portal Data Jawa Tengah — kecamatan-level livestock population datasets (multiple regencies/years): http://data.jatengprov.go.id/dataset?tags=populasi%20ternak

### Weather data (requires free registration for full historical daily records)
- BMKG Data Online (historical daily rainfall/temp/humidity by station): https://dataonline.bmkg.go.id/
- BMKG Central Java Climatology Station (regional bulletins/analysis): https://staklim-jateng.bmkg.go.id/
- BMKG Open Data (forecast/nowcast only, not historical): https://data.bmkg.go.id/

### Kecamatan code lookup (unresolved blocker — leads found, not yet verified as complete)
- kodewilayah.id — appears to have the full Kota Semarang (33.74) code table, but blocks automated fetching (robots.txt): https://kodewilayah.id/33.74 — **open manually and copy the table**
- nomor.net — confirms individual codes one at a time, e.g. 33.74.13 = Semarang Barat, 33.74.07 = Semarang Selatan: https://www.nomor.net/_kodepos.php?_i=kecamatan-kodepos&sby=000000&daerah=Kota&jobs=Semarang
- Wikipedia (Indonesian) — full list of Semarang's 16 kecamatan and 177 kelurahan (no numeric codes, names only — useful for cross-checking): https://id.wikipedia.org/wiki/Daftar_kecamatan_dan_kelurahan_di_Kota_Semarang
- Official source of truth: Permendagri (Ministry of Home Affairs regulation) on administrative area codes — search for the latest "Permendagri Kode dan Data Wilayah Administrasi Pemerintahan" if the above sources disagree

---

## 7. Decision Tree — What to Do Next

### IF the surveillance office or Gasem et al. authors provide real febrile-illness control data:

1. Confirm the control data has the **same fields** as the existing case file (clinical, environmental, animal-exposure variables) — if fields don't match, Models 2 and 3 can't be built on it, only Model 1.
2. Merge cases + controls into a single file with a binary `is_case` column.
3. In `ml_pipeline_scaffold.py`: set `TARGET_COL = "is_case"`, replace `build_target()` to return the merged case+control dataframe (no more Deceased/Recovered filtering).
4. Re-run the script as-is — feature groups, CV setup, and algorithms don't need to change.
5. Add SHAP feature importance now that the real target is locked in (this is when the "which variables matter most" secondary question gets a real, publishable answer).
6. Revisit sample size: if controls bring N well above ~200–300, consider adding a held-out test set in addition to CV, since a true train/test split becomes more meaningful at that size.
7. Update the paper's Methods/Results sections to reflect the real case-control design instead of the placeholder severity framing.

### IF no real control data arrives (or it arrives but lacks the needed fields):

1. **Formally pivot Track C's primary outcome to severity/mortality** (Deceased vs. Recovered) as the paper's actual research question, not just a placeholder. This was already flagged as the most defensible fallback (see earlier discussion).
2. Rewrite the Introduction/Hypotheses around prognosis ("which factors predict a fatal outcome among diagnosed cases") rather than exposure-risk ("who gets leptospirosis").
3. Keep the One Health framing, but reframe the animal/environmental variables as prognostic factors rather than risk-of-infection factors — note in Discussion that this is a meaningful but different clinical question than originally proposed.
4. Lean more heavily on Tracks A and B (ecological model + hotspot visualization) as the paper's population-level risk evidence, since those don't require patient-level controls and already show a real, defensible finding (humidity effect).
5. Cite the Gasem et al. and Kebumen studies as supporting literature/precedent for the exposure-risk question, explicitly noting in Limitations that a prospective case-control study is the natural next step this project sets up, rather than something it was able to complete itself.
6. Consider a smaller-scope pivot: since the Kebumen study design (nearest-neighbor community controls) required no special data-sharing agreement, a future data collection round modeled on that approach could be proposed as a follow-up study rather than retrofitted into this one.

---

## 8. File Manifest (produced so far)

| File | Track | Description |
|---|---|---|
| `monthly_ecological_panel.csv` | A | 72-month case/weather panel |
| `monthly_cases_vs_humidity.png` | A | Time series chart |
| `cases_by_kecamatan_code.png` | B | Case distribution by (unmapped) kecamatan code |
| `ml_pipeline_scaffold.py` | C | Full nested model comparison pipeline |
| `model_comparison_results.csv` | C | AUROC results, 3 models × 3 algorithms |
| `build_summary.md` | A/B/C | Narrative summary of first-pass results |
| `README.md` | — | This file |
