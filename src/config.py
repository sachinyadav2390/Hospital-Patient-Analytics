"""
Hospital Patient Analytics & Healthcare Performance Optimization
Central Configuration Module
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RAW_DATA_DIR = BASE_DIR / os.getenv("DATA_RAW_DIR", "data/raw")
PROCESSED_DATA_DIR = BASE_DIR / os.getenv("DATA_PROCESSED_DIR", "data/processed")
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
EXCEL_DIR = BASE_DIR / "excel"
POWERBI_DATA_DIR = BASE_DIR / os.getenv("POWERBI_EXPORT_DIR", "powerbi/data")
SQL_DIR = BASE_DIR / "sql"
DOCS_DIR = BASE_DIR / "docs"

# Ensure directories exist
for directory in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
    EXCEL_DIR,
    POWERBI_DATA_DIR,
    SQL_DIR,
    DOCS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Configuration
DB_DIALECT = os.getenv("DB_DIALECT", "postgresql")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hospital_analytics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Fallback SQLite DB Path for local self-contained execution and testing
SQLITE_DB_PATH = BASE_DIR / "hospital_analytics.db"

# Core Pipeline Parameters
RANDOM_STATE = int(os.getenv("RANDOM_STATE", "42"))
SYNTHEA_DEFAULT_URL = "https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_csv_latest.zip"

# Core Synthea Table Manifest
SYNTHEA_TABLES = [
    "patients",
    "encounters",
    "conditions",
    "procedures",
    "medications",
    "observations",
    "organizations",
    "providers",
]
