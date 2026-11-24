# Healthcare Data Dictionary & Attribute Catalog
## Hospital Patient Analytics & Healthcare Performance Optimization

### 1. Table Manifest

| Table Name | Entity Grain | Primary Key | Total Records | Classification |
|:---|:---|:---|---:|:---|
| `dim_patient` | 1 row per unique patient | `patient_key` | 1,200 | Dimension (Demographics, Segmentation) |
| `dim_date` | 1 row per calendar day | `date_key` | 2,192 | Dimension (Calendar Hierarchy) |
| `dim_encounter_type` | 1 row per care setting modality | `encounter_class` | 6 | Dimension (Clinical Setting Catalog) |
| `dim_organization` | 1 row per hospital / facility | `org_id` | 6 | Dimension (Healthcare Facilities) |
| `dim_provider` | 1 row per healthcare practitioner | `provider_id` | 48 | Dimension (Clinical Personnel & Specialty) |
| `dim_condition` | 1 row per clinical diagnosis code | `condition_code` | 12 | Dimension (Diagnosis Catalog & Chronic Flags) |
| `fact_encounters` | 1 row per completed clinical encounter | `encounter_id` | 5,960 | Fact (Atomic Operational & Financial Transaction) |
| `fact_encounter_conditions`| 1 row per condition diagnosed during visit | `id` | 4,501 | Bridge Fact (Encounter-to-Diagnosis Many-to-Many) |
| `fact_encounter_procedures`| 1 row per surgical/diagnostic procedure | `procedure_id` | 2,970 | Bridge Fact (Encounter-to-Procedure Many-to-Many) |

---

### 2. Dimension Table Definitions

#### Table: `dim_patient`
| Column Name | Data Type | Nullable | Description / Business Derivation Rules |
|:---|:---|:---:|:---|
| `patient_key` | VARCHAR(64) | NO | De-identified surrogate primary key. Derived as SHA-256 salted hash of source ID prefixed with `PT_`. |
| `birthdate` | DATE | NO | Patient date of birth (ISO 8601 `YYYY-MM-DD`). |
| `deathdate` | DATE | YES | Patient date of death. Null indicates patient is alive at study cutoff. |
| `is_deceased` | INTEGER | NO | Binary flag: `1` if `deathdate` is populated, otherwise `0`. |
| `gender` | VARCHAR(10) | NO | Standardized administrative gender: `'M'` (Male), `'F'` (Female), `'U'` (Unknown). |
| `race` | VARCHAR(50) | NO | Self-reported racial classification: `'white'`, `'black'`, `'asian'`, `'other'`, `'unknown'`. |
| `ethnicity` | VARCHAR(50) | NO | Self-reported ethnic origin: `'nonhispanic'`, `'hispanic'`, `'unknown'`. |
| `marital` | VARCHAR(10) | YES | Marital status: `'M'` (Married), `'S'` (Single), `'D'` (Divorced), `'U'` (Unknown). |
| `city` | VARCHAR(100) | NO | City of residence within Massachusetts simulation (e.g., Boston, Cambridge). |
| `state` | VARCHAR(50) | NO | State code (`'MA'`). |
| `zip` | VARCHAR(20) | NO | 5-digit postal zip code. |
| `annual_income` | NUMERIC(12, 2)| YES | Synthesized annual household income in USD. |
| `current_age` | NUMERIC(5, 1) | NO | Patient age as of 2024-12-31: `(2024-12-31 - birthdate) / 365.25`. |
| `current_age_group`| VARCHAR(50)| NO | Standardized demographic age tier (Pediatric, Young Adult, Adult, Middle-Aged, Older Adult, Senior). |
| `cluster_id` | INTEGER | YES | K-Means cluster assignment (0, 1, 2, 3). |
| `cluster_name` | VARCHAR(100)| YES | Clinical archetype label (e.g., "High-Cost Complex Inpatients", "Frequent Emergency Utilizers"). |
| `utilization_tier` | VARCHAR(50) | NO | Encounter frequency category (Single, Occasional, Frequent, High Utilizer). |
| `total_lifetime_encounters` | INTEGER | NO | Cumulative count of all recorded encounters for patient. |
| `total_lifetime_claim_cost` | NUMERIC(14, 2) | NO | Cumulative sum of gross billed charges across patient history. |

