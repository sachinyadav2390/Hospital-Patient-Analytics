"""
SQL Query Execution & Verification Engine
Hospital Patient Analytics & Healthcare Performance Optimization

Executes all 16 advanced SQL queries against the provisioned star schema,
validates output row counts and performance, and saves a summary report.
"""

import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import SQL_DIR, REPORTS_DIR
from src.db_loader import get_database_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SQLExecutionEngine")


class SQLQueryRunner:
    def __init__(self, sql_file: Path = SQL_DIR / "advanced_analytical_queries.sql", reports_dir: Path = REPORTS_DIR):
        self.sql_file = sql_file
        self.reports_dir = reports_dir
        self.engine, self.dialect = get_database_engine()

    def parse_queries(self) -> List[Dict[str, str]]:
        """Parse distinct queries from SQL script based on comments."""
        with open(self.sql_file, "r", encoding="utf-8") as f:
            content = f.read()

        import re
        # Find all queries starting with -- QUERY
        pattern = r"-- QUERY\s+(\d+):\s+([^\n\r]+)([\s\S]*?)(?=(?:-- QUERY|\Z))"
        matches = re.findall(pattern, content)

        queries = []
        for q_num, title, body in matches:
            # Strip comment lines from body
            sql_lines = [l for l in body.splitlines() if not l.strip().startswith("--")]
            sql_code = "\n".join(sql_lines).strip()
            if sql_code.endswith(";"):
                sql_code = sql_code[:-1].strip()
            if sql_code:
                queries.append({
                    "title": f"QUERY {q_num}: {title.strip()}",
                    "sql": sql_code
                })

        return queries

    def execute_all(self) -> Dict[str, Any]:
        """Execute each query, record timing, row count, and output sample."""
        queries = self.parse_queries()
        logger.info(f"Loaded {len(queries)} advanced analytical SQL queries to execute on {self.dialect.upper()}...")

        results = []
        with self.engine.connect() as conn:
            for idx, q in enumerate(queries, start=1):
                title = q["title"]
                sql_text = q["sql"]
                t0 = time.time()
                try:
                    df = pd.read_sql_query(text(sql_text), conn)
                    elapsed_ms = round((time.time() - t0) * 1000, 2)
                    sample = df.head(3).to_dict(orient="records")

                    logger.info(f"[{idx}/{len(queries)}] SUCCESS: '{title}' ({len(df)} rows, {elapsed_ms}ms)")
                    results.append({
                        "query_number": idx,
                        "title": title,
                        "status": "SUCCESS",
                        "row_count": len(df),
                        "columns": list(df.columns),
                        "execution_time_ms": elapsed_ms,
                        "sample_data": sample,
                    })
                except Exception as e:
                    logger.error(f"[{idx}/{len(queries)}] ERROR in '{title}': {e}")
                    results.append({
                        "query_number": idx,
                        "title": title,
                        "status": "ERROR",
                        "error_message": str(e),
                    })

        summary = {
            "dialect": self.dialect,
            "total_queries": len(queries),
            "successful_queries": len([r for r in results if r["status"] == "SUCCESS"]),
            "failed_queries": len([r for r in results if r["status"] == "ERROR"]),
            "query_results": results,
        }

        # Save JSON output
        json_path = self.reports_dir / "sql_query_results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # Generate Markdown Report
        md_path = self.reports_dir / "sql_analysis_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._generate_markdown(summary))

        logger.info(f"SQL execution results saved to {json_path} and {md_path}")
        return summary

    def _generate_markdown(self, summary: Dict[str, Any]) -> str:
        md = ["# Hospital Patient Analytics — Advanced SQL Execution Audit\n\n"]
        md.append(f"**Database Engine:** `{summary['dialect'].upper()}`  \n")
        md.append(f"**Total Queries Evaluated:** {summary['total_queries']} | **Passed:** {summary['successful_queries']} | **Failed:** {summary['failed_queries']}\n\n")
        md.append("| # | Analytical Query Title | Rows Returned | Latency (ms) | Status |\n")
        md.append("|:---|:---|---:|---:|:---|\n")

        for r in summary["query_results"]:
            if r["status"] == "SUCCESS":
                md.append(f"| {r['query_number']} | `{r['title']}` | {r['row_count']:,} | {r['execution_time_ms']} ms | ✅ PASS |\n")
            else:
                md.append(f"| {r['query_number']} | `{r['title']}` | ERROR | N/A | ❌ FAIL: {r.get('error_message')} |\n")

        md.append("\n## Sample Query Outputs\n\n")
        for r in summary["query_results"]:
            if r["status"] == "SUCCESS" and r["sample_data"]:
                md.append(f"### {r['title']}\n\n")
                sample_data = r["sample_data"]
                if sample_data:
                    cols = list(sample_data[0].keys())
                    header = "| " + " | ".join(cols) + " |\n"
                    separator = "| " + " | ".join(["---"] * len(cols)) + " |\n"
                    rows = []
                    for row in sample_data:
                        row_str = "| " + " | ".join([str(row.get(c, "")) for c in cols]) + " |\n"
                        rows.append(row_str)
                    md.append(header + separator + "".join(rows) + "\n\n")

        return "".join(md)


def main():
    runner = SQLQueryRunner()
    runner.execute_all()


if __name__ == "__main__":
    main()
