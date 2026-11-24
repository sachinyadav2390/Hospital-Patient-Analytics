-- ============================================================================
-- Hospital Patient Analytics & Healthcare Performance Optimization
-- 16 Production-Grade Advanced Analytical SQL Queries
-- Demonstrating CTEs, Window Functions, Complex Aggregations, & Star Schema Joins
-- Compatible with PostgreSQL and SQLite
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Longitudinal Monthly Encounter Trends by Care Setting
-- Demonstrates: CTE, Date Dimension Join, Conditional Aggregation, MoM Growth
-- ----------------------------------------------------------------------------
WITH monthly_volume AS (
    SELECT
        d.year_month,
        d.year,
        d.month_name,
        COUNT(f.encounter_id) AS total_encounters,
        SUM(CASE WHEN f.encounter_class = 'inpatient' THEN 1 ELSE 0 END) AS inpatient_count,
        SUM(CASE WHEN f.encounter_class = 'emergency' THEN 1 ELSE 0 END) AS emergency_count,
        SUM(CASE WHEN f.encounter_class = 'ambulatory' THEN 1 ELSE 0 END) AS ambulatory_count,
        SUM(CASE WHEN f.encounter_class = 'wellness' THEN 1 ELSE 0 END) AS wellness_count,
        ROUND(SUM(f.total_claim_cost), 2) AS gross_claim_revenue
    FROM fact_encounters f
    INNER JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year_month, d.year, d.month_name
)
SELECT
    year_month,
    year,
    month_name,
    total_encounters,
    inpatient_count,
    emergency_count,
    ambulatory_count,
    wellness_count,
    gross_claim_revenue,
    LAG(total_encounters, 1) OVER (ORDER BY year_month) AS prior_month_encounters,
    ROUND(
        (total_encounters - LAG(total_encounters, 1) OVER (ORDER BY year_month)) * 100.0 /
        NULLIF(LAG(total_encounters, 1) OVER (ORDER BY year_month), 0),
        2
    ) AS mom_growth_pct
FROM monthly_volume
ORDER BY year_month;


-- ----------------------------------------------------------------------------
-- QUERY 2: Patient Healthcare Expenditure Deciles (NTILE Segmentation)
-- Demonstrates: Window Function NTILE, Pareto Distribution Analysis
-- ----------------------------------------------------------------------------
WITH patient_totals AS (
    SELECT
        p.patient_key,
        p.gender,
        p.current_age_group,
        COUNT(f.encounter_id) AS total_encounters,
        ROUND(SUM(f.total_claim_cost), 2) AS patient_lifetime_cost,
        ROUND(SUM(f.payer_coverage), 2) AS total_payer_coverage,
        ROUND(SUM(f.patient_payment), 2) AS total_out_of_pocket
    FROM dim_patient p
    INNER JOIN fact_encounters f ON p.patient_key = f.patient_key
    GROUP BY p.patient_key, p.gender, p.current_age_group
),
decile_assignment AS (
    SELECT
        patient_key,
        gender,
        current_age_group,
        total_encounters,
        patient_lifetime_cost,
        total_payer_coverage,
        total_out_of_pocket,
        NTILE(10) OVER (ORDER BY patient_lifetime_cost DESC) AS cost_decile
    FROM patient_totals
)
SELECT
    cost_decile,
    COUNT(patient_key) AS patients_in_decile,
    ROUND(SUM(patient_lifetime_cost), 2) AS decile_total_spend,
    ROUND(AVG(patient_lifetime_cost), 2) AS avg_patient_spend,
    ROUND(AVG(total_encounters), 1) AS avg_encounters,
    ROUND(
        SUM(patient_lifetime_cost) * 100.0 / SUM(SUM(patient_lifetime_cost)) OVER (),
        2
    ) AS spend_percentage_of_hospital_total
FROM decile_assignment
GROUP BY cost_decile
ORDER BY cost_decile;


