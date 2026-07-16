# Security and Privacy

## Threat Model

The main risk is unintended disclosure of sensitive patient or site data through uploads, unsafe output paths, shared artifacts, direct identifiers, or free-text fields. The software does not defend against a fully compromised machine, malicious local user, insecure institutional storage, or inappropriate governance decisions.

## Mitigations

- Core workflows require no network access.
- Data processing is local by default.
- Generated artifacts are checked against the project root by default.
- The audit command reports path status and identifier-column warnings.
- The de-identification command can drop or hash configured identifier columns.
- Synthetic demo data supports public reproducibility without sharing private records.
- Model cards and reports include governance and limitation language.

## Reviewer-Facing Position

This project provides security-aware workflow controls, not formal compliance certification. Hospitals and researchers remain responsible for consent, access permissions, encryption at rest, institutional approvals, data retention, and secure deployment environments.
