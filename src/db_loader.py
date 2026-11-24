"""
Database Loader & Star Schema Provisioner
Hospital Patient Analytics & Healthcare Performance Optimization

Builds normalized staging and star schema tables, populates dimensions and facts
from processed CSVs, and creates performance indexes. Compatible with PostgreSQL
and SQLite (automatic local fallback).
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import (
    PROCESSED_DATA_DIR,
    SQL_DIR,
    DB_DIALECT,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    SQLITE_DB_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DatabaseLoader")


def get_database_engine() -> Tuple[Engine, str]:
    """
    Establish database engine using environment variables.
    Attempts PostgreSQL first; falls back smoothly to local SQLite if unavailable.
    """
    dialect = DB_DIALECT.lower()
    if dialect == "postgresql":
        # Check if password and host are specified
        pg_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        try:
            engine = create_engine(pg_url, connect_args={"connect_timeout": 3})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            logger.info(f"Connected successfully to PostgreSQL database at {DB_HOST}:{DB_PORT}/{DB_NAME}")
            return engine, "postgresql"
        except Exception as e:
            logger.warning(f"PostgreSQL connection to {DB_HOST}:{DB_PORT} failed ({e}). Falling back to SQLite.")

    # SQLite Fallback
    sqlite_url = f"sqlite:///{SQLITE_DB_PATH.resolve()}"
    engine = create_engine(sqlite_url)
    logger.info(f"Connected to local SQLite database at {SQLITE_DB_PATH}")
    return engine, "sqlite"


class DatabaseLoader:
    def __init__(self, data_dir: Path = PROCESSED_DATA_DIR, sql_dir: Path = SQL_DIR):
        self.data_dir = data_dir
        self.sql_dir = sql_dir
        self.engine, self.dialect = get_database_engine()

    def execute_schema_ddl(self) -> None:
        """Read and execute the schema DDL script."""
        schema_file = self.sql_dir / "schema.sql"
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_file}")

        logger.info(f"Applying schema DDL from {schema_file} on {self.dialect.upper()}...")
        with open(schema_file, "r", encoding="utf-8") as f:
            ddl_content = f.read()

        # Split DDL into individual statements
        statements = [stmt.strip() for stmt in ddl_content.split(";") if stmt.strip()]

        with self.engine.begin() as conn:
            for stmt in statements:
                # Remove comments at start
                cleaned = "\n".join([line for line in stmt.split("\n") if not line.strip().startswith("--")]).strip()
                if cleaned:
                    try:
                        conn.execute(text(cleaned))
                    except Exception as e:
                        # SQLite might differ on specific constraints; log non-critical errors
                        logger.debug(f"DDL statement notice: {e}")

        logger.info("Schema DDL applied successfully.")

    def populate_dim_date(self) -> None:
        """Generate and populate a complete calendar dimension from 2020 to 2025."""
        logger.info("Populating dim_date calendar dimension...")
        date_range = pd.date_range(start="2020-01-01", end="2025-12-31", freq="D")
        date_rows = []

        for d in date_range:
            date_key = int(d.strftime("%Y%m%d"))
            date_rows.append({
                "date_key": date_key,
                "full_date": d.strftime("%Y-%m-%d"),
                "year": d.year,
                "quarter": f"{d.year}-Q{d.quarter}",
                "quarter_number": d.quarter,
                "year_month": d.strftime("%Y-%m"),
                "month_number": d.month,
                "month_name": d.strftime("%B"),
                "day_of_month": d.day,
                "day_of_week": d.weekday(),
                "day_name": d.strftime("%A"),
                "is_weekend": 1 if d.weekday() in [5, 6] else 0,
            })

        df_date = pd.DataFrame(date_rows)
        with self.engine.begin() as conn:
            df_date.to_sql("dim_date", conn, if_exists="append", index=False)
        logger.info(f"dim_date populated with {len(df_date)} calendar dates.")

    def populate_dim_encounter_type(self) -> None:
        """Populate care setting dimension with descriptions and clinical acuity."""
        data = [
            {"encounter_class": "ambulatory", "display_name": "Ambulatory Clinic", "setting_description": "Scheduled outpatient clinic visit", "acuity_level": "Low"},
            {"encounter_class": "wellness", "display_name": "Preventive / Wellness", "setting_description": "Annual health checkup and routine screening", "acuity_level": "Low"},
            {"encounter_class": "outpatient", "display_name": "Hospital Outpatient", "setting_description": "Specialist hospital consultation or diagnostic workup", "acuity_level": "Moderate"},
            {"encounter_class": "urgentcare", "display_name": "Urgent Care Walk-In", "setting_description": "Unscheduled episodic minor acute illness", "acuity_level": "Moderate"},
            {"encounter_class": "emergency", "display_name": "Emergency Department", "setting_description": "Acute unscheduled life-safety and trauma services", "acuity_level": "High"},
            {"encounter_class": "inpatient", "display_name": "Inpatient Hospitalization", "setting_description": "Formal hospital admission requiring bed stay", "acuity_level": "Critical"},
        ]
        df = pd.DataFrame(data)
        with self.engine.begin() as conn:
            df.to_sql("dim_encounter_type", conn, if_exists="append", index=False)
        logger.info(f"dim_encounter_type populated with {len(df)} care settings.")

    def populate_dim_condition(self) -> None:
        """Populate condition catalog dimension from conditions summary."""
        df_cond = pd.read_csv(self.data_dir / "dim_conditions_summary.csv")
        chronic_keywords = ["diabetes", "hypertension", "asthma", "bronchitis", "anemia", "prediabetes", "stroke", "infarction", "osteoarthritis"]

        cond_rows = []
        for _, r in df_cond.iterrows():
            code = str(r["CODE"])
            desc = str(r["DESCRIPTION"])
            is_chronic = 1 if any(kw in desc.lower() for kw in chronic_keywords) else 0
            category = "Cardiometabolic" if any(k in desc.lower() for k in ["diabetes", "hypertension", "infarction", "stroke"]) else "Respiratory / General"
            cond_rows.append({
                "condition_code": code,
                "condition_name": desc,
                "is_chronic": is_chronic,
                "clinical_category": category,
            })

        df_dim_cond = pd.DataFrame(cond_rows).drop_duplicates(subset=["condition_code"])
        with self.engine.begin() as conn:
            df_dim_cond.to_sql("dim_condition", conn, if_exists="append", index=False)
        logger.info(f"dim_condition populated with {len(df_dim_cond)} condition definitions.")

    def populate_all_tables(self) -> Dict[str, int]:
        """Load all analytical dimension and fact tables into database."""
        logger.info("Loading dimension and fact tables into database...")

        # 1. Schema & System Dimensions
        self.execute_schema_ddl()
        self.populate_dim_date()
        self.populate_dim_encounter_type()
        self.populate_dim_condition()

        # 2. dim_organization
        df_org = pd.read_csv(self.data_dir / "dim_organizations_enriched.csv")
        df_org_sql = df_org.rename(columns={
            "Id": "org_id",
            "NAME": "org_name",
            "CITY": "city",
            "STATE": "state",
            "ZIP": "zip",
            "PHONE": "phone",
            "REVENUE": "annual_revenue",
            "UTILIZATION": "utilization_rating",
        })[["org_id", "org_name", "city", "state", "zip", "phone", "annual_revenue", "utilization_rating"]]

        with self.engine.begin() as conn:
            df_org_sql.to_sql("dim_organization", conn, if_exists="append", index=False)

        # 3. dim_provider
        df_prov = pd.read_csv(self.data_dir / "dim_providers_enriched.csv")
        df_prov_sql = df_prov.rename(columns={
            "Id": "provider_id",
            "ORGANIZATION": "org_id",
            "NAME": "provider_name",
            "GENDER": "gender",
            "SPECIALITY": "speciality",
            "CLINICAL_DEPARTMENT": "clinical_department",
            "UTILIZATION": "historical_utilization",
        })[["provider_id", "org_id", "provider_name", "gender", "speciality", "clinical_department", "historical_utilization"]]

        with self.engine.begin() as conn:
            df_prov_sql.to_sql("dim_provider", conn, if_exists="append", index=False)

        # 4. dim_patient
        df_pt = pd.read_csv(self.data_dir / "patient_segments_kmeans.csv")
        df_pt_sql = pd.DataFrame({
            "patient_key": df_pt["PATIENT_KEY"],
            "birthdate": df_pt["BIRTHDATE"],
            "deathdate": df_pt["DEATHDATE"],
            "is_deceased": df_pt["DEATHDATE"].notnull().astype(int),
            "gender": df_pt["GENDER"],
            "race": df_pt["RACE"],
            "ethnicity": df_pt["ETHNICITY"],
            "marital": df_pt["MARITAL"],
            "city": df_pt["CITY"],
            "state": df_pt["STATE"],
            "zip": df_pt["ZIP"].astype(str),
            "annual_income": df_pt["INCOME"],
            "current_age": df_pt["CURRENT_AGE"],
            "current_age_group": df_pt["CURRENT_AGE_GROUP"],
            "cluster_id": df_pt["CLUSTER_ID"],
            "cluster_name": df_pt["CLUSTER_NAME"],
            "utilization_tier": df_pt["UTILIZATION_TIER"],
            "total_lifetime_encounters": df_pt["FREQUENCY"],
            "total_lifetime_claim_cost": df_pt["TOTAL_COST"],
        })

        with self.engine.begin() as conn:
            df_pt_sql.to_sql("dim_patient", conn, if_exists="append", index=False)

        # 5. fact_encounters
        df_enc = pd.read_csv(self.data_dir / "reencounter_analysis_30day.csv")
        df_enc["START"] = pd.to_datetime(df_enc["START"])
        df_enc["STOP"] = pd.to_datetime(df_enc["STOP"])
        date_keys = df_enc["START"].dt.strftime("%Y%m%d").astype(int)

        df_fact_enc = pd.DataFrame({
            "encounter_id": df_enc["Id"],
            "patient_key": df_enc["PATIENT_KEY"],
            "date_key": date_keys,
            "org_id": df_enc["ORGANIZATION"],
            "provider_id": df_enc["PROVIDER"],
            "encounter_class": df_enc["ENCOUNTERCLASS"],
            "payer": df_enc["PAYER"],
            "start_time": df_enc["START"].astype(str),
            "stop_time": df_enc["STOP"].astype(str),
            "start_hour": df_enc["START_HOUR"],
            "duration_minutes": df_enc["DURATION_MINUTES"],
            "duration_hours": df_enc["DURATION_HOURS"],
            "length_of_stay_days": df_enc["LENGTH_OF_STAY_DAYS"],
            "age_at_encounter": df_enc["AGE_AT_ENCOUNTER"],
            "age_group": df_enc["AGE_GROUP"],
            "base_encounter_cost": df_enc["BASE_ENCOUNTER_COST"],
            "total_claim_cost": df_enc["TOTAL_CLAIM_COST"],
            "payer_coverage": df_enc["PAYER_COVERAGE"],
            "patient_payment": df_enc["PATIENT_PAYMENT"],
            "coverage_ratio": df_enc["COVERAGE_RATIO"],
            "is_inpatient": df_enc["IS_INPATIENT"],
            "is_emergency": df_enc["IS_EMERGENCY"],
            "visit_sequence_number": df_enc["VISIT_NUMBER"],
            "re_encounter_30d": df_enc["RE_ENCOUNTER_30D"],
        })

        with self.engine.begin() as conn:
            df_fact_enc.to_sql("fact_encounters", conn, if_exists="append", index=False)

        # 6. fact_encounter_conditions
        df_cond_raw = pd.read_csv(self.data_dir / "cleaned_conditions.csv")
        valid_enc_ids = set(df_fact_enc["encounter_id"])
        df_cond_clean = df_cond_raw[df_cond_raw["ENCOUNTER"].isin(valid_enc_ids)].copy()

        df_fact_cond = pd.DataFrame({
            "id": range(1, len(df_cond_clean) + 1),
            "encounter_id": df_cond_clean["ENCOUNTER"],
            "patient_key": df_cond_clean["PATIENT_KEY"],
            "condition_code": df_cond_clean["CODE"].astype(str),
            "onset_date": df_cond_clean["START"].astype(str),
            "resolved_date": df_cond_clean["STOP"].astype(str),
        })

        with self.engine.begin() as conn:
            df_fact_cond.to_sql("fact_encounter_conditions", conn, if_exists="append", index=False)

        # 7. fact_encounter_procedures
        df_proc = pd.read_csv(self.data_dir / "cleaned_procedures.csv")
        df_proc_clean = df_proc[df_proc["ENCOUNTER"].isin(valid_enc_ids)].copy()

        df_fact_proc = pd.DataFrame({
            "procedure_id": range(1, len(df_proc_clean) + 1),
            "encounter_id": df_proc_clean["ENCOUNTER"],
            "patient_key": df_proc_clean["PATIENT_KEY"],
            "procedure_code": df_proc_clean["CODE"].astype(str),
            "procedure_name": df_proc_clean["DESCRIPTION"],
            "procedure_date": df_proc_clean["DATE"].astype(str),
            "procedure_cost": df_proc_clean["BASE_COST"],
        })

        with self.engine.begin() as conn:
            df_fact_proc.to_sql("fact_encounter_procedures", conn, if_exists="append", index=False)

        # Record counts verification
        counts = {}
        with self.engine.connect() as conn:
            for tbl in ["dim_patient", "dim_date", "dim_organization", "dim_provider", "dim_encounter_type", "dim_condition", "fact_encounters", "fact_encounter_conditions", "fact_encounter_procedures"]:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {tbl};")).scalar()
                counts[tbl] = int(res)
                logger.info(f"Verified table '{tbl}': {res:,} records.")

        return counts


def main():
    loader = DatabaseLoader()
    counts = loader.populate_all_tables()
    print("Database Loading Summary:", counts)


if __name__ == "__main__":
    main()
