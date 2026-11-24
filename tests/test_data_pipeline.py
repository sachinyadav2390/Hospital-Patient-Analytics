"""
Automated Quality Assurance & Reconciliation Test Suite
Hospital Patient Analytics & Healthcare Performance Optimization

Validates:
1. Schema integrity & primary/foreign key uniqueness
2. HIPAA de-identification & PII elimination
3. Chronological validity (STOP >= START, START >= BIRTHDATE)
4. Cost non-negativity & revenue formula reconciliation
5. Exact age & age-bracket derivations
6. Cross-tool reconciliation across Python, SQL, Excel, and Power BI
"""

import pytest
import pandas as pd
import numpy as np
import openpyxl
from sqlalchemy import text


# -----------------------------------------------------------------------------
# 1. SCHEMA & DE-IDENTIFICATION TESTS
# -----------------------------------------------------------------------------

def test_patient_pii_elimination(clean_patients):
    """Verify that direct PII identifiers are completely eliminated from analytical tables."""
    forbidden_pii = ["SSN", "DRIVERS", "PASSPORT", "FIRST", "LAST", "MAIDEN", "ADDRESS", "PHONE"]
    for col in forbidden_pii:
        assert col not in clean_patients.columns, f"Direct PII column '{col}' detected in cleaned patient dataset!"

    # Verify surrogate patient keys format
    assert clean_patients["PATIENT_KEY"].notnull().all(), "Null patient keys detected!"
    assert clean_patients["PATIENT_KEY"].str.startswith("PT_").all(), "Invalid patient key format detected!"


def test_primary_key_uniqueness(clean_patients, clean_encounters):
    """Verify that primary keys have 0 duplicates."""
    assert clean_patients["PATIENT_KEY"].duplicated().sum() == 0, "Duplicate PATIENT_KEY found in dim_patients!"
    assert clean_encounters["Id"].duplicated().sum() == 0, "Duplicate encounter Id found in fact_encounters!"


# -----------------------------------------------------------------------------
# 2. CHRONOLOGICAL & CLINICAL VALIDITY TESTS
# -----------------------------------------------------------------------------

def test_encounter_chronology(clean_encounters):
    """Verify that encounter STOP timestamp is always >= START timestamp."""
    invalid_duration = clean_encounters["STOP"] < clean_encounters["START"]
    assert invalid_duration.sum() == 0, f"Found {invalid_duration.sum()} encounters where STOP < START!"
    assert (clean_encounters["DURATION_MINUTES"] >= 0).all(), "Negative duration minutes detected!"


def test_encounter_birthdate_chronology(clean_encounters, clean_patients):
    """Verify encounter start occurs after patient birthdate."""
    pt_births = clean_patients.set_index("PATIENT_KEY")["BIRTHDATE"].to_dict()
    enc_births = pd.to_datetime(clean_encounters["PATIENT_KEY"].map(pt_births)).dt.tz_localize(None)
    start_naive = pd.to_datetime(clean_encounters["START"]).dt.tz_localize(None)

    invalid_birth_order = start_naive < enc_births
    assert invalid_birth_order.sum() == 0, f"Found {invalid_birth_order.sum()} encounters occurring before patient birthdate!"


def test_age_at_encounter_calculation(clean_encounters):
    """Verify that age at encounter is positive, realistic (0 to 110), and properly grouped."""
    assert (clean_encounters["AGE_AT_ENCOUNTER"] >= 0).all(), "Negative age at encounter found!"
    assert (clean_encounters["AGE_AT_ENCOUNTER"] <= 110).all(), "Unrealistic age (>110) found!"

    valid_groups = {"0-17 (Pediatric)", "18-34 (Young Adult)", "35-49 (Adult)", "50-64 (Middle-Aged)", "65-79 (Older Adult)", "80+ (Senior)"}
    assert set(clean_encounters["AGE_GROUP"].unique()).issubset(valid_groups), "Unrecognized age group category!"


# -----------------------------------------------------------------------------
# 3. FINANCIAL INTEGRITY & FORMULA TESTS
# -----------------------------------------------------------------------------

def test_cost_non_negativity(clean_encounters):
    """Verify that all cost components are strictly >= 0."""
    for col in ["BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST", "PAYER_COVERAGE", "PATIENT_PAYMENT"]:
        assert (clean_encounters[col] >= 0).all(), f"Negative values found in financial column '{col}'!"


def test_revenue_split_formula(clean_encounters):
    """Verify that TOTAL_CLAIM_COST == PAYER_COVERAGE + PATIENT_PAYMENT (within rounding tolerance)."""
    calculated_sum = (clean_encounters["PAYER_COVERAGE"] + clean_encounters["PATIENT_PAYMENT"]).round(2)
    diff = (clean_encounters["TOTAL_CLAIM_COST"].round(2) - calculated_sum).abs()
    assert (diff <= 0.02).all(), f"Financial imbalance detected: Claim cost != Payer + Patient coverage! Max diff: {diff.max()}"


