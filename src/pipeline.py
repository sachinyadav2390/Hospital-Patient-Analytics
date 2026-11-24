"""
End-to-End Master Pipeline Orchestrator
Hospital Patient Analytics & Healthcare Performance Optimization

Executes all 7 core pipeline stages sequentially:
1. Data Ingestion & Schema Inventory
2. Data Cleaning & Pseudonymization
3. Feature Engineering & Clinical Metrics
4. Exploratory Data Analysis & Visualizations
5. Advanced Analytics (K-Means, Cohorts, 30-Day Re-encounters)
6. Database Star Schema Provisioning & Advanced SQL Execution
7. Production Excel Analytics & Power BI Data Model Export
"""

import sys
import time
import logging
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import DataIngestionPipeline
from src.cleaning import DataCleaningPipeline
from src.features import FeatureEngineeringPipeline
from src.eda import HealthcareEDAPipeline
from src.advanced_analytics import AdvancedAnalyticsPipeline
from src.db_loader import DatabaseLoader
from src.run_sql_queries import SQLQueryRunner
from src.generate_excel import ExcelWorkbookGenerator
from src.export_powerbi import export_powerbi_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MasterPipeline")


def run_pipeline() -> None:
    t_start = time.time()
    logger.info("=" * 80)
    logger.info("STARTING END-TO-END HOSPITAL PATIENT ANALYTICS PIPELINE")
    logger.info("=" * 80)

    # Stage 1: Ingestion
    logger.info("\n>>> STAGE 1: Data Ingestion & Schema Audit")
    DataIngestionPipeline().run()

    # Stage 2: Cleaning
    logger.info("\n>>> STAGE 2: Data Cleaning & Pseudonymization")
    DataCleaningPipeline().run()

    # Stage 3: Features
    logger.info("\n>>> STAGE 3: Feature Engineering & Metrics Derivation")
    FeatureEngineeringPipeline().run()

    # Stage 4: EDA
    logger.info("\n>>> STAGE 4: Exploratory Data Analysis & Visualizations")
    HealthcareEDAPipeline().run()

    # Stage 5: Advanced Analytics
    logger.info("\n>>> STAGE 5: Advanced Healthcare Analytics & ML Segmentation")
    AdvancedAnalyticsPipeline().run()

    # Stage 6: Database & SQL
    logger.info("\n>>> STAGE 6: Star Schema Database Provisioning & SQL Execution")
    db_loader = DatabaseLoader()
    db_loader.populate_all_tables()
    SQLQueryRunner().execute_all()

    # Stage 7: Excel & Power BI
    logger.info("\n>>> STAGE 7: Production Excel Workbook & Power BI Model Export")
    ExcelWorkbookGenerator().build_workbook()
    export_powerbi_tables()

    elapsed = round(time.time() - t_start, 2)
    logger.info("=" * 80)
    logger.info(f"END-TO-END HEALTHCARE PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s")
    logger.info("=" * 80)


if __name__ == "__main__":
    run_pipeline()
