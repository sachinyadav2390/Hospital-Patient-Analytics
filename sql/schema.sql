-- ============================================================================
-- Hospital Patient Analytics & Healthcare Performance Optimization
-- Relational Staging Schema & Analytical Star Schema
-- Compatible with PostgreSQL 13+ and SQLite 3.35+
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. STAGING TABLES (Normalized / Raw Ingestion Mirror)
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS stg_observations;
DROP TABLE IF EXISTS stg_medications;
DROP TABLE IF EXISTS stg_procedures;
DROP TABLE IF EXISTS stg_conditions;
DROP TABLE IF EXISTS stg_encounters;
DROP TABLE IF EXISTS stg_providers;
DROP TABLE IF EXISTS stg_organizations;
DROP TABLE IF EXISTS stg_patients;

CREATE TABLE stg_patients (
    patient_key VARCHAR(64) PRIMARY KEY,
    raw_id VARCHAR(64) NOT NULL,
    birthdate DATE NOT NULL,
    deathdate DATE,
    gender VARCHAR(10),
    race VARCHAR(50),
    ethnicity VARCHAR(50),
    marital VARCHAR(10),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    lat NUMERIC(9, 6),
    lon NUMERIC(9, 6),
    healthcare_expenses NUMERIC(12, 2),
    healthcare_coverage NUMERIC(12, 2),
    income NUMERIC(12, 2)
);

CREATE TABLE stg_organizations (
    org_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    lat NUMERIC(9, 6),
    lon NUMERIC(9, 6),
    phone VARCHAR(50),
    revenue NUMERIC(15, 2),
    utilization INTEGER
);

CREATE TABLE stg_providers (
    provider_id VARCHAR(64) PRIMARY KEY,
    org_id VARCHAR(64) REFERENCES stg_organizations(org_id),
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(10),
    speciality VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    lat NUMERIC(9, 6),
    lon NUMERIC(9, 6),
    utilization INTEGER
);

CREATE TABLE stg_encounters (
    encounter_id VARCHAR(64) PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    stop_time TIMESTAMP NOT NULL,
    patient_key VARCHAR(64) NOT NULL REFERENCES stg_patients(patient_key),
    org_id VARCHAR(64) REFERENCES stg_organizations(org_id),
    provider_id VARCHAR(64) REFERENCES stg_providers(provider_id),
    payer VARCHAR(100),
    encounter_class VARCHAR(50) NOT NULL,
    code VARCHAR(50),
    description VARCHAR(255),
    base_encounter_cost NUMERIC(12, 2) DEFAULT 0.00,
    total_claim_cost NUMERIC(12, 2) DEFAULT 0.00,
    payer_coverage NUMERIC(12, 2) DEFAULT 0.00,
    patient_payment NUMERIC(12, 2) DEFAULT 0.00,
    reason_code VARCHAR(50),
    reason_description VARCHAR(255)
);

CREATE TABLE stg_conditions (
    condition_id INTEGER PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_key VARCHAR(64) NOT NULL REFERENCES stg_patients(patient_key),
    encounter_id VARCHAR(64) NOT NULL REFERENCES stg_encounters(encounter_id),
    code VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL
);

CREATE TABLE stg_procedures (
    procedure_id INTEGER PRIMARY KEY,
    procedure_date TIMESTAMP NOT NULL,
    patient_key VARCHAR(64) NOT NULL REFERENCES stg_patients(patient_key),
    encounter_id VARCHAR(64) NOT NULL REFERENCES stg_encounters(encounter_id),
    code VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL,
    base_cost NUMERIC(12, 2) DEFAULT 0.00,
    reason_code VARCHAR(50),
    reason_description VARCHAR(255)
);

CREATE TABLE stg_medications (
    medication_id INTEGER PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_key VARCHAR(64) NOT NULL REFERENCES stg_patients(patient_key),
    payer VARCHAR(100),
    encounter_id VARCHAR(64) NOT NULL REFERENCES stg_encounters(encounter_id),
    code VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL,
    base_cost NUMERIC(12, 2) DEFAULT 0.00,
    payer_coverage NUMERIC(12, 2) DEFAULT 0.00,
    dispenses INTEGER DEFAULT 1,
    total_cost NUMERIC(12, 2) DEFAULT 0.00,
    reason_code VARCHAR(50),
    reason_description VARCHAR(255)
);

