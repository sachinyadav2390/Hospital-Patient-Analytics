"""
Power BI Table Exporter & Data Model Provisioner
Hospital Patient Analytics & Healthcare Performance Optimization

Exports normalized, clean dimension and fact tables formatted for direct
Power BI Desktop ingestion.
"""

import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import text

from src.config import POWERBI_DATA_DIR
from src.db_loader import get_database_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PowerBIExporter")


def export_powerbi_tables() -> None:
    """Read star schema tables from database and export as Power BI-ready CSVs."""
    POWERBI_DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine, dialect = get_database_engine()

    tables = [
        ("dim_patient", "Dim_Patient.csv"),
        ("dim_date", "Dim_Date.csv"),
        ("dim_encounter_type", "Dim_Encounter_Type.csv"),
        ("dim_organization", "Dim_Organization.csv"),
        ("dim_provider", "Dim_Provider.csv"),
        ("dim_condition", "Dim_Condition.csv"),
        ("fact_encounters", "Fact_Encounters.csv"),
        ("fact_encounter_conditions", "Fact_Encounter_Conditions.csv"),
        ("fact_encounter_procedures", "Fact_Encounter_Procedures.csv"),
    ]

    logger.info(f"Exporting {len(tables)} tables to {POWERBI_DATA_DIR}...")
    with engine.connect() as conn:
        for tbl_name, out_file in tables:
            df = pd.read_sql_table(tbl_name, conn)
            out_path = POWERBI_DATA_DIR / out_file
            df.to_csv(out_path, index=False)
            logger.info(f"Exported '{tbl_name}' -> {out_file} ({len(df):,} rows)")

    logger.info("All Power BI tables exported successfully.")


if __name__ == "__main__":
    export_powerbi_tables()
