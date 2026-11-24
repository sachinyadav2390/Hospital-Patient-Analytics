"""
Pytest Fixtures for Hospital Patient Analytics QA Suite
"""

import pytest
import pandas as pd
from pathlib import Path

from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, POWERBI_DATA_DIR, SQLITE_DB_PATH
from src.db_loader import get_database_engine


@pytest.fixture(scope="session")
def processed_dir() -> Path:
    return PROCESSED_DATA_DIR


@pytest.fixture(scope="session")
def raw_dir() -> Path:
    return RAW_DATA_DIR


@pytest.fixture(scope="session")
def powerbi_dir() -> Path:
    return POWERBI_DATA_DIR


@pytest.fixture(scope="session")
def db_engine():
    engine, _ = get_database_engine()
    return engine


@pytest.fixture(scope="session")
def clean_encounters(processed_dir) -> pd.DataFrame:
    df = pd.read_csv(processed_dir / "reencounter_analysis_30day.csv")
    df["START"] = pd.to_datetime(df["START"])
    df["STOP"] = pd.to_datetime(df["STOP"])
    return df


@pytest.fixture(scope="session")
def clean_patients(processed_dir) -> pd.DataFrame:
    df = pd.read_csv(processed_dir / "patient_segments_kmeans.csv")
    df["BIRTHDATE"] = pd.to_datetime(df["BIRTHDATE"])
    return df
