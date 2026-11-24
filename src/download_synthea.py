"""
Synthea Healthcare Dataset Downloader & Synthetic Sample Generator
Hospital Patient Analytics & Healthcare Performance Optimization

This script acquires or generates the Synthea synthetic healthcare dataset
comprising patients, encounters, conditions, procedures, medications,
observations, organizations, and providers.

NOTICE: All data processed by this project is strictly synthetic (MITRE Synthea).
No real Protected Health Information (PHI) or real patient records are used.
"""

import os
import sys
import argparse
import logging
import zipfile
import io
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import requests

from src.config import RAW_DATA_DIR, RANDOM_STATE, SYNTHEA_DEFAULT_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SyntheaLoader")


def download_synthea_archive(url: str, output_dir: Path) -> bool:
    """Download and extract Synthea CSV zip archive from specified URL."""
    logger.info(f"Attempting to download Synthea archive from {url}...")
    try:
        response = requests.get(url, timeout=30, stream=True)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                z.extractall(output_dir)
            logger.info(f"Successfully extracted Synthea archive to {output_dir}")
            _write_notice(output_dir, source=f"Official Synthea Archive ({url})")
            return True
        else:
            logger.warning(f"Download returned status code {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"Download failed due to network or connection issue: {e}")
        return False


def generate_synthea_sample(output_dir: Path, n_patients: int = 1200, seed: int = RANDOM_STATE) -> None:
    """
    Generate a statistically coherent, schema-compliant synthetic Synthea sample dataset.
    This provides an immediate, reproducible benchmark matching the MITRE Synthea schema.
    """
    logger.info(f"Generating realistic synthetic Synthea dataset ({n_patients} patients, seed={seed})...")
    random.seed(seed)
    np.random.seed(seed)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Organizations
    org_data = [
        {"Id": str(uuid.uuid4()), "NAME": "Massachusetts General Medical Center", "ADDRESS": "55 Fruit St", "CITY": "Boston", "STATE": "MA", "ZIP": "02114", "LAT": 42.3629, "LON": -71.0694, "PHONE": "617-726-2000", "REVENUE": 24500000.0, "UTILIZATION": 880},
        {"Id": str(uuid.uuid4()), "NAME": "Brigham & Women's Regional Hospital", "ADDRESS": "75 Francis St", "CITY": "Boston", "STATE": "MA", "ZIP": "02115", "LAT": 42.3359, "LON": -71.1070, "PHONE": "617-732-5500", "REVENUE": 21000000.0, "UTILIZATION": 790},
        {"Id": str(uuid.uuid4()), "NAME": "Cambridge Community Health Alliance", "ADDRESS": "1493 Cambridge St", "CITY": "Cambridge", "STATE": "MA", "ZIP": "02139", "LAT": 42.3736, "LON": -71.1097, "PHONE": "617-665-1000", "REVENUE": 14200000.0, "UTILIZATION": 620},
        {"Id": str(uuid.uuid4()), "NAME": "Worcester Memorial Hospital", "ADDRESS": "119 Belmont St", "CITY": "Worcester", "STATE": "MA", "ZIP": "01605", "LAT": 42.2741, "LON": -71.7850, "PHONE": "508-793-6611", "REVENUE": 16500000.0, "UTILIZATION": 690},
        {"Id": str(uuid.uuid4()), "NAME": "Springfield Baystate Health Network", "ADDRESS": "759 Chestnut St", "CITY": "Springfield", "STATE": "MA", "ZIP": "01199", "LAT": 42.1228, "LON": -72.6045, "PHONE": "413-794-0000", "REVENUE": 18900000.0, "UTILIZATION": 740},
        {"Id": str(uuid.uuid4()), "NAME": "Lowell General Acute Care", "ADDRESS": "295 Varnum Ave", "CITY": "Lowell", "STATE": "MA", "ZIP": "01854", "LAT": 42.6456, "LON": -71.3323, "PHONE": "978-937-6000", "REVENUE": 11800000.0, "UTILIZATION": 510},
    ]
    df_orgs = pd.DataFrame(org_data)
    df_orgs.to_csv(output_dir / "organizations.csv", index=False)
    org_ids = df_orgs["Id"].tolist()

    # 2. Providers
    specialities = ["Internal Medicine", "Emergency Medicine", "Family Medicine", "Cardiology", "Pediatrics", "Orthopedic Surgery", "Neurology", "General Surgery"]
    prov_data = []
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]

    for i in range(48):
        prov_id = str(uuid.uuid4())
        org_id = random.choice(org_ids)
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        gender = random.choice(["M", "F"])
        spec = random.choice(specialities)
        prov_data.append({
            "Id": prov_id,
            "ORGANIZATION": org_id,
            "NAME": f"Dr. {fn} {ln}",
            "GENDER": gender,
            "SPECIALITY": spec,
            "ADDRESS": f"{random.randint(10, 999)} Health Ave",
            "CITY": "Boston",
            "STATE": "MA",
            "ZIP": "02115",
            "LAT": 42.35 + random.uniform(-0.1, 0.1),
            "LON": -71.05 + random.uniform(-0.1, 0.1),
            "UTILIZATION": random.randint(100, 1200)
        })
    df_provs = pd.DataFrame(prov_data)
    df_provs.to_csv(output_dir / "providers.csv", index=False)
    prov_ids = df_provs["Id"].tolist()

    # 3. Patients
    cities = [("Boston", "02115"), ("Cambridge", "02138"), ("Worcester", "01605"), ("Springfield", "01199"), ("Lowell", "01854"), ("Newton", "02458"), ("Somerville", "02143"), ("Quincy", "02169")]
    races = ["white", "black", "asian", "other"]
    race_weights = [0.68, 0.14, 0.10, 0.08]
    ethnicities = ["nonhispanic", "hispanic"]
    eth_weights = [0.86, 0.14]

    patient_rows = []
    base_date = datetime(2024, 12, 31)

    for i in range(n_patients):
        p_id = str(uuid.uuid4())
        gender = random.choice(["M", "F"])
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        age = int(np.clip(random.gauss(48, 22), 1, 94))
        birth_year = base_date.year - age
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birthdate = datetime(birth_year, birth_month, birth_day).strftime("%Y-%m-%d")

        # Death date (approx 4.5% mortality rate in cohort)
        deathdate = ""
        if age > 65 and random.random() < 0.10:
            death_dt = datetime(2023, random.randint(1, 12), random.randint(1, 28))
            deathdate = death_dt.strftime("%Y-%m-%d")

        city, z_code = random.choice(cities)
        race = random.choices(races, weights=race_weights)[0]
        eth = random.choices(ethnicities, weights=eth_weights)[0]
        income = int(np.clip(random.lognormvariate(10.8, 0.6), 18000, 220000))
        expenses = round(random.uniform(1500, 45000), 2)
        coverage = round(expenses * random.uniform(0.65, 0.95), 2)

        patient_rows.append({
            "Id": p_id,
            "BIRTHDATE": birthdate,
            "DEATHDATE": deathdate,
            "SSN": f"999-{random.randint(10,99)}-{random.randint(1000,9999)}",
            "DRIVERS": f"S{random.randint(10000000, 99999999)}",
            "PASSPORT": f"X{random.randint(10000000, 99999999)}",
            "PREFIX": "Mr." if gender == "M" else "Ms.",
            "FIRST": fn,
            "LAST": ln,
            "SUFFIX": "",
            "MAIDEN": ln if gender == "F" and random.random() < 0.3 else "",
            "MARITAL": random.choice(["M", "S", "D"]),
            "RACE": race,
            "ETHNICITY": eth,
            "GENDER": gender,
            "BIRTHPLACE": f"{city} MA",
            "ADDRESS": f"{random.randint(1, 899)} Maple St",
            "CITY": city,
            "STATE": "MA",
            "COUNTY": "Middlesex County",
            "ZIP": z_code,
            "LAT": 42.36 + random.uniform(-0.15, 0.15),
            "LON": -71.06 + random.uniform(-0.15, 0.15),
            "HEALTHCARE_EXPENSES": expenses,
            "HEALTHCARE_COVERAGE": coverage,
            "INCOME": income
        })

    df_patients = pd.DataFrame(patient_rows)
    df_patients.to_csv(output_dir / "patients.csv", index=False)

    # 4. Encounters
    # Realistic distributions across encounter classes
    encounter_classes = ["ambulatory", "wellness", "outpatient", "emergency", "inpatient", "urgentcare"]
    class_weights = [0.42, 0.22, 0.16, 0.10, 0.06, 0.04]

    encounter_reasons = [
        ("44054006", "Type 2 diabetes mellitus"),
        ("38341003", "Essential hypertension"),
        ("195967001", "Asthma"),
        ("59621000", "Essential hypertension (disorder)"),
        ("10509003", "Acute bronchitis"),
        ("15777000", "Prediabetes"),
        ("271737000", "Anemia"),
        ("444814009", "Viral sinusitis"),
        ("65363002", "Otitis media"),
        ("230690007", "Stroke"),
        ("22298006", "Myocardial infarction"),
        ("195662009", "Acute viral pharyngitis"),
    ]

    payers = ["Medicare", "Medicaid", "Blue Cross Blue Shield", "Harvard Pilgrim", "Tufts Health Plan", "Self-Pay"]
    payer_weights = [0.30, 0.20, 0.25, 0.12, 0.08, 0.05]

    encounters = []
    conditions = []
    procedures = []
    medications = []
    observations = []

    start_study = datetime(2021, 1, 1)
    end_study = datetime(2024, 12, 31)
    study_days = (end_study - start_study).days

    encounter_id_counter = 0

    for idx, p in df_patients.iterrows():
        p_id = p["Id"]
        p_birth = datetime.strptime(p["BIRTHDATE"], "%Y-%m-%d")
        p_death = datetime.strptime(p["DEATHDATE"], "%Y-%m-%d") if p["DEATHDATE"] else end_study

        # Determine visit frequency based on age and chronic conditions
        age = 2024 - p_birth.year
        if age < 18:
            n_enc = random.randint(1, 4)
        elif age < 50:
            n_enc = random.randint(1, 6)
        elif age < 70:
            n_enc = random.randint(2, 10)
        else:
            n_enc = random.randint(3, 14)

        # Generate timestamps
        enc_dates = []
        for _ in range(n_enc):
            day_offset = random.randint(0, min(study_days, max(1, (p_death - start_study).days)))
            enc_dt = start_study + timedelta(days=day_offset, hours=random.randint(7, 19), minutes=random.randint(0, 59))
            if enc_dt < p_death:
                enc_dates.append(enc_dt)
        enc_dates.sort()

        # Generate index encounters and subsequent readmission-like events
        for i_enc, enc_start in enumerate(enc_dates):
            encounter_id_counter += 1
            enc_id = str(uuid.uuid4())
            enc_class = random.choices(encounter_classes, weights=class_weights)[0]

            # Encounter duration
            if enc_class == "wellness":
                duration_hours = random.uniform(0.5, 1.0)
                base_cost = round(random.uniform(85.0, 160.0), 2)
            elif enc_class == "ambulatory":
                duration_hours = random.uniform(0.5, 2.5)
                base_cost = round(random.uniform(120.0, 320.0), 2)
            elif enc_class == "outpatient":
                duration_hours = random.uniform(1.0, 4.0)
                base_cost = round(random.uniform(250.0, 750.0), 2)
            elif enc_class == "urgentcare":
                duration_hours = random.uniform(1.0, 3.5)
                base_cost = round(random.uniform(180.0, 450.0), 2)
            elif enc_class == "emergency":
                duration_hours = random.uniform(2.0, 10.0)
                base_cost = round(random.uniform(850.0, 3200.0), 2)
            else: # inpatient
                duration_hours = random.uniform(24.0, 240.0) # 1 to 10 days
                base_cost = round(random.uniform(3500.0, 22000.0), 2)

            enc_stop = enc_start + timedelta(hours=duration_hours)
            total_claim_cost = round(base_cost * random.uniform(1.10, 1.45), 2)
            payer = random.choices(payers, weights=payer_weights)[0]
            coverage_rate = 0.0 if payer == "Self-Pay" else random.uniform(0.70, 0.95)
            payer_coverage = round(total_claim_cost * coverage_rate, 2)

            reason_code, reason_desc = random.choice(encounter_reasons)
            org_id = random.choice(org_ids)
            prov_id = random.choice(prov_ids)

            encounters.append({
                "Id": enc_id,
                "START": enc_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "STOP": enc_stop.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "PATIENT": p_id,
                "ORGANIZATION": org_id,
                "PROVIDER": prov_id,
                "PAYER": payer,
                "ENCOUNTERCLASS": enc_class,
                "CODE": reason_code,
                "DESCRIPTION": f"Encounter for {reason_desc}",
                "BASE_ENCOUNTER_COST": base_cost,
                "TOTAL_CLAIM_COST": total_claim_cost,
                "PAYER_COVERAGE": payer_coverage,
                "REASONCODE": reason_code,
                "REASONDESCRIPTION": reason_desc
            })

            # Conditions
            if random.random() < 0.75:
                cond_code, cond_name = random.choice(encounter_reasons)
                conditions.append({
                    "START": enc_start.strftime("%Y-%m-%d"),
                    "STOP": enc_stop.strftime("%Y-%m-%d") if random.random() < 0.3 else "",
                    "PATIENT": p_id,
                    "ENCOUNTER": enc_id,
                    "CODE": cond_code,
                    "DESCRIPTION": cond_name
                })

            # Procedures (inpatient, emergency, outpatient)
            if enc_class in ["inpatient", "emergency", "outpatient"] or random.random() < 0.25:
                proc_list = [
                    ("430193006", "Medication reconciliation", 65.0),
                    ("225285007", "Chest X-ray", 180.0),
                    ("268400002", "12 lead electrocardiogram", 145.0),
                    ("73761001", "Colonoscopy", 1250.0),
                    ("80146002", "Appendectomy", 5800.0),
                    ("232717009", "Coronary artery bypass graft", 28000.0),
                    ("410006001", "Physical therapy assessment", 120.0),
                ]
                proc_code, proc_desc, proc_cost = random.choice(proc_list)
                procedures.append({
                    "DATE": enc_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "PATIENT": p_id,
                    "ENCOUNTER": enc_id,
                    "CODE": proc_code,
                    "DESCRIPTION": proc_desc,
                    "BASE_COST": proc_cost,
                    "REASONCODE": reason_code,
                    "REASONDESCRIPTION": reason_desc
                })

            # Medications
            if random.random() < 0.60:
                med_list = [
                    ("860975", "Metformin 500 MG Oral Tablet", 15.0),
                    ("314076", "Lisinopril 10 MG Oral Tablet", 12.0),
                    ("259255", "Atorvastatin 20 MG Oral Tablet", 24.0),
                    ("245314", "Albuterol 90 MCG Inhaler", 45.0),
                    ("197361", "Amlodipine 5 MG Oral Tablet", 14.0),
                    ("310798", "Hydrochlorothiazide 25 MG Oral Tablet", 10.0),
                    ("308056", "Omeprazole 20 MG Delayed Release Capsule", 22.0),
                ]
                m_code, m_desc, m_cost = random.choice(med_list)
                dispenses = random.randint(1, 4)
                med_total = round(m_cost * dispenses, 2)
                medications.append({
                    "START": enc_start.strftime("%Y-%m-%d"),
                    "STOP": (enc_start + timedelta(days=90)).strftime("%Y-%m-%d"),
                    "PATIENT": p_id,
                    "PAYER": payer,
                    "ENCOUNTER": enc_id,
                    "CODE": m_code,
                    "DESCRIPTION": m_desc,
                    "BASE_COST": m_cost,
                    "PAYER_COVERAGE": round(med_total * coverage_rate, 2),
                    "DISPENSES": dispenses,
                    "TOTALCOST": med_total,
                    "REASONCODE": reason_code,
                    "REASONDESCRIPTION": reason_desc
                })

            # Observations (vitals & labs)
            obs_list = [
                ("8302-2", "Body Height", round(random.gauss(170, 10), 1), "cm", "numeric"),
                ("29463-7", "Body Weight", round(random.gauss(78, 16), 1), "kg", "numeric"),
                ("39156-5", "Body Mass Index", round(random.gauss(27.5, 5.2), 1), "kg/m2", "numeric"),
                ("8480-6", "Systolic Blood Pressure", round(random.gauss(126, 16), 0), "mmHg", "numeric"),
                ("8462-4", "Diastolic Blood Pressure", round(random.gauss(80, 10), 0), "mmHg", "numeric"),
                ("8867-4", "Heart rate", round(random.gauss(74, 12), 0), "/min", "numeric"),
                ("2339-0", "Glucose", round(random.gauss(102, 28), 1), "mg/dL", "numeric"),
            ]
            for o_code, o_desc, o_val, o_units, o_type in random.sample(obs_list, k=random.randint(3, 6)):
                observations.append({
                    "DATE": enc_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "PATIENT": p_id,
                    "ENCOUNTER": enc_id,
                    "CODE": o_code,
                    "DESCRIPTION": o_desc,
                    "VALUE": str(o_val),
                    "UNITS": o_units,
                    "TYPE": o_type
                })

    df_enc = pd.DataFrame(encounters)
    df_enc.to_csv(output_dir / "encounters.csv", index=False)

    df_cond = pd.DataFrame(conditions)
    df_cond.to_csv(output_dir / "conditions.csv", index=False)

    df_proc = pd.DataFrame(procedures)
    df_proc.to_csv(output_dir / "procedures.csv", index=False)

    df_med = pd.DataFrame(medications)
    df_med.to_csv(output_dir / "medications.csv", index=False)

    df_obs = pd.DataFrame(observations)
    df_obs.to_csv(output_dir / "observations.csv", index=False)

    _write_notice(output_dir, source=f"Synthea Synthetic Healthcare Generator (N={n_patients}, seed={seed})")
    logger.info(f"Sample dataset generation complete: {len(df_patients)} patients, {len(df_enc)} encounters, {len(df_cond)} conditions.")