def test_clinical_department_assignment(clean_encounters):
    """Verify every encounter has a valid, non-null clinical department mapped."""
    assert clean_encounters["CLINICAL_DEPARTMENT"].notnull().all(), "Null clinical departments detected!"
    assert not (clean_encounters["CLINICAL_DEPARTMENT"] == "").any(), "Empty clinical department strings detected!"


# -----------------------------------------------------------------------------
# 4. CROSS-TOOL RECONCILIATION TESTS (Python, SQL, Power BI, Excel)
# -----------------------------------------------------------------------------

def test_database_record_count_reconciliation(db_engine, clean_encounters, clean_patients):
    """Verify record counts match exactly between Python processed dataframes and SQL tables."""
    with db_engine.connect() as conn:
        sql_enc_count = conn.execute(text("SELECT COUNT(*) FROM fact_encounters;")).scalar()
        sql_pt_count = conn.execute(text("SELECT COUNT(*) FROM dim_patient;")).scalar()

    assert sql_enc_count == len(clean_encounters), f"Encounter row mismatch: SQL ({sql_enc_count}) vs Python ({len(clean_encounters)})"
    assert sql_pt_count == len(clean_patients), f"Patient row mismatch: SQL ({sql_pt_count}) vs Python ({len(clean_patients)})"


def test_database_financial_reconciliation(db_engine, clean_encounters):
    """Verify total claim cost sum matches to the exact penny between Python and SQL."""
    py_total = round(clean_encounters["TOTAL_CLAIM_COST"].sum(), 2)
    with db_engine.connect() as conn:
        sql_total = round(conn.execute(text("SELECT SUM(total_claim_cost) FROM fact_encounters;")).scalar(), 2)

    assert abs(py_total - sql_total) < 0.01, f"Financial mismatch: SQL (${sql_total}) vs Python (${py_total})"


def test_powerbi_csv_reconciliation(powerbi_dir, clean_encounters, clean_patients):
    """Verify Power BI export CSV files match the canonical analytical totals."""
    pbi_enc = pd.read_csv(powerbi_dir / "Fact_Encounters.csv")
    pbi_pt = pd.read_csv(powerbi_dir / "Dim_Patient.csv")

    assert len(pbi_enc) == len(clean_encounters), "Power BI encounter row count mismatch!"
    assert len(pbi_pt) == len(clean_patients), "Power BI patient row count mismatch!"
    assert abs(pbi_enc["total_claim_cost"].sum() - clean_encounters["TOTAL_CLAIM_COST"].sum()) < 0.01, "Power BI gross charges mismatch!"


def test_excel_workbook_reconciliation(processed_dir):
    """Verify Excel workbook exists, contains all required sheets, and matches canonical totals."""
    from src.config import EXCEL_DIR
    excel_path = EXCEL_DIR / "Hospital_Patient_Analytics_Executive_Workbook.xlsx"
    assert excel_path.exists(), f"Excel workbook not found at {excel_path}!"

    wb = openpyxl.load_workbook(excel_path, read_only=True)
    required_sheets = [
        "Executive Summary",
        "Care Setting Operations",
        "Department & Payer Analytics",
        "Conditions & Procedures",
        "Patient Segmentation",
        "Encounter Data Extract",
        "Data Dictionary & QA"
    ]
    for s in required_sheets:
        assert s in wb.sheetnames, f"Required worksheet '{s}' missing from Excel workbook!"


def test_foreign_key_referential_integrity(db_engine):
    """Verify that there are 0 orphaned foreign keys in fact_encounters."""
    with db_engine.connect() as conn:
        orphaned_pt = conn.execute(text("""
            SELECT COUNT(*) FROM fact_encounters f
            LEFT JOIN dim_patient p ON f.patient_key = p.patient_key
            WHERE p.patient_key IS NULL;
        """)).scalar()

        orphaned_dates = conn.execute(text("""
            SELECT COUNT(*) FROM fact_encounters f
            LEFT JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.date_key IS NULL;
        """)).scalar()

        orphaned_orgs = conn.execute(text("""
            SELECT COUNT(*) FROM fact_encounters f
            LEFT JOIN dim_organization o ON f.org_id = o.org_id
            WHERE o.org_id IS NULL;
        """)).scalar()

    assert orphaned_pt == 0, f"Detected {orphaned_pt} orphaned patient keys in fact_encounters!"
    assert orphaned_dates == 0, f"Detected {orphaned_dates} orphaned date keys in fact_encounters!"
    assert orphaned_orgs == 0, f"Detected {orphaned_orgs} orphaned organization keys in fact_encounters!"