-- ----------------------------------------------------------------------------
-- QUERY 3: 30-Day Subsequent Re-encounter Rate by Clinical Department
-- Demonstrates: Filtered Index Encounters, Window Function (Subsequent Event Check)
-- ----------------------------------------------------------------------------
WITH eligible_acute_encounters AS (
    SELECT
        f.encounter_id,
        f.patient_key,
        f.encounter_class,
        pr.clinical_department,
        f.stop_time,
        f.re_encounter_30d,
        f.total_claim_cost
    FROM fact_encounters f
    INNER JOIN dim_provider pr ON f.provider_id = pr.provider_id
    WHERE f.encounter_class IN ('inpatient', 'emergency')
)
SELECT
    clinical_department,
    COUNT(encounter_id) AS total_acute_discharges,
    SUM(re_encounter_30d) AS subsequent_30d_reencounters,
    ROUND(SUM(re_encounter_30d) * 100.0 / COUNT(encounter_id), 2) AS reencounter_rate_pct,
    ROUND(AVG(total_claim_cost), 2) AS avg_index_claim_cost
FROM eligible_acute_encounters
GROUP BY clinical_department
HAVING COUNT(encounter_id) >= 10
ORDER BY reencounter_rate_pct DESC;


-- ----------------------------------------------------------------------------
-- QUERY 4: Inpatient Length of Stay (LOS) Benchmark & Outlier Detection
-- Demonstrates: Statistical Mean/StdDev Window Function, Z-score Outliers
-- ----------------------------------------------------------------------------
WITH inpatient_stats AS (
    SELECT
        f.encounter_id,
        f.patient_key,
        pr.clinical_department,
        f.length_of_stay_days,
        f.total_claim_cost,
        AVG(f.length_of_stay_days) OVER (PARTITION BY pr.clinical_department) AS dept_mean_los,
        ROUND(f.length_of_stay_days - AVG(f.length_of_stay_days) OVER (PARTITION BY pr.clinical_department), 2) AS los_variance_from_dept_mean
    FROM fact_encounters f
    INNER JOIN dim_provider pr ON f.provider_id = pr.provider_id
    WHERE f.encounter_class = 'inpatient'
)
SELECT
    clinical_department,
    COUNT(encounter_id) AS total_admissions,
    ROUND(AVG(length_of_stay_days), 2) AS mean_los_days,
    ROUND(MIN(length_of_stay_days), 2) AS min_los_days,
    ROUND(MAX(length_of_stay_days), 2) AS max_los_days,
    SUM(CASE WHEN length_of_stay_days > (dept_mean_los * 1.5) THEN 1 ELSE 0 END) AS high_stay_outliers,
    ROUND(AVG(total_claim_cost), 2) AS avg_admission_claim_cost
FROM inpatient_stats
GROUP BY clinical_department
ORDER BY mean_los_days DESC;


-- ----------------------------------------------------------------------------
-- QUERY 5: Top Diagnosed Chronic Conditions (Avoiding Double-Counting in Joins)
-- Demonstrates: Bridge Table Aggregation, Distinct Patient Counts, Cost Aggregation
-- ----------------------------------------------------------------------------
SELECT
    c.condition_code,
    c.condition_name,
    c.is_chronic,
    c.clinical_category,
    COUNT(DISTINCT fc.encounter_id) AS distinct_encounters,
    COUNT(DISTINCT fc.patient_key) AS unique_patients_diagnosed,
    ROUND(SUM(f.total_claim_cost) / COUNT(fc.id), 2) AS attributed_avg_encounter_cost
FROM dim_condition c
INNER JOIN fact_encounter_conditions fc ON c.condition_code = fc.condition_code
INNER JOIN fact_encounters f ON fc.encounter_id = f.encounter_id
GROUP BY c.condition_code, c.condition_name, c.is_chronic, c.clinical_category
ORDER BY unique_patients_diagnosed DESC;


-- ----------------------------------------------------------------------------
-- QUERY 6: Payer Reimbursed Revenue vs. Contractual Shortfall Analysis
-- Demonstrates: Financial Performance Metrics, Payer Collection Ratios
-- ----------------------------------------------------------------------------
SELECT
    f.payer,
    COUNT(f.encounter_id) AS total_claims_submitted,
    ROUND(SUM(f.total_claim_cost), 2) AS gross_billed_charges,
    ROUND(SUM(f.payer_coverage), 2) AS total_payer_reimbursement,
    ROUND(SUM(f.patient_payment), 2) AS total_patient_responsibility,
    ROUND(
        SUM(f.payer_coverage) * 100.0 / NULLIF(SUM(f.total_claim_cost), 0),
        2
    ) AS payer_reimbursement_rate_pct,
    ROUND(
        SUM(f.patient_payment) * 100.0 / NULLIF(SUM(f.total_claim_cost), 0),
        2
    ) AS patient_copay_burden_pct
