# Final Build README

## What Has Been Achieved

- Refactored the project into a local Python package named `onehealth_risk`.
- Added a CLI matching the planned workflow:
  - `validate`
  - `train`
  - `train-local`
  - `evaluate`
  - `predict`
  - `demo semarang`
- Added `configs/semarang.yaml` as the first demo/site configuration.
- Preserved local-only operation: data, models, reports, and predictions stay inside the project folders.
- Implemented nested feature sets:
  - clinical
  - clinical + environmental + geography
  - clinical + environmental + animal + geography
- Implemented global model artifact saving under `models/global/`.
- Implemented `models/global/latest/` for convenient prediction and local calibration.
- Implemented local calibration under `models/local/semarang/local_calibrator.joblib`.
- Implemented evaluation reports with AUROC, sensitivity, specificity, calibration, and confusion matrix counts.
- Implemented prediction CSV export with global and optional local risk scores.
- Added a generated model card at `outputs/reports/model_card.md`.
- Added smoke tests in `tests/test_cli_smoke.py`.

## Verified Commands

These commands were run successfully:

```powershell
python -m onehealth_risk.cli validate --config configs/semarang.yaml
python -m onehealth_risk.cli train --config configs/semarang.yaml
python -m onehealth_risk.cli train-local --config configs/semarang.yaml --base-model models/global/latest
python -m onehealth_risk.cli evaluate --config configs/semarang.yaml
python -m onehealth_risk.cli predict --config configs/semarang.yaml --input data/raw/leptospirosis_surveillance_cases_semarang_2018_2023.csv --output outputs/predictions/semarang_predictions.csv --model models/global/latest
python -m onehealth_risk.cli predict --config configs/semarang.yaml --input data/raw/leptospirosis_surveillance_cases_semarang_2018_2023.csv --output outputs/predictions/semarang_predictions_local.csv --model models/global/latest --local-calibrator models/local/semarang/local_calibrator.joblib
python -m onehealth_risk.cli demo semarang
```

Direct API smoke verification also passed:

- Config validation: true
- Raw Semarang rows: 182
- Training subset rows: 90
- Usable feature counts: clinical 35, clinical/environmental 76, full nested set 98

`pytest` could not be run because it is not installed in this Python environment.

## Current Model Snapshot

Latest evaluation results in `outputs/reports/model_comparison.csv`:

| Feature set | Rows | Features | AUROC | Sensitivity | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: |
| clinical | 90 | 35 | 0.720 | 0.694 | 0.667 |
| clinical_environmental | 90 | 76 | 0.659 | 0.639 | 0.574 |
| clinical_environmental_animal | 90 | 98 | 0.659 | 0.583 | 0.611 |

## What Can Be Improved

- Add patient-level febrile illness controls so the target can become true case/control risk rather than severity among leptospirosis cases.
- Add daily BMKG weather and lag features for stronger rainfall/exposure modelling.
- Add livestock density or animal reservoir data by kecamatan/year.
- Add richer test coverage once `pytest` is installed.
- Add Streamlit or FastAPI later as a thin UI/API layer over the same package.
- Add clearer model selection logic if multiple algorithms are introduced beyond the current logistic baseline.

## Constraints And Limitations

- The present Semarang target is `Deceased` vs `Recovered`, not leptospirosis vs non-leptospirosis.
- The available training subset is small: 90 labelled severity rows.
- Current outputs are research/demo artifacts and should not be used as standalone clinical decision support.
- Local security, consent, de-identification, and governance remain the user's responsibility.
- The public LEKMINKES aggregate data is useful context but does not replace patient-level controls.