CREATE TABLE stg_observations (
    observation_id INTEGER PRIMARY KEY,
    observation_date TIMESTAMP NOT NULL,
    patient_key VARCHAR(64) NOT NULL REFERENCES stg_patients(patient_key),
    encounter_id VARCHAR(64) NOT NULL REFERENCES stg_encounters(encounter_id),
    code VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL,
    value VARCHAR(100),
    units VARCHAR(50),
    observation_type VARCHAR(50)
);


-- ----------------------------------------------------------------------------
-- 2. STAR SCHEMA DIMENSIONAL MODEL (Analytical Architecture)
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS fact_patient_medications;
DROP TABLE IF EXISTS fact_encounter_procedures;
DROP TABLE IF EXISTS fact_encounter_conditions;
DROP TABLE IF EXISTS fact_encounters;
DROP TABLE IF EXISTS dim_condition;
DROP TABLE IF EXISTS dim_encounter_type;
DROP TABLE IF EXISTS dim_provider;
DROP TABLE IF EXISTS dim_organization;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_patient;

-- Dimension: Patient (Demographics, Segmentation, Utilization Archetype)
CREATE TABLE dim_patient (
    patient_key VARCHAR(64) PRIMARY KEY,
    birthdate DATE NOT NULL,
    deathdate DATE,
    is_deceased INTEGER DEFAULT 0,
    gender VARCHAR(10) NOT NULL,
    race VARCHAR(50) NOT NULL,
    ethnicity VARCHAR(50) NOT NULL,
    marital VARCHAR(10),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    annual_income NUMERIC(12, 2),
    current_age NUMERIC(5, 1),
    current_age_group VARCHAR(50),
    cluster_id INTEGER,
    cluster_name VARCHAR(100),
    utilization_tier VARCHAR(50),
    total_lifetime_encounters INTEGER DEFAULT 0,
    total_lifetime_claim_cost NUMERIC(14, 2) DEFAULT 0.00
);

-- Dimension: Date (Complete Calendar Dimension)
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,         -- YYYYMMDD
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter VARCHAR(10) NOT NULL,         -- e.g. '2023-Q1'
    quarter_number INTEGER NOT NULL,      -- 1 to 4
    year_month VARCHAR(10) NOT NULL,      -- e.g. '2023-01'
    month_number INTEGER NOT NULL,        -- 1 to 12
    month_name VARCHAR(20) NOT NULL,      -- 'January'
    day_of_month INTEGER NOT NULL,        -- 1 to 31
    day_of_week INTEGER NOT NULL,         -- 0 = Monday, 6 = Sunday (or 1-7)
    day_name VARCHAR(20) NOT NULL,        -- 'Monday'
    is_weekend INTEGER NOT NULL           -- 1 = Weekend, 0 = Weekday
);

-- Dimension: Organization (Hospital & Healthcare Facilities)
CREATE TABLE dim_organization (
    org_id VARCHAR(64) PRIMARY KEY,
    org_name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zip VARCHAR(20),
    phone VARCHAR(50),
    annual_revenue NUMERIC(15, 2),
    utilization_rating INTEGER
);

-- Dimension: Provider & Clinical Department
CREATE TABLE dim_provider (
    provider_id VARCHAR(64) PRIMARY KEY,
    org_id VARCHAR(64) REFERENCES dim_organization(org_id),
    provider_name VARCHAR(255) NOT NULL,
    gender VARCHAR(10),
    speciality VARCHAR(100) NOT NULL,
    clinical_department VARCHAR(100) NOT NULL,
    historical_utilization INTEGER
);

-- Dimension: Care Setting / Encounter Type
CREATE TABLE dim_encounter_type (
    encounter_class VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    setting_description VARCHAR(255) NOT NULL,
    acuity_level VARCHAR(50) NOT NULL     -- 'Low', 'Moderate', 'High', 'Critical'
);

-- Dimension: Clinical Diagnosis Catalog
CREATE TABLE dim_condition (
    condition_code VARCHAR(50) PRIMARY KEY,
    condition_name VARCHAR(255) NOT NULL,
    is_chronic INTEGER DEFAULT 0,
    clinical_category VARCHAR(100) NOT NULL
);

