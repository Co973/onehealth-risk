# One Health Risk

Local-first, security-aware, reproducible One Health surveillance ML toolkit.

This project is a research software artifact, not a clinically validated leptospirosis predictor. It helps hospitals and research teams run validation, feature assembly, baseline modelling, local calibration, reporting, and prediction export on their own machine when data are sensitive or cannot be shared.

## Public Demo

The reviewer-safe path uses synthetic data only:

```powershell
python -m pip install -e .
python -m onehealth_risk.cli demo synthetic
```

That command writes `configs/synthetic.yaml`, synthetic CSVs under `data/demo/`, models under `models/`, and reports/predictions under `outputs/`.

For an already generated synthetic config:

```powershell
python -m onehealth_risk.cli run-all --config configs/synthetic.yaml
python -m onehealth_risk.cli audit-local --config configs/synthetic.yaml
python -m onehealth_risk.cli report --config configs/synthetic.yaml
```

Windows users can also run:

```powershell
.\scripts\run_all.ps1
```

## CLI

```powershell
python -m onehealth_risk.cli validate --config configs/synthetic.yaml
python -m onehealth_risk.cli train --config configs/synthetic.yaml
python -m onehealth_risk.cli evaluate --config configs/synthetic.yaml
python -m onehealth_risk.cli predict --config configs/synthetic.yaml --input data/demo/synthetic_cases.csv --output outputs/predictions/demo_predictions.csv --model models/global/latest
python -m onehealth_risk.cli deidentify --config configs/synthetic.yaml --input data/demo/synthetic_cases.csv --output data/processed/synthetic/synthetic_deidentified.csv
```

Existing Semarang commands still work with `configs/semarang.yaml`, but that config is a local/private case-study validation path. Do not publish patient-level Semarang data unless local approvals explicitly permit it.

## Outputs

- `outputs/reports/reproducibility_report.md`
- `outputs/reports/security_audit.json`
- `outputs/reports/security_audit.md`
- `outputs/reports/feature_availability.csv`
- `outputs/reports/model_comparison.csv`
- `outputs/reports/model_card.md`
- `outputs/reports/security_controls.csv`
- `outputs/predictions/demo_predictions.csv`

## Security Posture

Core workflows require no network access. Generated data, reports, models, and predictions are checked so output paths stay under the project root by default. The audit command warns about configured identifier columns and common direct-identifier column names such as names, addresses, phone numbers, email addresses, national IDs, notes, and free text.

These controls reduce accidental disclosure risk; they are not a compliance certification. Users remain responsible for consent, institutional approvals, storage encryption, local access control, de-identification decisions, and secure deployment environments.

## Package Layout

- `onehealth_risk.data`: CSV/Excel loading and schema validation.
- `onehealth_risk.demo`: synthetic reviewer-safe demo data generation.
- `onehealth_risk.features`: nested clinical, environmental, animal, and geography feature sets.
- `onehealth_risk.models`: global baseline model training and local calibration.
- `onehealth_risk.security`: local path audits, identifier warnings, and de-identification.
- `onehealth_risk.workflow`: one-command reproducibility pipeline.
- `onehealth_risk.reports`: model-card and reporting helpers.
