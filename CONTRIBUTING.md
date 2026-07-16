# Contributing

Thank you for improving One Health Risk.

## Development Setup

```powershell
python -m pip install -e . -r requirements.txt
pytest
```

## Expectations

- Keep the synthetic demo runnable without private data.
- Keep generated outputs under project-local `outputs/` and `models/` by default.
- Do not commit private patient-level records or site-identifying files.
- Avoid clinical-validity claims unless supported by an approved validation study.
- Add focused tests for CLI, reporting, security, and reproducibility changes.

## Security and Privacy

Report security concerns privately to the project maintainers. Do not open public issues containing patient data, identifiers, file paths to sensitive storage, or institutional secrets.