-- ----------------------------------------------------------------------------
-- Core Fact: Encounters (Grain: 1 row per clinical encounter)
-- ----------------------------------------------------------------------------
CREATE TABLE fact_encounters (
    encounter_id VARCHAR(64) PRIMARY KEY,
    patient_key VARCHAR(64) NOT NULL REFERENCES dim_patient(patient_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    org_id VARCHAR(64) NOT NULL REFERENCES dim_organization(org_id),
    provider_id VARCHAR(64) NOT NULL REFERENCES dim_provider(provider_id),
    encounter_class VARCHAR(50) NOT NULL REFERENCES dim_encounter_type(encounter_class),
    payer VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    stop_time TIMESTAMP NOT NULL,
    start_hour INTEGER NOT NULL,
    duration_minutes NUMERIC(8, 1) NOT NULL,
    duration_hours NUMERIC(8, 2) NOT NULL,
    length_of_stay_days NUMERIC(6, 2) NOT NULL,
    age_at_encounter NUMERIC(5, 1) NOT NULL,
    age_group VARCHAR(50) NOT NULL,
    base_encounter_cost NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_claim_cost NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    payer_coverage NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    patient_payment NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    coverage_ratio NUMERIC(5, 4) NOT NULL DEFAULT 0.0000,
    is_inpatient INTEGER NOT NULL DEFAULT 0,
    is_emergency INTEGER NOT NULL DEFAULT 0,
    visit_sequence_number INTEGER NOT NULL DEFAULT 1,
    re_encounter_30d INTEGER NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- Bridge / Secondary Facts (Prevents Double Counting in Many-to-Many Relationships)
-- ----------------------------------------------------------------------------

-- Fact Encounter Conditions (Diagnoses documented during encounter)
CREATE TABLE fact_encounter_conditions (
    id INTEGER PRIMARY KEY,
    encounter_id VARCHAR(64) NOT NULL REFERENCES fact_encounters(encounter_id),
    patient_key VARCHAR(64) NOT NULL REFERENCES dim_patient(patient_key),
    condition_code VARCHAR(50) NOT NULL REFERENCES dim_condition(condition_code),
    onset_date DATE NOT NULL,
    resolved_date DATE
);

-- Fact Encounter Procedures (Surgical & diagnostic procedures performed)
CREATE TABLE fact_encounter_procedures (
    procedure_id INTEGER PRIMARY KEY,
    encounter_id VARCHAR(64) NOT NULL REFERENCES fact_encounters(encounter_id),
    patient_key VARCHAR(64) NOT NULL REFERENCES dim_patient(patient_key),
    procedure_code VARCHAR(50) NOT NULL,
    procedure_name VARCHAR(255) NOT NULL,
    procedure_date TIMESTAMP NOT NULL,
    procedure_cost NUMERIC(12, 2) NOT NULL DEFAULT 0.00
);

-- Fact Patient Medications (Prescriptions & dispensations)
CREATE TABLE fact_patient_medications (
    medication_id INTEGER PRIMARY KEY,
    encounter_id VARCHAR(64) NOT NULL REFERENCES fact_encounters(encounter_id),
    patient_key VARCHAR(64) NOT NULL REFERENCES dim_patient(patient_key),
    drug_code VARCHAR(50) NOT NULL,
    drug_name VARCHAR(255) NOT NULL,
    prescribed_date DATE NOT NULL,
    dispenses INTEGER NOT NULL DEFAULT 1,
    unit_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_cost NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    payer_coverage NUMERIC(12, 2) NOT NULL DEFAULT 0.00
);

-- ----------------------------------------------------------------------------
-- 3. PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX idx_fact_enc_patient ON fact_encounters(patient_key);
CREATE INDEX idx_fact_enc_date ON fact_encounters(date_key);
CREATE INDEX idx_fact_enc_org ON fact_encounters(org_id);
CREATE INDEX idx_fact_enc_provider ON fact_encounters(provider_id);
CREATE INDEX idx_fact_enc_class ON fact_encounters(encounter_class);
CREATE INDEX idx_fact_enc_start ON fact_encounters(start_time);
CREATE INDEX idx_fact_enc_reencounter ON fact_encounters(re_encounter_30d);

CREATE INDEX idx_fact_cond_encounter ON fact_encounter_conditions(encounter_id);
CREATE INDEX idx_fact_cond_code ON fact_encounter_conditions(condition_code);
CREATE INDEX idx_fact_proc_encounter ON fact_encounter_procedures(encounter_id);
CREATE INDEX idx_fact_med_encounter ON fact_patient_medications(encounter_id);
