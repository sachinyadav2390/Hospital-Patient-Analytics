# Hospital Patient Analytics — Advanced SQL Execution Audit

**Database Engine:** `SQLITE`  
**Total Queries Evaluated:** 16 | **Passed:** 16 | **Failed:** 0

| # | Analytical Query Title | Rows Returned | Latency (ms) | Status |
|:---|:---|---:|---:|:---|
| 1 | `QUERY 1: Longitudinal Monthly Encounter Trends by Care Setting` | 48 | 31.08 ms | ✅ PASS |
| 2 | `QUERY 2: Patient Healthcare Expenditure Deciles (NTILE Segmentation)` | 10 | 33.2 ms | ✅ PASS |
| 3 | `QUERY 3: 30-Day Subsequent Re-encounter Rate by Clinical Department` | 8 | 9.72 ms | ✅ PASS |
| 4 | `QUERY 4: Inpatient Length of Stay (LOS) Benchmark & Outlier Detection` | 8 | 4.97 ms | ✅ PASS |
| 5 | `QUERY 5: Top Diagnosed Chronic Conditions (Avoiding Double-Counting in Joins)` | 12 | 44.62 ms | ✅ PASS |
| 6 | `QUERY 6: Payer Reimbursed Revenue vs. Contractual Shortfall Analysis` | 6 | 14.27 ms | ✅ PASS |
| 7 | `QUERY 7: Longitudinal Patient Acquisition Cohort Analysis in Pure SQL` | 12 | 54.11 ms | ✅ PASS |
| 8 | `QUERY 8: Frequent Healthcare Utilizers & Sequential Event Gap Analysis` | 20 | 62.59 ms | ✅ PASS |
| 9 | `QUERY 9: Provider Clinical Productivity & Departmental Ranking` | 48 | 42.4 ms | ✅ PASS |
| 10 | `QUERY 10: Clinical Department Volume vs. Financial Contribution Matrix` | 8 | 15.16 ms | ✅ PASS |
| 11 | `QUERY 11: Intake Admission Volume by Day of Week & Hour of Day` | 7 | 18.3 ms | ✅ PASS |
| 12 | `QUERY 12: First-Time Patient Conversion to Long-Term Follow-up Care` | 4 | 11.81 ms | ✅ PASS |
| 13 | `QUERY 13: High-Cost Clinical Procedures & Expense Contribution` | 7 | 7.63 ms | ✅ PASS |
| 14 | `QUERY 14: Complex Multimorbidity (Chronic Condition Comorbidity Burden)` | 8 | 12.09 ms | ✅ PASS |
| 15 | `QUERY 15: Hospital Facility Network Volume & Regional Utilization Share` | 6 | 19.36 ms | ✅ PASS |
| 16 | `QUERY 16: Rolling 90-Day Moving Average of Emergency Department Influx` | 1,461 | 28.21 ms | ✅ PASS |

## Sample Query Outputs

### QUERY 1: Longitudinal Monthly Encounter Trends by Care Setting

| year_month | year | month_name | total_encounters | inpatient_count | emergency_count | ambulatory_count | wellness_count | gross_claim_revenue | prior_month_encounters | mom_growth_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2021-01 | 2021 | January | 122 | 7 | 13 | 53 | 31 | 160346.18 | nan | nan |
| 2021-02 | 2021 | February | 139 | 13 | 20 | 54 | 29 | 377258.89 | 122.0 | 13.93 |
| 2021-03 | 2021 | March | 125 | 10 | 11 | 56 | 17 | 177067.74 | 139.0 | -10.07 |


### QUERY 2: Patient Healthcare Expenditure Deciles (NTILE Segmentation)

| cost_decile | patients_in_decile | decile_total_spend | avg_patient_spend | avg_encounters | spend_percentage_of_hospital_total |
| --- | --- | --- | --- | --- | --- |
| 1 | 120 | 4129314.07 | 34410.95 | 7.8 | 44.37 |
| 2 | 120 | 2251881.75 | 18765.68 | 6.3 | 24.2 |
| 3 | 120 | 1086796.06 | 9056.63 | 6.8 | 11.68 |


