"""
Feature Engineering & Healthcare Metrics Pipeline
Hospital Patient Analytics & Healthcare Performance Optimization

This module derives:
1. Exact patient age at encounter from birthdate
2. Age tiers (Pediatric, Young Adult, Adult, Middle-Aged, Older Adult, Senior)
3. Date/calendar dimensions (Year, Quarter, Month, Day of week, Weekend)
4. Encounter duration in hours, minutes, and length of stay (days)
5. Clear separation between Encounter Setting (Class) and Clinical Department
6. Strict financial distinction: Gross Billed Claim Cost, Payer Coverage, Patient Out-of-Pocket Payment
7. Patient-level cumulative visit frequency and utilization tiers
"""

import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np

from src.config import PROCESSED_DATA_DIR, REPORTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FeatureEngineering")

# Mapping Provider Specialities to Functional Clinical Departments
SPECIALTY_TO_DEPARTMENT = {
    "Internal Medicine": "Department of Internal Medicine",
    "Emergency Medicine": "Emergency Services",
    "Cardiology": "Heart & Vascular Institute",
    "Pediatrics": "Children's Health Services",
    "General Surgery": "Surgical Services",
    "Orthopedic Surgery": "Orthopedic & Musculoskeletal Care",
    "Neurology": "Neurological Sciences",
    "Family Medicine": "Primary & Community Medicine",
}


def assign_age_group(age: float) -> str:
    """Categorize patient age into standardized healthcare demographic brackets."""
    if pd.isna(age):
        return "Unknown"
    elif age < 18:
        return "0-17 (Pediatric)"
    elif age < 35:
        return "18-34 (Young Adult)"
    elif age < 50:
        return "35-49 (Adult)"
    elif age < 65:
        return "50-64 (Middle-Aged)"
    elif age < 80:
        return "65-79 (Older Adult)"
    else:
        return "80+ (Senior)"


def assign_utilization_tier(visits: int) -> str:
    """Classify patient historical healthcare utilization."""
    if visits <= 1:
        return "1 Visit (Single)"
    elif visits <= 4:
        return "2-4 Visits (Occasional)"
    elif visits <= 9:
        return "5-9 Visits (Frequent)"
    else:
        return "10+ Visits (High Utilizer)"


