param(
    [string]$Config = "configs/synthetic.yaml"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Config)) {
    python -m onehealth_risk.cli demo synthetic --config $Config
} else {
    python -m onehealth_risk.cli run-all --config $Config
}