FROM fact_encounters f
GROUP BY f.payer
ORDER BY gross_billed_charges DESC;


-- ----------------------------------------------------------------------------
-- QUERY 7: Longitudinal Patient Acquisition Cohort Analysis in Pure SQL
-- Demonstrates: Cohort Inception Grouping, Dynamic Month Offset Calculation
-- ----------------------------------------------------------------------------
WITH patient_cohort AS (
    SELECT
        f.patient_key,
        MIN(d.year_month) AS cohort_month
    FROM fact_encounters f
    INNER JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY f.patient_key
),
patient_activity AS (
    SELECT
        f.patient_key,
        c.cohort_month,
        d.year_month AS activity_month,
        (CAST(SUBSTR(d.year_month, 1, 4) AS INT) - CAST(SUBSTR(c.cohort_month, 1, 4) AS INT)) * 12 +
        (CAST(SUBSTR(d.year_month, 6, 2) AS INT) - CAST(SUBSTR(c.cohort_month, 6, 2) AS INT)) AS month_offset
    FROM fact_encounters f
    INNER JOIN dim_date d ON f.date_key = d.date_key
    INNER JOIN patient_cohort c ON f.patient_key = c.patient_key
)
SELECT
    cohort_month,
    COUNT(DISTINCT CASE WHEN month_offset = 0 THEN patient_key END) AS m0_cohort_size,
    COUNT(DISTINCT CASE WHEN month_offset = 1 THEN patient_key END) AS m1_active,
    COUNT(DISTINCT CASE WHEN month_offset = 3 THEN patient_key END) AS m3_active,
    COUNT(DISTINCT CASE WHEN month_offset = 6 THEN patient_key END) AS m6_active,
    COUNT(DISTINCT CASE WHEN month_offset = 12 THEN patient_key END) AS m12_active,
    ROUND(
        COUNT(DISTINCT CASE WHEN month_offset = 6 THEN patient_key END) * 100.0 /
        NULLIF(COUNT(DISTINCT CASE WHEN month_offset = 0 THEN patient_key END), 0),
        1
    ) AS m6_retention_rate_pct
FROM patient_activity
GROUP BY cohort_month
ORDER BY cohort_month
LIMIT 12;


-- ----------------------------------------------------------------------------
-- QUERY 8: Frequent Healthcare Utilizers & Sequential Event Gap Analysis
-- Demonstrates: Window Functions LEAD/LAG, Day Intervals Between Visits
-- ----------------------------------------------------------------------------
WITH visit_intervals AS (
    SELECT
        f.patient_key,
        f.encounter_id,
        f.start_time,
        f.encounter_class,
        f.total_claim_cost,
        f.visit_sequence_number,
        LAG(f.start_time, 1) OVER (PARTITION BY f.patient_key ORDER BY f.start_time) AS prev_visit_time
    FROM fact_encounters f
)
SELECT
    patient_key,
    COUNT(encounter_id) AS total_visits_recorded,
    ROUND(SUM(total_claim_cost), 2) AS total_expenditure,
    MAX(visit_sequence_number) AS max_sequence,
    ROUND(AVG(
        CASE
            WHEN prev_visit_time IS NOT NULL THEN
                (JULIANDAY(start_time) - JULIANDAY(prev_visit_time))
            ELSE NULL
        END
    ), 1) AS avg_days_between_visits
FROM visit_intervals
GROUP BY patient_key
HAVING COUNT(encounter_id) >= 6
ORDER BY total_visits_recorded DESC, total_expenditure DESC
LIMIT 20;


-- ----------------------------------------------------------------------------
-- QUERY 9: Provider Clinical Productivity & Departmental Ranking
-- Demonstrates: DENSE_RANK Window Function, Revenue Contribution
-- ----------------------------------------------------------------------------
WITH provider_metrics AS (
    SELECT
        pr.provider_id,
        pr.provider_name,
        pr.clinical_department,
        COUNT(f.encounter_id) AS encounters_handled,
        ROUND(SUM(f.total_claim_cost), 2) AS total_charges_billed,
        ROUND(AVG(f.duration_hours), 2) AS avg_encounter_duration_hrs
    FROM dim_provider pr
    INNER JOIN fact_encounters f ON pr.provider_id = f.provider_id
    GROUP BY pr.provider_id, pr.provider_name, pr.clinical_department
)
SELECT
    clinical_department,
    provider_name,
    encounters_handled,
    total_charges_billed,
    avg_encounter_duration_hrs,
    DENSE_RANK() OVER (PARTITION BY clinical_department ORDER BY total_charges_billed DESC) AS rank_in_department,
    ROUND(
        total_charges_billed * 100.0 / SUM(total_charges_billed) OVER (PARTITION BY clinical_department),
        2
    ) AS pct_of_department_revenue