class FeatureEngineeringPipeline:
    def __init__(self, data_dir: Path = PROCESSED_DATA_DIR, reports_dir: Path = REPORTS_DIR):
        self.data_dir = data_dir
        self.reports_dir = reports_dir

    def run(self) -> Dict[str, Any]:
        """Execute full feature engineering workflow."""
        logger.info("Executing feature engineering pipeline...")

        # Load cleaned datasets
        patients = pd.read_csv(self.data_dir / "cleaned_patients.csv")
        encounters = pd.read_csv(self.data_dir / "cleaned_encounters.csv")
        providers = pd.read_csv(self.data_dir / "cleaned_providers.csv")
        organizations = pd.read_csv(self.data_dir / "cleaned_organizations.csv")
        conditions = pd.read_csv(self.data_dir / "cleaned_conditions.csv")

        # Parse Datetime Fields and harmonize timezone awareness (convert to tz-naive)
        patients["BIRTHDATE"] = pd.to_datetime(patients["BIRTHDATE"]).dt.tz_localize(None)
        encounters["START"] = pd.to_datetime(encounters["START"]).dt.tz_localize(None)
        encounters["STOP"] = pd.to_datetime(encounters["STOP"]).dt.tz_localize(None)

        # 1. Merge Patient Demographics into Encounters for exact age at encounter
        pt_lookup = patients[["PATIENT_KEY", "BIRTHDATE", "GENDER", "RACE", "ETHNICITY", "CITY", "STATE", "ZIP", "INCOME"]].copy()
        enc_merged = encounters.merge(pt_lookup, on="PATIENT_KEY", how="left")

        # Exact Age at Encounter (accounting for leap years)
        enc_merged["AGE_AT_ENCOUNTER"] = (
            (enc_merged["START"] - enc_merged["BIRTHDATE"]).dt.days / 365.25
        ).clip(lower=0.0).round(1)
        enc_merged["AGE_GROUP"] = enc_merged["AGE_AT_ENCOUNTER"].apply(assign_age_group)

        # 2. Calendar and Time Features
        enc_merged["ENCOUNTER_YEAR"] = enc_merged["START"].dt.year
        enc_merged["ENCOUNTER_QUARTER"] = enc_merged["START"].dt.to_period("Q").astype(str)
        enc_merged["ENCOUNTER_MONTH"] = enc_merged["START"].dt.to_period("M").astype(str)
        enc_merged["ENCOUNTER_DATE"] = enc_merged["START"].dt.strftime("%Y-%m-%d")
        enc_merged["DAY_OF_WEEK"] = enc_merged["START"].dt.day_name()
        enc_merged["IS_WEEKEND"] = enc_merged["START"].dt.dayofweek.isin([5, 6]).astype(int)
        enc_merged["START_HOUR"] = enc_merged["START"].dt.hour

        # 3. Encounter Duration and Operational Metrics
        enc_merged["DURATION_MINUTES"] = (
            (enc_merged["STOP"] - enc_merged["START"]).dt.total_seconds() / 60.0
        ).clip(lower=15.0).round(1)
        enc_merged["DURATION_HOURS"] = (enc_merged["DURATION_MINUTES"] / 60.0).round(2)
        enc_merged["LENGTH_OF_STAY_DAYS"] = (
            (enc_merged["STOP"] - enc_merged["START"]).dt.total_seconds() / 86400.0
        ).clip(lower=0.0).round(2)

        enc_merged["IS_INPATIENT"] = (enc_merged["ENCOUNTERCLASS"] == "inpatient").astype(int)
        enc_merged["IS_EMERGENCY"] = (enc_merged["ENCOUNTERCLASS"] == "emergency").astype(int)

        # 4. Clinical Department Separation (from Provider Specialty)
        prov_dept_map = providers.set_index("Id")["SPECIALITY"].map(SPECIALTY_TO_DEPARTMENT).to_dict()
        enc_merged["CLINICAL_DEPARTMENT"] = enc_merged["PROVIDER"].map(prov_dept_map).fillna("General Medicine Services")

        # 5. Financial & Revenue Metrics
        # Clarifying Billed Claims vs Payer Coverage vs Patient Payment
        enc_merged["TOTAL_CLAIM_COST"] = enc_merged["TOTAL_CLAIM_COST"].round(2)
        enc_merged["PAYER_COVERAGE"] = enc_merged["PAYER_COVERAGE"].round(2)
        enc_merged["PATIENT_PAYMENT"] = (
            enc_merged["TOTAL_CLAIM_COST"] - enc_merged["PAYER_COVERAGE"]
        ).clip(lower=0.0).round(2)
        enc_merged["COVERAGE_RATIO"] = np.where(
            enc_merged["TOTAL_CLAIM_COST"] > 0,
            (enc_merged["PAYER_COVERAGE"] / enc_merged["TOTAL_CLAIM_COST"]).clip(0.0, 1.0).round(4),
            0.0
        )

        # 6. Patient Historical Visit Sequence & Frequency
        enc_merged = enc_merged.sort_values(by=["PATIENT_KEY", "START"]).reset_index(drop=True)
        enc_merged["VISIT_NUMBER"] = enc_merged.groupby("PATIENT_KEY").cumcount() + 1
        total_visits_per_pt = enc_merged.groupby("PATIENT_KEY")["Id"].transform("count")
        enc_merged["PATIENT_TOTAL_VISITS"] = total_visits_per_pt
        enc_merged["UTILIZATION_TIER"] = enc_merged["PATIENT_TOTAL_VISITS"].apply(assign_utilization_tier)

        # 7. Patient Summary Dataset (Enriched Demographics & Lifelong Metrics)
        pt_summary = enc_merged.groupby("PATIENT_KEY").agg(
            TOTAL_ENCOUNTERS=("Id", "count"),
            FIRST_ENCOUNTER=("START", "min"),
            LAST_ENCOUNTER=("START", "max"),
            TOTAL_CLAIM_COST=("TOTAL_CLAIM_COST", "sum"),
            TOTAL_PAYER_COVERAGE=("PAYER_COVERAGE", "sum"),
            TOTAL_PATIENT_PAYMENT=("PATIENT_PAYMENT", "sum"),
            AVG_ENCOUNTER_DURATION_HOURS=("DURATION_HOURS", "mean"),
            INPATIENT_ADMISSIONS=("IS_INPATIENT", "sum"),
            EMERGENCY_VISITS=("IS_EMERGENCY", "sum"),
        ).reset_index()

        pt_enriched = patients.merge(pt_summary, on="PATIENT_KEY", how="left")
        pt_enriched["CURRENT_AGE"] = (
            (pd.Timestamp("2024-12-31") - pt_enriched["BIRTHDATE"]).dt.days / 365.25
        ).clip(lower=0.0).round(1)
        pt_enriched["CURRENT_AGE_GROUP"] = pt_enriched["CURRENT_AGE"].apply(assign_age_group)
        pt_enriched["UTILIZATION_TIER"] = pt_enriched["TOTAL_ENCOUNTERS"].fillna(0).astype(int).apply(assign_utilization_tier)

        # 8. Save Enriched Datasets
        fact_encounters_path = self.data_dir / "fact_encounters_enriched.csv"
        enc_merged.to_csv(fact_encounters_path, index=False)

        dim_patients_path = self.data_dir / "dim_patients_enriched.csv"
        pt_enriched.to_csv(dim_patients_path, index=False)

        # Enriched Providers with Department
        providers["CLINICAL_DEPARTMENT"] = providers["SPECIALITY"].map(SPECIALTY_TO_DEPARTMENT).fillna("General Medicine Services")
        providers.to_csv(self.data_dir / "dim_providers_enriched.csv", index=False)

        # Enriched Organizations
        organizations.to_csv(self.data_dir / "dim_organizations_enriched.csv", index=False)

        # Condition Frequency Summary
        cond_summary = conditions.groupby(["CODE", "DESCRIPTION"]).agg(
            TOTAL_DIAGNOSES=("START", "count"),
            UNIQUE_PATIENTS=("PATIENT_KEY", "nunique")
        ).reset_index().sort_values(by="TOTAL_DIAGNOSES", ascending=False)
        cond_summary.to_csv(self.data_dir / "dim_conditions_summary.csv", index=False)

        logger.info(f"Feature engineering completed: {len(enc_merged)} encounters enriched, {len(pt_enriched)} patients enriched.")
        return {
            "total_encounters": len(enc_merged),
            "total_patients": len(pt_enriched),
            "total_conditions": len(conditions),
            "date_range": (enc_merged["START"].min().strftime("%Y-%m-%d"), enc_merged["START"].max().strftime("%Y-%m-%d")),
            "mean_duration_hours": float(enc_merged["DURATION_HOURS"].mean()),
            "total_claim_revenue": float(enc_merged["TOTAL_CLAIM_COST"].sum()),
        }


def main():
    pipeline = FeatureEngineeringPipeline()
    metrics = pipeline.run()
    print("Feature Engineering Metrics Summary:", metrics)


if __name__ == "__main__":
    main()