### QUERY 3: 30-Day Subsequent Re-encounter Rate by Clinical Department

| clinical_department | total_acute_discharges | subsequent_30d_reencounters | reencounter_rate_pct | avg_index_claim_cost |
| --- | --- | --- | --- | --- |
| Surgical Services | 23 | 7 | 30.43 | 8835.77 |
| Orthopedic & Musculoskeletal Care | 62 | 12 | 19.35 | 8823.31 |
| Children's Health Services | 146 | 22 | 15.07 | 7096.77 |


### QUERY 4: Inpatient Length of Stay (LOS) Benchmark & Outlier Detection

| clinical_department | total_admissions | mean_los_days | min_los_days | max_los_days | high_stay_outliers | avg_admission_claim_cost |
| --- | --- | --- | --- | --- | --- | --- |
| Department of Internal Medicine | 43 | 5.75 | 1.03 | 9.95 | 11 | 15355.54 |
| Neurological Sciences | 35 | 5.61 | 1.25 | 9.46 | 4 | 17269.83 |
| Primary & Community Medicine | 61 | 5.55 | 1.21 | 9.96 | 7 | 15237.42 |


### QUERY 5: Top Diagnosed Chronic Conditions (Avoiding Double-Counting in Joins)

| condition_code | condition_name | is_chronic | clinical_category | distinct_encounters | unique_patients_diagnosed | attributed_avg_encounter_cost |
| --- | --- | --- | --- | --- | --- | --- |
| 22298006 | Myocardial infarction | 1 | Cardiometabolic | 422 | 333 | 1347.84 |
| 65363002 | Otitis media | 0 | Respiratory / General | 380 | 325 | 1564.21 |
| 444814009 | Viral sinusitis | 0 | Respiratory / General | 386 | 322 | 1707.05 |


### QUERY 6: Payer Reimbursed Revenue vs. Contractual Shortfall Analysis

| payer | total_claims_submitted | gross_billed_charges | total_payer_reimbursement | total_patient_responsibility | payer_reimbursement_rate_pct | patient_copay_burden_pct |
| --- | --- | --- | --- | --- | --- | --- |
| Medicare | 1828 | 2961543.27 | 2445101.36 | 516441.91 | 82.56 | 17.44 |
| Blue Cross Blue Shield | 1529 | 2341473.0 | 1952764.41 | 388708.59 | 83.4 | 16.6 |
| Medicaid | 1148 | 1637805.66 | 1368826.17 | 268979.49 | 83.58 | 16.42 |


### QUERY 7: Longitudinal Patient Acquisition Cohort Analysis in Pure SQL

| cohort_month | m0_cohort_size | m1_active | m3_active | m6_active | m12_active | m6_retention_rate_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 2021-01 | 116 | 10 | 23 | 8 | 8 | 6.9 |
| 2021-02 | 121 | 12 | 13 | 14 | 12 | 11.6 |
| 2021-03 | 86 | 6 | 8 | 8 | 15 | 9.3 |


### QUERY 8: Frequent Healthcare Utilizers & Sequential Event Gap Analysis

| patient_key | total_visits_recorded | total_expenditure | max_sequence | avg_days_between_visits |
| --- | --- | --- | --- | --- |
| PT_CE7BB6593021 | 14 | 55441.87 | 14 | 51.6 |
| PT_3AFE8DA758D4 | 14 | 48373.19 | 14 | 105.3 |
| PT_61E90FBCA60B | 14 | 46576.23 | 14 | 105.2 |


### QUERY 9: Provider Clinical Productivity & Departmental Ranking

| clinical_department | provider_name | encounters_handled | total_charges_billed | avg_encounter_duration_hrs | rank_in_department | pct_of_department_revenue |
| --- | --- | --- | --- | --- | --- | --- |
| Children's Health Services | Dr. William Williams | 150 | 251713.61 | 7.46 | 1 | 19.97 |
| Children's Health Services | Dr. Elizabeth Williams | 115 | 219897.59 | 10.05 | 2 | 17.45 |
| Children's Health Services | Dr. James Hernandez | 129 | 215093.09 | 11.31 | 3 | 17.07 |


### QUERY 10: Clinical Department Volume vs. Financial Contribution Matrix

