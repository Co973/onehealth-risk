# Data Dictionary Template

Use this template for site configs and local governance review. Mark each column as required, optional, direct identifier, quasi-identifier, free text, target, or derived.

| Column | Category | Required | Type | Description | Identifier Handling |
| --- | --- | --- | --- | --- | --- |
| patient_id | identifier | yes | string | Local row or encounter identifier. | Hash or drop before sharing. |
| registered_date | clinical | yes | month/year or date | Case registration date. | Keep local. |
| patient_age | clinical | yes | numeric | Age at presentation. | Consider age binning for public sharing. |
| patient_gender | clinical | yes | categorical | Recorded gender/sex field used by the site. | Review local disclosure risk. |
| patient_loc_kelurahan_code | geography | yes | string | Local administrative geography code. | Review site-identification risk. |
| patient_status | target | yes | categorical | Modelling target for local validation. | Do not imply clinical validity. |
| symp_* | clinical | optional | binary/categorical | Symptom indicators. | Keep local. |
| humidity | environmental | optional | numeric | Monthly humidity. | Usually public/non-sensitive. |
| temperature_c | environmental | optional | numeric | Monthly temperature. | Usually public/non-sensitive. |
| rainfall_mm | environmental | optional | numeric | Monthly rainfall. | Usually public/non-sensitive. |
| animal_present_* | animal | optional | binary/categorical | Animal/reservoir exposure indicators. | Review household disclosure risk. |
| free_text_notes | free text | no | text | Narrative notes. | Drop before modelling or sharing unless approved. |
