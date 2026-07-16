from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config, project_path
from .data import load_cases, load_population_long, load_weather_long, validate_config
from .demo import write_synthetic_demo
from .evaluate import evaluate_config
from .models import train_global, train_local
from .predict import predict_csv
from .reports import LOCAL_WARNING, write_model_card
from .security import audit_local, deidentify_csv, write_audit_report
from .workflow import run_all, write_feature_availability, write_local_workflow_summary


def cmd_validate(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    result = validate_config(config)
    print(json.dumps(result.__dict__, indent=2))
    print(LOCAL_WARNING)
    if not result.ok:
        raise SystemExit(1)


def cmd_train(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    path = train_global(config)
    print(f"Saved global models to {path}")
    print(LOCAL_WARNING)


def cmd_train_local(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    path = train_local(config, args.base_model)
    print(f"Saved local calibration layer to {path}")
    print(LOCAL_WARNING)


def cmd_evaluate(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    report = evaluate_config(config)
    card = write_model_card(config, report)
    print(f"Wrote evaluation report to {report}")
    print(f"Wrote model card to {card}")
    print(LOCAL_WARNING)


def cmd_predict(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    out = predict_csv(config, args.input, args.output, args.model, args.local_calibrator)
    print(f"Wrote predictions to {out}")
    print(LOCAL_WARNING)


def cmd_demo(args: argparse.Namespace) -> None:
    if args.name == "synthetic":
        config_path = write_synthetic_demo(args.config, args.rows)
        config = load_config(config_path)
        artifacts = run_all(config)
        print("Synthetic demo complete")
        for name, path in artifacts.items():
            print(f"{name}: {path}")
        print(LOCAL_WARNING)
        return
    if args.name != "semarang":
        raise SystemExit(f"Unknown demo: {args.name}")
    config = load_config("configs/semarang.yaml")
    processed = project_path(config, "paths.processed", "data/processed")
    processed.mkdir(parents=True, exist_ok=True)
    load_cases(config).to_csv(processed / "cases_with_kecamatan.csv", index=False)
    load_weather_long(config).to_csv(processed / "weather_monthly_long.csv", index=False)
    load_population_long(config).to_csv(processed / "population_long.csv", index=False)
    model_dir = train_global(config)
    report = evaluate_config(config)
    card = write_model_card(config, report)
    print(f"Demo complete for Semarang")
    print(f"Models: {model_dir}")
    print(f"Evaluation: {report}")
    print(f"Model card: {card}")
    print(LOCAL_WARNING)


def cmd_audit_local(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    audit = audit_local(config)
    json_path, md_path = write_audit_report(config, audit)
    print(json.dumps(audit, indent=2))
    print(f"Wrote security audit JSON to {json_path}")
    print(f"Wrote security audit report to {md_path}")
    print(LOCAL_WARNING)
    if not audit["ok"]:
        raise SystemExit(1)


def cmd_deidentify(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    out = deidentify_csv(config, args.input, args.output)
    print(f"Wrote de-identified CSV to {out}")
    print(LOCAL_WARNING)


def cmd_report(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    comparison = evaluate_config(config)
    card = write_model_card(config, comparison)
    features = write_feature_availability(config)
    audit = audit_local(config)
    audit_json, audit_md = write_audit_report(config, audit)
    controls = write_local_workflow_summary(config, audit)
    print(f"Wrote model comparison to {comparison}")
    print(f"Wrote model card to {card}")
    print(f"Wrote feature availability table to {features}")
    print(f"Wrote security audit JSON to {audit_json}")
    print(f"Wrote security audit report to {audit_md}")
    print(f"Wrote security controls table to {controls}")
    print(LOCAL_WARNING)


def cmd_run_all(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    artifacts = run_all(config)
    print("Run-all complete")
    for name, path in artifacts.items():
        print(f"{name}: {path}")
    print(LOCAL_WARNING)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onehealth-risk")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--config", required=True)
    validate.set_defaults(func=cmd_validate)

    train = sub.add_parser("train")
    train.add_argument("--config", required=True)
    train.set_defaults(func=cmd_train)

    train_local_parser = sub.add_parser("train-local")
    train_local_parser.add_argument("--config", required=True)
    train_local_parser.add_argument("--base-model", required=True)
    train_local_parser.set_defaults(func=cmd_train_local)

    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--config", required=True)
    evaluate.set_defaults(func=cmd_evaluate)

    report = sub.add_parser("report")
    report.add_argument("--config", required=True)
    report.set_defaults(func=cmd_report)

    run_all_parser = sub.add_parser("run-all")
    run_all_parser.add_argument("--config", required=True)
    run_all_parser.set_defaults(func=cmd_run_all)

    audit = sub.add_parser("audit-local")
    audit.add_argument("--config", required=True)
    audit.set_defaults(func=cmd_audit_local)

    deidentify = sub.add_parser("deidentify")
    deidentify.add_argument("--config", required=True)
    deidentify.add_argument("--input", required=True)
    deidentify.add_argument("--output", required=True)
    deidentify.set_defaults(func=cmd_deidentify)

    predict = sub.add_parser("predict")
    predict.add_argument("--config", required=True)
    predict.add_argument("--input", required=True)
    predict.add_argument("--output", required=True)
    predict.add_argument("--model", default=str(Path("models/global/latest")))
    predict.add_argument("--local-calibrator")
    predict.set_defaults(func=cmd_predict)

    demo = sub.add_parser("demo")
    demo.add_argument("name")
    demo.add_argument("--config", default="configs/synthetic.yaml")
    demo.add_argument("--rows", type=int, default=240)
    demo.set_defaults(func=cmd_demo)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