| clinical_department | encounter_volume | volume_share_pct | gross_charges | revenue_share_pct | avg_cost_per_encounter | avg_duration_hours |
| --- | --- | --- | --- | --- | --- | --- |
| Emergency Services | 1358 | 22.79 | 2229282.21 | 23.95 | 1641.59 | 11.7 |
| Primary & Community Medicine | 1066 | 17.89 | 1539480.52 | 16.54 | 1444.17 | 9.59 |
| Heart & Vascular Institute | 1123 | 18.84 | 1531212.94 | 16.45 | 1363.5 | 8.99 |


### QUERY 11: Intake Admission Volume by Day of Week & Hour of Day

| day_name | day_of_week | is_weekend | total_intakes | emergency_intakes | inpatient_admissions | emergency_intake_ratio_pct |
| --- | --- | --- | --- | --- | --- | --- |
| Monday | 0 | 0 | 848 | 79 | 56 | 9.32 |
| Tuesday | 1 | 0 | 864 | 92 | 52 | 10.65 |
| Wednesday | 2 | 0 | 837 | 83 | 53 | 9.92 |


### QUERY 12: First-Time Patient Conversion to Long-Term Follow-up Care

| visit_frequency_tier | patient_count | patient_percentage | avg_visits_in_tier |
| --- | --- | --- | --- |
| 2 to 4 Visits | 498 | 41.5 | 3.0 |
| 5 to 9 Visits | 437 | 36.42 | 6.5 |
| 10+ High Utilizer | 133 | 11.08 | 11.2 |


### QUERY 13: High-Cost Clinical Procedures & Expense Contribution

| procedure_code | procedure_name | procedure_volume | unique_patients | total_procedure_expenditure | mean_unit_procedure_cost | min_unit_cost | max_unit_cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 232717009 | Coronary artery bypass graft | 433 | 364 | 12124000.0 | 28000.0 | 28000.0 | 28000.0 |
| 80146002 | Appendectomy | 435 | 349 | 2523000.0 | 5800.0 | 5800.0 | 5800.0 |
| 73761001 | Colonoscopy | 412 | 339 | 515000.0 | 1250.0 | 1250.0 | 1250.0 |


### QUERY 14: Complex Multimorbidity (Chronic Condition Comorbidity Burden)

| chronic_conditions_count | patient_count | avg_annual_income | avg_lifetime_claim_cost | avg_lifetime_encounters |
| --- | --- | --- | --- | --- |
| 0 | 100 | 57868.7 | 3322.21 | 1.8 |
| 1 | 301 | 58936.8 | 4324.74 | 2.7 |
| 2 | 303 | 59295.55 | 5912.59 | 4.0 |


### QUERY 15: Hospital Facility Network Volume & Regional Utilization Share

| org_id | org_name | city | annual_revenue | utilization_rating | actual_encounters_managed | unique_patients_served | total_billed_charges | avg_charge_per_encounter | hospital_network_market_share_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 198123d8-87c9-4a9d-acae-6cea8971ef1f | Massachusetts General Medical Center | Boston | 24500000 | 880 | 1021 | 646 | 1812301.93 | 1775.03 | 17.13 |
| fbcca2bd-d027-43c7-ba7c-664fb7952bac | Cambridge Community Health Alliance | Cambridge | 14200000 | 620 | 1016 | 668 | 1477989.96 | 1454.71 | 17.05 |
| 80bcb923-219b-47b3-a755-735e8c3e53b2 | Springfield Baystate Health Network | Springfield | 18900000 | 740 | 996 | 662 | 1618630.53 | 1625.13 | 16.71 |


### QUERY 16: Rolling 90-Day Moving Average of Emergency Department Influx

| full_date | daily_ed_visits | daily_ed_charges | rolling_90d_avg_ed_visits | rolling_90d_total_ed_charges |
| --- | --- | --- | --- | --- |
| 2021-01-01 | 1 | 2479.43 | 1.0 | 2479.43 |
| 2021-01-02 | 0 | nan | 0.5 | 2479.43 |
| 2021-01-03 | 1 | 3444.45 | 0.67 | 5923.88 |


