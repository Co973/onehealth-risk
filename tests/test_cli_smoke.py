from __future__ import annotations

import pytest

from onehealth_risk.config import load_config
from onehealth_risk.data import validate_config
from onehealth_risk.demo import synthetic_config, write_synthetic_demo
from onehealth_risk.features import prepare_training_frame
from onehealth_risk.security import audit_local, deidentify_csv
from onehealth_risk.workflow import run_all


def test_semarang_config_validates() -> None:
    result = validate_config(load_config("configs/semarang.yaml"))
    assert result.ok
    assert result.row_count > 0


def test_nested_feature_sets_are_available() -> None:
    config = load_config("configs/semarang.yaml")
    df, y, sets = prepare_training_frame(config)
    assert len(df) == len(y)
    assert sets["clinical"]
    assert len(sets["clinical_environmental_animal"]) >= len(sets["clinical"])


def test_synthetic_demo_generation_and_validation(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = write_synthetic_demo("configs/synthetic.yaml", n_rows=80)
    config = load_config(config_path)
    result = validate_config(config)
    assert result.ok
    assert result.row_count == 80
    assert audit_local(config)["ok"]


def test_run_all_synthetic_creates_expected_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = write_synthetic_demo("configs/synthetic.yaml", n_rows=120)
    artifacts = run_all(load_config(config_path))
    assert artifacts["predictions"].exists()
    assert artifacts["model_dir"].joinpath("manifest.json").exists()
    assert artifacts["reproducibility_report"].exists()
    assert artifacts["security_audit_json"].exists()


def test_unsafe_external_output_path_is_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = synthetic_config()
    config["_project_root"] = str(tmp_path)
    config["paths"]["reports"] = str(tmp_path.parent / "outside_reports")
    with pytest.raises(ValueError):
        audit = audit_local(config)
        if not audit["ok"]:
            raise ValueError(audit["errors"][0])


def test_deidentify_hashes_configured_identifier(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = write_synthetic_demo("configs/synthetic.yaml", n_rows=20)
    config = load_config(config_path)
    out = deidentify_csv(
        config,
        "data/demo/synthetic_cases.csv",
        "data/processed/synthetic/synthetic_deidentified.csv",
    )
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "SYN-0001" not in text