FROM provider_metrics
ORDER BY clinical_department, rank_in_department;


-- ----------------------------------------------------------------------------
-- QUERY 10: Clinical Department Volume vs. Financial Contribution Matrix
-- Demonstrates: Aggregate Proportions, Care Setting Contribution
-- ----------------------------------------------------------------------------
SELECT
    pr.clinical_department,
    COUNT(f.encounter_id) AS encounter_volume,
    ROUND(COUNT(f.encounter_id) * 100.0 / (SELECT COUNT(*) FROM fact_encounters), 2) AS volume_share_pct,
    ROUND(SUM(f.total_claim_cost), 2) AS gross_charges,
    ROUND(SUM(f.total_claim_cost) * 100.0 / (SELECT SUM(total_claim_cost) FROM fact_encounters), 2) AS revenue_share_pct,
    ROUND(AVG(f.total_claim_cost), 2) AS avg_cost_per_encounter,
    ROUND(AVG(f.duration_hours), 2) AS avg_duration_hours
FROM dim_provider pr
INNER JOIN fact_encounters f ON pr.provider_id = f.provider_id
GROUP BY pr.clinical_department
ORDER BY gross_charges DESC;


-- ----------------------------------------------------------------------------
-- QUERY 11: Intake Admission Volume by Day of Week & Hour of Day
-- Demonstrates: Temporal Patterns, Emergency vs Scheduled Influx
-- ----------------------------------------------------------------------------
SELECT
    d.day_name,
    d.day_of_week,
    d.is_weekend,
    COUNT(f.encounter_id) AS total_intakes,
    SUM(CASE WHEN f.is_emergency = 1 THEN 1 ELSE 0 END) AS emergency_intakes,
    SUM(CASE WHEN f.is_inpatient = 1 THEN 1 ELSE 0 END) AS inpatient_admissions,
    ROUND(
        SUM(CASE WHEN f.is_emergency = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(f.encounter_id),
        2
    ) AS emergency_intake_ratio_pct
FROM fact_encounters f
INNER JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.day_name, d.day_of_week, d.is_weekend
ORDER BY d.day_of_week;


-- ----------------------------------------------------------------------------
-- QUERY 12: First-Time Patient Conversion to Long-Term Follow-up Care
-- Demonstrates: Sequence Logic, Patient Retention Rates
-- ----------------------------------------------------------------------------
WITH patient_visit_counts AS (
    SELECT
        patient_key,
        COUNT(encounter_id) AS visit_count,
        MIN(start_time) AS initial_visit_date,
        MAX(start_time) AS most_recent_visit_date
    FROM fact_encounters
    GROUP BY patient_key
)
SELECT
    CASE
        WHEN visit_count = 1 THEN 'Single Visit Only'
        WHEN visit_count BETWEEN 2 AND 4 THEN '2 to 4 Visits'
        WHEN visit_count BETWEEN 5 AND 9 THEN '5 to 9 Visits'
        ELSE '10+ High Utilizer'
    END AS visit_frequency_tier,
    COUNT(patient_key) AS patient_count,
    ROUND(COUNT(patient_key) * 100.0 / (SELECT COUNT(*) FROM dim_patient), 2) AS patient_percentage,
    ROUND(AVG(visit_count), 1) AS avg_visits_in_tier
FROM patient_visit_counts
GROUP BY
    CASE
        WHEN visit_count = 1 THEN 'Single Visit Only'
        WHEN visit_count BETWEEN 2 AND 4 THEN '2 to 4 Visits'
        WHEN visit_count BETWEEN 5 AND 9 THEN '5 to 9 Visits'
        ELSE '10+ High Utilizer'
    END
ORDER BY patient_count DESC;


-- ----------------------------------------------------------------------------
-- QUERY 13: High-Cost Clinical Procedures & Expense Contribution
-- Demonstrates: Bridge Table Procedure Aggregation, Unit Economics
-- ----------------------------------------------------------------------------
SELECT
    fp.procedure_code,
    fp.procedure_name,
    COUNT(fp.procedure_id) AS procedure_volume,
    COUNT(DISTINCT fp.patient_key) AS unique_patients,
    ROUND(SUM(fp.procedure_cost), 2) AS total_procedure_expenditure,
    ROUND(AVG(fp.procedure_cost), 2) AS mean_unit_procedure_cost,
    ROUND(MIN(fp.procedure_cost), 2) AS min_unit_cost,
    ROUND(MAX(fp.procedure_cost), 2) AS max_unit_cost
FROM fact_encounter_procedures fp
GROUP BY fp.procedure_code, fp.procedure_name
ORDER BY total_procedure_expenditure DESC;


-- ----------------------------------------------------------------------------
-- QUERY 14: Complex Multimorbidity (Chronic Condition Comorbidity Burden)
-- Demonstrates: Patient-level Condition Stacking, Health Status Profiling
-- ----------------------------------------------------------------------------
WITH patient_chronic_burden AS (
    SELECT
        fc.patient_key,
        COUNT(DISTINCT fc.condition_code) AS distinct_chronic_conditions
    FROM fact_encounter_conditions fc
    INNER JOIN dim_condition c ON fc.condition_code = c.condition_code
    WHERE c.is_chronic = 1
    GROUP BY fc.patient_key
)
SELECT
    COALESCE(b.distinct_chronic_conditions, 0) AS chronic_conditions_count,
    COUNT(p.patient_key) AS patient_count,
    ROUND(AVG(p.annual_income), 2) AS avg_annual_income,
    ROUND(AVG(p.total_lifetime_claim_cost), 2) AS avg_lifetime_claim_cost,
    ROUND(AVG(p.total_lifetime_encounters), 1) AS avg_lifetime_encounters
FROM dim_patient p
LEFT JOIN patient_chronic_burden b ON p.patient_key = b.patient_key
GROUP BY COALESCE(b.distinct_chronic_conditions, 0)
ORDER BY chronic_conditions_count ASC;


-- ----------------------------------------------------------------------------
-- QUERY 15: Hospital Facility Network Volume & Regional Utilization Share
-- Demonstrates: Facility-Level Aggregations, Utilization Ratios
-- ----------------------------------------------------------------------------
SELECT
    o.org_id,
    o.org_name,
    o.city,
    o.annual_revenue,
    o.utilization_rating,
    COUNT(f.encounter_id) AS actual_encounters_managed,
    COUNT(DISTINCT f.patient_key) AS unique_patients_served,
    ROUND(SUM(f.total_claim_cost), 2) AS total_billed_charges,
    ROUND(AVG(f.total_claim_cost), 2) AS avg_charge_per_encounter,
    ROUND(
        COUNT(f.encounter_id) * 100.0 / (SELECT COUNT(*) FROM fact_encounters),
        2
    ) AS hospital_network_market_share_pct
FROM dim_organization o
LEFT JOIN fact_encounters f ON o.org_id = f.org_id
GROUP BY o.org_id, o.org_name, o.city, o.annual_revenue, o.utilization_rating
ORDER BY actual_encounters_managed DESC;


-- ----------------------------------------------------------------------------
-- QUERY 16: Rolling 90-Day Moving Average of Emergency Department Influx
-- Demonstrates: Moving Average Window Function (ROWS BETWEEN), Time Smoothing
-- ----------------------------------------------------------------------------
WITH daily_emergency_counts AS (
    SELECT
        d.full_date,
        d.date_key,
        COUNT(f.encounter_id) AS daily_ed_visits,
        ROUND(SUM(f.total_claim_cost), 2) AS daily_ed_charges
    FROM dim_date d
    LEFT JOIN fact_encounters f ON d.date_key = f.date_key AND f.is_emergency = 1
    WHERE d.year BETWEEN 2021 AND 2024
    GROUP BY d.full_date, d.date_key
)
SELECT
    full_date,
    daily_ed_visits,
    daily_ed_charges,
    ROUND(
        AVG(daily_ed_visits) OVER (ORDER BY date_key ROWS BETWEEN 89 PRECEDING AND CURRENT ROW),
        2
    ) AS rolling_90d_avg_ed_visits,
    ROUND(
        SUM(daily_ed_charges) OVER (ORDER BY date_key ROWS BETWEEN 89 PRECEDING AND CURRENT ROW),
        2
    ) AS rolling_90d_total_ed_charges
FROM daily_emergency_counts
ORDER BY date_key;