def _write_notice(output_dir: Path, source: str) -> None:
    notice_text = f"""================================================================================
SYNTHEA SYNTHETIC HEALTHCARE DATASET NOTICE
Hospital Patient Analytics & Healthcare Performance Optimization
================================================================================
Source: {source}
Generated Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Legal & Compliance Notice:
- All data in this directory is strictly SYNTHETIC, generated following the
  MITRE Synthea™ open-source synthetic patient simulation specifications.
- This dataset contains NO real Protected Health Information (PHI) and NO
  real Personally Identifiable Information (PII) under HIPAA / HITECH.
- Any resemblance to actual living or deceased individuals, clinical events,
  or provider activities is entirely coincidental.
================================================================================
"""
    with open(output_dir / "SYNTHETIC_DATA_NOTICE.txt", "w", encoding="utf-8") as f:
        f.write(notice_text)


def main():
    parser = argparse.ArgumentParser(description="Acquire or generate Synthea synthetic healthcare dataset.")
    parser.add_argument("--download", action="store_true", help="Download official Synthea archive via URL")
    parser.add_argument("--url", default=SYNTHEA_DEFAULT_URL, help="Synthea archive URL")
    parser.add_argument("--output-dir", default=str(RAW_DATA_DIR), help="Output directory for raw CSV files")
    parser.add_argument("--generate-sample", action="store_true", help="Generate statistically coherent synthetic sample")
    parser.add_argument("--patients", type=int, default=1200, help="Number of patients for synthetic sample")
    parser.add_argument("--seed", type=int, default=RANDOM_STATE, help="Random seed for reproducibility")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)

    if args.download:
        success = download_synthea_archive(args.url, out_dir)
        if not success:
            logger.info("Falling back to synthetic sample generation...")
            generate_synthea_sample(out_dir, n_patients=args.patients, seed=args.seed)
    else:
        # Default behavior: generate reproducible standardized sample
        generate_synthea_sample(out_dir, n_patients=args.patients, seed=args.seed)


if __name__ == "__main__":
    main()
