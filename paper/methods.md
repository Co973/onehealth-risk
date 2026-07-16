# Methods

One Health Risk uses a site YAML configuration to locate local data, define required columns, declare target labels, describe nested feature groups, and set security controls. The workflow validates the case table, derives date and geography fields, joins monthly weather features, constructs nested clinical, environmental, animal, and geography feature sets, and fits logistic-regression baseline models with preprocessing for numeric and categorical variables.

The `run-all` command executes validation, local path audit, model training, cross-validated evaluation, model-card generation, feature availability export, security-control summary, prediction export, and reproducibility reporting. All outputs are written under project-local `models/` and `outputs/` paths by default.

The public demo uses synthetic patient-like rows, synthetic weather, synthetic population, and synthetic geography lookup tables. The synthetic data are designed to exercise the software workflow and do not represent real patients.
