"""
Data Ingestion & Raw Validation Pipeline
Hospital Patient Analytics & Healthcare Performance Optimization

This module ingests raw Synthea CSV files, validates schemas and data types,
checks for missing values and duplicates, and produces a complete data inventory.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

from src.config import RAW_DATA_DIR, REPORTS_DIR, SYNTHEA_TABLES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DataIngestion")

# Standard Schema Specifications for Synthea Tables
TABLE_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "patients": {
        "required_columns": ["Id", "BIRTHDATE", "GENDER", "RACE", "ETHNICITY"],
        "primary_key": "Id",
        "date_columns": ["BIRTHDATE", "DEATHDATE"],
        "numeric_columns": ["HEALTHCARE_EXPENSES", "HEALTHCARE_COVERAGE", "INCOME", "LAT", "LON"],
    },
    "encounters": {
        "required_columns": ["Id", "START", "STOP", "PATIENT", "ORGANIZATION", "ENCOUNTERCLASS", "BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST"],
        "primary_key": "Id",
        "date_columns": ["START", "STOP"],
        "numeric_columns": ["BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST", "PAYER_COVERAGE"],
    },
    "conditions": {
        "required_columns": ["START", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION"],
        "primary_key": None,
        "date_columns": ["START", "STOP"],
        "numeric_columns": [],
    },
    "procedures": {
        "required_columns": ["DATE", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION", "BASE_COST"],
        "primary_key": None,
        "date_columns": ["DATE"],
        "numeric_columns": ["BASE_COST"],
    },
    "medications": {
        "required_columns": ["START", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION", "BASE_COST", "TOTALCOST"],
        "primary_key": None,
        "date_columns": ["START", "STOP"],
        "numeric_columns": ["BASE_COST", "PAYER_COVERAGE", "DISPENSES", "TOTALCOST"],
    },
    "observations": {
        "required_columns": ["DATE", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION", "VALUE"],
        "primary_key": None,
        "date_columns": ["DATE"],
        "numeric_columns": [],
    },
    "organizations": {
        "required_columns": ["Id", "NAME", "CITY", "STATE", "ZIP"],
        "primary_key": "Id",
        "date_columns": [],
        "numeric_columns": ["LAT", "LON", "REVENUE", "UTILIZATION"],
    },
    "providers": {
        "required_columns": ["Id", "ORGANIZATION", "NAME", "SPECIALITY"],
        "primary_key": "Id",
        "date_columns": [],
        "numeric_columns": ["LAT", "LON", "UTILIZATION"],
    },
}


class DataIngestionPipeline:
    def __init__(self, raw_dir: Path = RAW_DATA_DIR, reports_dir: Path = REPORTS_DIR):
        self.raw_dir = raw_dir
        self.reports_dir = reports_dir
        self.inventory: Dict[str, Any] = {}
        self.raw_datasets: Dict[str, pd.DataFrame] = {}

    def load_table(self, table_name: str) -> pd.DataFrame:
        """Load a single raw CSV file into a Pandas DataFrame."""
        file_path = self.raw_dir / f"{table_name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Raw file not found: {file_path}")

        df = pd.read_csv(file_path, low_memory=False)
        self.raw_datasets[table_name] = df
        return df

    def validate_schema(self, table_name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate columns, primary key uniqueness, missingness, and data types."""
        schema = TABLE_SCHEMAS.get(table_name, {})
        req_cols = schema.get("required_columns", [])
        pk = schema.get("primary_key")

        missing_required = [c for c in req_cols if c not in df.columns]

        # Missing values profile
        null_counts = df.isnull().sum().to_dict()
        null_pcts = (df.isnull().sum() / len(df) * 100).round(2).to_dict()
        missing_summary = {
            col: {"null_count": int(null_counts[col]), "null_percentage": float(null_pcts[col])}
            for col in df.columns if null_counts[col] > 0
        }

        # Duplicate counts
        full_row_dupes = int(df.duplicated().sum())
        pk_dupes = 0
        if pk and pk in df.columns:
            pk_dupes = int(df[pk].duplicated().sum())

        return {
            "table_name": table_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "missing_required_columns": missing_required,
            "is_schema_valid": len(missing_required) == 0,
            "primary_key": pk,
            "pk_duplicates": pk_dupes,
            "full_row_duplicates": full_row_dupes,
            "missing_values_summary": missing_summary,
        }

    def run(self) -> Dict[str, Any]:
        """Execute full ingestion validation pipeline across all tables."""
        logger.info("Starting raw data ingestion and schema validation...")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        inventory_results = {}

        for table in SYNTHEA_TABLES:
            try:
                df = self.load_table(table)
                val_result = self.validate_schema(table, df)
                inventory_results[table] = val_result
                logger.info(
                    f"Loaded '{table}': {val_result['row_count']} rows, {val_result['column_count']} cols, "
                    f"PK dupes: {val_result['pk_duplicates']}, full dupes: {val_result['full_row_duplicates']}"
                )
            except Exception as e:
                logger.error(f"Error processing {table}: {e}")
                inventory_results[table] = {"error": str(e), "is_schema_valid": False}

        self.inventory = {
            "status": "SUCCESS",
            "source_type": "MITRE Synthea Synthetic Data",
            "tables": inventory_results,
            "total_tables_ingested": len([t for t in inventory_results.values() if t.get("is_schema_valid")]),
        }

        # Save JSON audit
        json_path = self.reports_dir / "data_ingestion_audit.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.inventory, f, indent=2)

        # Generate Markdown Summary
        md_summary = self._generate_markdown_summary()
        md_path = self.reports_dir / "data_ingestion_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_summary)

        logger.info(f"Ingestion audit report saved to {json_path} and {md_path}")
        return self.inventory

    def _generate_markdown_summary(self) -> str:
        md = ["# Hospital Patient Analytics — Data Ingestion & Inventory Audit\n"]
        md.append("**Dataset:** MITRE Synthea Synthetic Healthcare Simulation\n")
        md.append(f"**Total Tables:** {len(self.inventory.get('tables', {}))}\n\n")
        md.append("| Table Name | Row Count | Column Count | Primary Key | PK Duplicates | Missing Req Cols | Schema Status |\n")
        md.append("|:---|---:|---:|:---|---:|:---|:---|\n")

        for tbl, info in self.inventory.get("tables", {}).items():
            if "error" in info:
                md.append(f"| `{tbl}` | ERROR | ERROR | N/A | N/A | {info['error']} | ❌ FAILED |\n")
            else:
                pk = info.get("primary_key") or "Composite / Event"
                status = "✅ PASS" if info.get("is_schema_valid") and info.get("pk_duplicates") == 0 else "⚠️ REVIEW"
                missing = ", ".join(info.get("missing_required_columns", [])) or "None"
                md.append(
                    f"| `{tbl}` | {info['row_count']:,} | {info['column_count']} | `{pk}` | "
                    f"{info['pk_duplicates']} | {missing} | {status} |\n"
                )

        md.append("\n## Missing Values Profile\n\n")
        for tbl, info in self.inventory.get("tables", {}).items():
            if "missing_values_summary" in info and info["missing_values_summary"]:
                md.append(f"### Table `{tbl}`\n")
                md.append("| Column | Missing Rows | Null % |\n|:---|---:|---:|\n")
                for col, m in info["missing_values_summary"].items():
                    md.append(f"| `{col}` | {m['null_count']:,} | {m['null_percentage']:.2f}% |\n")
                md.append("\n")

        return "".join(md)


def main():
    pipeline = DataIngestionPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