#### Table: `dim_date`
| Column Name | Data Type | Nullable | Description / Business Derivation Rules |
|:---|:---|:---:|:---|
| `date_key` | INTEGER | NO | Smart primary key in integer format `YYYYMMDD` (e.g., `20230514`). |
| `full_date` | DATE | NO | Standard calendar date (`YYYY-MM-DD`). |
| `year` | INTEGER | NO | 4-digit calendar year (2020 – 2025). |
| `quarter` | VARCHAR(10) | NO | Year and Quarter string (e.g., `'2023-Q2'`). |
| `quarter_number` | INTEGER | NO | Quarter index (1, 2, 3, 4). |
| `year_month` | VARCHAR(10) | NO | Year and Month string (e.g., `'2023-05'`). |
| `month_number` | INTEGER | NO | Month index (1 to 12). |
| `month_name` | VARCHAR(20) | NO | Full month name (e.g., `'May'`). |
| `day_of_month` | INTEGER | NO | Calendar day of month (1 to 31). |
| `day_of_week` | INTEGER | NO | Weekday index (0 = Monday, 6 = Sunday). |
| `day_name` | VARCHAR(20) | NO | Full day of week (e.g., `'Monday'`). |
| `is_weekend` | INTEGER | NO | Binary flag: `1` for Saturday/Sunday, `0` for Monday–Friday. |

#### Table: `dim_encounter_type`
| Column Name | Data Type | Nullable | Description / Business Derivation Rules |
|:---|:---|:---:|:---|
| `encounter_class` | VARCHAR(50) | NO | Standardized setting identifier (`ambulatory`, `wellness`, `outpatient`, `urgentcare`, `emergency`, `inpatient`). |
| `display_name` | VARCHAR(100)| NO | Executive label for dashboards and reports (e.g., "Emergency Department"). |
| `setting_description` | VARCHAR(255) | NO | Clinical setting definition and scope of care. |
| `acuity_level` | VARCHAR(50) | NO | Acuity classification (`Low`, `Moderate`, `High`, `Critical`). |

---

### 3. Fact Table Definitions

#### Table: `fact_encounters`
| Column Name | Data Type | Nullable | Description / Business Derivation Rules |
|:---|:---|:---:|:---|
| `encounter_id` | VARCHAR(64) | NO | Unique surrogate identifier for encounter event (UUID). |
| `patient_key` | VARCHAR(64) | NO | Foreign key referencing `dim_patient.patient_key`. |
| `date_key` | INTEGER | NO | Foreign key referencing `dim_date.date_key` (based on encounter start date). |
| `org_id` | VARCHAR(64) | NO | Foreign key referencing `dim_organization.org_id`. |
| `provider_id` | VARCHAR(64) | NO | Foreign key referencing `dim_provider.provider_id`. |
| `encounter_class`| VARCHAR(50) | NO | Foreign key referencing `dim_encounter_type.encounter_class`. |
| `payer` | VARCHAR(100)| NO | Primary health insurance payer (Medicare, Medicaid, Commercial, Self-Pay). |
| `start_time` | TIMESTAMP | NO | Date and time of clinical admission/intake. |
| `stop_time` | TIMESTAMP | NO | Date and time of discharge/departure. Validated: `stop_time >= start_time`. |
| `start_hour` | INTEGER | NO | Hour of day of intake (0 to 23). |
| `duration_minutes` | NUMERIC(8, 1)| NO | Encounter duration in minutes: `(stop_time - start_time) / 60`. Minimum 15.0 min. |
| `duration_hours` | NUMERIC(8, 2)| NO | Encounter duration in hours: `duration_minutes / 60`. |
| `length_of_stay_days` | NUMERIC(6, 2)| NO | Inpatient length of stay in fractional days: `(stop_time - start_time) / 86400`. |
| `age_at_encounter` | NUMERIC(5, 1)| NO | Exact patient age at admission: `(start_time - birthdate) / 365.25`. |
| `age_group` | VARCHAR(50) | NO | Standardized demographic age tier at encounter. |
| `base_encounter_cost` | NUMERIC(12, 2)| NO | Base facility/professional service fee before ancillary charges. |
| `total_claim_cost` | NUMERIC(12, 2)| NO | Gross billed charges submitted to healthcare payer. Validated: `total_claim_cost >= base_encounter_cost`. |
| `payer_coverage` | NUMERIC(12, 2)| NO | Amount reimbursed by insurance payer. |
| `patient_payment` | NUMERIC(12, 2)| NO | Patient out-of-pocket obligation: `max(0.00, total_claim_cost - payer_coverage)`. |
| `coverage_ratio` | NUMERIC(5, 4)| NO | Payer reimbursement ratio: `payer_coverage / total_claim_cost`. |
| `is_inpatient` | INTEGER | NO | Binary flag: `1` if `encounter_class == 'inpatient'`, else `0`. |
| `is_emergency` | INTEGER | NO | Binary flag: `1` if `encounter_class == 'emergency'`, else `0`. |
| `visit_sequence_number` | INTEGER | NO | Sequential visit index per patient (1st visit = 1, 2nd visit = 2, etc.). |
| `re_encounter_30d` | INTEGER | NO | Binary indicator: `1` if patient experienced any subsequent encounter within 1 to 30 days post-discharge. |
