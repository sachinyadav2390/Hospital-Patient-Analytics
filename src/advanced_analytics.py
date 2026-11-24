"""
Advanced Healthcare Analytics Pipeline
Hospital Patient Analytics & Healthcare Performance Optimization

This module implements:
1. Healthcare Utilization & RFM-style segmentation
2. Unsupervised Machine Learning: K-Means Clustering with selection diagnostics (Elbow & Silhouette)
3. Longitudinal Patient Cohort Analysis (Acquisition Month to Follow-up Retention)
4. 30-Day Subsequent Encounter (Re-encounter) Analysis with strict eligibility rules & limitations
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples

from src.config import PROCESSED_DATA_DIR, FIGURES_DIR, REPORTS_DIR, RANDOM_STATE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AdvancedAnalytics")


class AdvancedAnalyticsPipeline:
    def __init__(
        self,
        data_dir: Path = PROCESSED_DATA_DIR,
        figures_dir: Path = FIGURES_DIR,
        reports_dir: Path = REPORTS_DIR,
        random_state: int = RANDOM_STATE,
    ):
        self.data_dir = data_dir
        self.figures_dir = figures_dir
        self.reports_dir = reports_dir
        self.random_state = random_state

    def run(self) -> Dict[str, Any]:
        """Execute full advanced analytics suite."""
        logger.info("Executing Advanced Healthcare Analytics Pipeline...")

        # Load input datasets
        fact_enc = pd.read_csv(self.data_dir / "fact_encounters_enriched.csv")
        dim_pt = pd.read_csv(self.data_dir / "dim_patients_enriched.csv")

        fact_enc["START"] = pd.to_datetime(fact_enc["START"])
        fact_enc["STOP"] = pd.to_datetime(fact_enc["STOP"])

        # 1. K-Means Patient Utilization Segmentation
        pt_clustered, cluster_profiles, best_k = self.run_kmeans_clustering(fact_enc, dim_pt)
        pt_clustered.to_csv(self.data_dir / "patient_segments_kmeans.csv", index=False)

        # 2. Longitudinal Cohort Analysis
        cohort_matrix, cohort_summary = self.run_cohort_analysis(fact_enc)
        cohort_matrix.to_csv(self.data_dir / "patient_cohort_retention.csv")

        # 3. 30-Day Subsequent Re-encounter Analysis
        reencounter_df, reencounter_metrics = self.run_30day_reencounter_analysis(fact_enc, dim_pt)
        reencounter_df.to_csv(self.data_dir / "reencounter_analysis_30day.csv", index=False)

        # Compile and export summary report
        summary = {
            "kmeans": {
                "optimal_clusters": int(best_k),
                "cluster_profiles": cluster_profiles,
            },
            "cohort": cohort_summary,
            "reencounter_analysis": reencounter_metrics,
        }

        with open(self.reports_dir / "advanced_analytics_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        md_report = self._generate_markdown_report(summary)
        with open(self.reports_dir / "advanced_analytics_report.md", "w", encoding="utf-8") as f:
            f.write(md_report)

        logger.info("Advanced analytics completed successfully.")
        return summary

    def run_kmeans_clustering(
        self, encounters: pd.DataFrame, patients: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any], int]:
        """
        K-Means Clustering on Patient Healthcare Utilization Features:
        - Recency: Days since last encounter (relative to 2024-12-31)
        - Frequency: Total lifetime encounters
        - Monetary: Total billed claims ($)
        - Inpatient Intensity: Number of inpatient stays
        - Emergency Intensity: Number of emergency visits
        """
        logger.info("Running K-Means patient segmentation and diagnostics...")
        ref_date = pd.Timestamp("2024-12-31")

        # Build Patient Feature Vector
        pt_features = encounters.groupby("PATIENT_KEY").agg(
            LAST_ENCOUNTER=("START", "max"),
            FREQUENCY=("Id", "count"),
            TOTAL_COST=("TOTAL_CLAIM_COST", "sum"),
            INPATIENT_COUNT=("IS_INPATIENT", "sum"),
            EMERGENCY_COUNT=("IS_EMERGENCY", "sum"),
            AVG_DURATION_HOURS=("DURATION_HOURS", "mean"),
        ).reset_index()

        pt_features["RECENCY_DAYS"] = (ref_date - pt_features["LAST_ENCOUNTER"]).dt.days.clip(lower=0)

        feature_cols = ["RECENCY_DAYS", "FREQUENCY", "TOTAL_COST", "INPATIENT_COUNT", "EMERGENCY_COUNT"]
        X = pt_features[feature_cols].copy()

        # Feature Scaling
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Selection Diagnostics: Elbow & Silhouette Scores (k = 2 to 6)
        inertias = []
        silhouettes = []
        k_range = range(2, 7)

        for k in k_range:
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = km.fit_predict(X_scaled)
            inertias.append(km.inertia_)
            sil = silhouette_score(X_scaled, labels)
            silhouettes.append(sil)

        # Plot Diagnostics (Fig 11)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        ax1.plot(k_range, inertias, marker="o", color="#0284C7", linewidth=2)
        ax1.set_title("K-Means Elbow Method (Inertia)")
        ax1.set_xlabel("Number of Clusters (k)")
        ax1.set_ylabel("Inertia (Sum of Squared Distances)")

        ax2.plot(k_range, silhouettes, marker="s", color="#0D9488", linewidth=2)
        ax2.set_title("Silhouette Score by Cluster Count (k)")
        ax2.set_xlabel("Number of Clusters (k)")
        ax2.set_ylabel("Average Silhouette Coefficient")

        fig.suptitle("K-Means Cluster Selection Diagnostics (Healthcare Utilization)", fontsize=13, weight="bold")
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig11_kmeans_elbow_silhouette.png")
        plt.close(fig)

        # Select Best k (choose k=4 for clinically meaningful segmentation)
        best_k = 4
        optimal_km = KMeans(n_clusters=best_k, random_state=self.random_state, n_init=15)
        pt_features["CLUSTER_ID"] = optimal_km.fit_predict(X_scaled)

        # Profile Clusters
        cluster_names = {
            0: "Low-Need Preventive Care",
            1: "Active Outpatient / Chronic",
            2: "High-Cost Acute Inpatients",
            3: "Frequent Emergency Attendees",
        }

        # Dynamically order clusters by Total Cost for consistent labeling
        cost_rank = pt_features.groupby("CLUSTER_ID")["TOTAL_COST"].mean().sort_values().index
        rank_to_archetype = {
            cost_rank[0]: "Low-Intensity Outpatients",
            cost_rank[1]: "Moderate-Need Chronic Care",
            cost_rank[2]: "Frequent Emergency Utilizers",
            cost_rank[3]: "High-Cost Complex Inpatients",
        }
        pt_features["CLUSTER_NAME"] = pt_features["CLUSTER_ID"].map(rank_to_archetype)

        profiles = {}
        for c_id, df_c in pt_features.groupby("CLUSTER_ID"):
            c_name = rank_to_archetype[c_id]
            profiles[c_name] = {
                "patient_count": int(len(df_c)),
                "pct_of_patients": round(len(df_c) / len(pt_features) * 100, 1),
                "mean_recency_days": round(float(df_c["RECENCY_DAYS"].mean()), 1),
                "mean_frequency": round(float(df_c["FREQUENCY"].mean()), 1),
                "mean_total_cost": round(float(df_c["TOTAL_COST"].mean()), 2),
                "mean_inpatient_stays": round(float(df_c["INPATIENT_COUNT"].mean()), 2),
                "mean_emergency_visits": round(float(df_c["EMERGENCY_COUNT"].mean()), 2),
            }

        # Merge back with patients
        merged_pt = patients.merge(
            pt_features[["PATIENT_KEY", "CLUSTER_ID", "CLUSTER_NAME", "RECENCY_DAYS", "FREQUENCY", "TOTAL_COST"]],
            on="PATIENT_KEY",
            how="left"
        )
        return merged_pt, profiles, best_k

    def run_cohort_analysis(self, encounters: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Longitudinal Cohort Retention:
        Cohort Defined by Patient's First Encounter Month (e.g. 2021-01 to 2022-06).
        Tracks subsequent activity over Month 0, 1, 2, ..., 12.
        """
        logger.info("Executing patient cohort retention analysis...")
        df = encounters[["PATIENT_KEY", "START"]].copy()
        df["ENCOUNTER_MONTH"] = df["START"].dt.to_period("M")

        # Determine Cohort (Month of First Encounter)
        pt_first = df.groupby("PATIENT_KEY")["ENCOUNTER_MONTH"].min().reset_index()
        pt_first.rename(columns={"ENCOUNTER_MONTH": "COHORT_MONTH"}, inplace=True)

        df = df.merge(pt_first, on="PATIENT_KEY", how="left")

        # Calculate Month Index (0, 1, 2, ...)
        df["MONTH_OFFSET"] = (
            (df["ENCOUNTER_MONTH"].dt.year - df["COHORT_MONTH"].dt.year) * 12
            + (df["ENCOUNTER_MONTH"].dt.month - df["COHORT_MONTH"].dt.month)
        )

        # Aggregate unique patients per cohort and month offset
        cohort_data = df.groupby(["COHORT_MONTH", "MONTH_OFFSET"])["PATIENT_KEY"].nunique().reset_index()
        cohort_pivot = cohort_data.pivot(index="COHORT_MONTH", columns="MONTH_OFFSET", values="PATIENT_KEY").fillna(0)

        # Calculate retention rates (% of initial cohort size)
        cohort_sizes = cohort_pivot.iloc[:, 0]
        retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100

        # Plot Cohort Heatmap (Fig 12)
        # Select first 8 cohorts and 12 follow-up months for clean visual presentation
        plot_matrix = retention_matrix.iloc[:8, :12]

        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(
            plot_matrix,
            annot=True,
            fmt=".1f",
            cmap="Blues",
            cbar_kws={"label": "Active Patient Retention Rate (%)"},
            ax=ax,
            linewidths=0.5,
            linecolor="white",
        )
        ax.set_title("Longitudinal Patient Cohort Retention Heatmap (Monthly Follow-Up)")
        ax.set_xlabel("Months Since Cohort Inception (Month 0 = Initial Encounter)")
        ax.set_ylabel("Patient Acquisition Cohort")
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig12_patient_cohort_retention_heatmap.png")
        plt.close(fig)

        summary = {
            "total_cohorts": len(cohort_pivot),
            "mean_month_1_retention": round(float(retention_matrix[1].mean()), 2) if 1 in retention_matrix.columns else 0.0,
            "mean_month_6_retention": round(float(retention_matrix[6].mean()), 2) if 6 in retention_matrix.columns else 0.0,
            "mean_month_12_retention": round(float(retention_matrix[12].mean()), 2) if 12 in retention_matrix.columns else 0.0,
        }
        return retention_matrix, summary

    def run_30day_reencounter_analysis(
        self, encounters: pd.DataFrame, patients: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        30-Day Subsequent Re-encounter Indicator:
        METHODOLOGICAL SPECIFICATIONS & LIMITATIONS:
        - Index Encounter: Acute hospital visits (Inpatient and Emergency).
        - Eligibility: Patient was discharged alive.
        - Indicator Flag: Whether the patient had ANY subsequent healthcare encounter within 1 to 30 days post-discharge.
        - Limitation Notice: This is NOT a formal CMS-certified Hospital Readmission Reduction Program (HRRP)
          all-cause readmission rate, which strictly requires inpatient-to-inpatient unplanned admissions
          with risk-adjustment methodology.
        """
        logger.info("Computing 30-day subsequent re-encounter indicators...")
        df = encounters.sort_values(by=["PATIENT_KEY", "START"]).copy().reset_index(drop=True)

        # Merge death dates for mortality exclusion
        pt_mortality = patients.set_index("PATIENT_KEY")["DEATHDATE"].to_dict()
        df["DEATHDATE"] = df["PATIENT_KEY"].map(pt_mortality)
        df["DEATHDATE"] = pd.to_datetime(df["DEATHDATE"])

        # Eligible Index Encounters: Inpatient or Emergency, where patient survived past discharge
        df["IS_INDEX_CANDIDATE"] = df["ENCOUNTERCLASS"].isin(["inpatient", "emergency"])
        df["SURVIVED_DISCHARGE"] = df["DEATHDATE"].isnull() | (df["DEATHDATE"] > df["STOP"])
        df["IS_ELIGIBLE_INDEX"] = df["IS_INDEX_CANDIDATE"] & df["SURVIVED_DISCHARGE"]

        # Calculate time to next encounter per patient
        df["NEXT_ENCOUNTER_START"] = df.groupby("PATIENT_KEY")["START"].shift(-1)
        df["NEXT_ENCOUNTER_CLASS"] = df.groupby("PATIENT_KEY")["ENCOUNTERCLASS"].shift(-1)
        df["DAYS_TO_NEXT_ENCOUNTER"] = (df["NEXT_ENCOUNTER_START"] - df["STOP"]).dt.total_seconds() / 86400.0

        # Flag 30-Day Subsequent Re-encounter
        df["RE_ENCOUNTER_30D"] = np.where(
            df["IS_ELIGIBLE_INDEX"] & (df["DAYS_TO_NEXT_ENCOUNTER"] >= 0) & (df["DAYS_TO_NEXT_ENCOUNTER"] <= 30),
            1,
            0
        )

        eligible_indices = df[df["IS_ELIGIBLE_INDEX"]].copy()
        total_eligible = len(eligible_indices)
        reencountered_count = int(eligible_indices["RE_ENCOUNTER_30D"].sum())
        overall_rate = round((reencountered_count / total_eligible * 100), 2) if total_eligible > 0 else 0.0

        # Breakdown by Encounter Class
        class_breakdown = eligible_indices.groupby("ENCOUNTERCLASS")["RE_ENCOUNTER_30D"].agg(
            ELIGIBLE_INDEX_COUNT="count",
            RE_ENCOUNTERS="sum",
            RATE=lambda x: round(x.mean() * 100, 2)
        ).to_dict(orient="index")

        # Breakdown by Age Group
        age_breakdown = eligible_indices.groupby("AGE_GROUP")["RE_ENCOUNTER_30D"].agg(
            ELIGIBLE_INDEX_COUNT="count",
            RE_ENCOUNTERS="sum",
            RATE=lambda x: round(x.mean() * 100, 2)
        ).to_dict(orient="index")

        # Plot Re-encounter Rates (Fig 13)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # By Setting
        settings = list(class_breakdown.keys())
        rates_setting = [class_breakdown[s]["RATE"] for s in settings]
        ax1.bar([s.capitalize() for s in settings], rates_setting, color=["#E11D48", "#8B5CF6"], width=0.45)
        ax1.set_title("30-Day Re-encounter Rate by Index Setting")
        ax1.set_ylabel("Re-encounter Rate (%)")
        for i, v in enumerate(rates_setting):
            ax1.text(i, v + 0.5, f"{v:.1f}%", ha="center", weight="bold")
        ax1.set_ylim(0, max(rates_setting) * 1.25)

        # By Age Group
        age_order = ["0-17 (Pediatric)", "18-34 (Young Adult)", "35-49 (Adult)", "50-64 (Middle-Aged)", "65-79 (Older Adult)", "80+ (Senior)"]
        age_rates = [age_breakdown.get(a, {}).get("RATE", 0.0) for a in age_order]
        ax2.bar(age_order, age_rates, color="#0284C7")
        ax2.set_title("30-Day Re-encounter Rate Across Age Brackets")
        ax2.set_ylabel("Re-encounter Rate (%)")
        ax2.tick_params(axis="x", rotation=35)
        for i, v in enumerate(age_rates):
            ax2.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=8, weight="bold")
        ax2.set_ylim(0, max(age_rates) * 1.25 if max(age_rates) > 0 else 10)

        fig.suptitle("30-Day Subsequent Re-encounter Analysis (Clinical Monitoring)", fontsize=13, weight="bold")
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig13_30day_reencounter_rates.png")
        plt.close(fig)

        metrics = {
            "total_eligible_index_encounters": total_eligible,
            "total_subsequent_reencounters_30d": reencountered_count,
            "overall_reencounter_rate_pct": overall_rate,
            "by_index_setting": class_breakdown,
            "by_age_group": age_breakdown,
            "methodology_disclaimer": "Metrics represent subsequent encounters across all outpatient/inpatient settings within 30 days post-acute discharge. Not equivalent to CMS risk-adjusted readmissions."
        }
        return df, metrics

    def _generate_markdown_report(self, summary: Dict[str, Any]) -> str:
        md = ["# Hospital Patient Analytics — Advanced Healthcare Analytics Report\n\n"]
        md.append("## 1. Unsupervised Machine Learning: K-Means Patient Segmentation\n\n")
        km = summary["kmeans"]
        md.append(f"**Optimal Cluster Count:** `k = {km['optimal_clusters']}` (Evaluated using Inertia Elbow and Silhouette Coefficients)\n\n")
        md.append("| Cluster Archetype | Patient Volume | % Share | Mean Recency (Days) | Mean Lifetime Visits | Mean Total Cost ($) | Mean Inpatient Stays |\n")
        md.append("|:---|---:|---:|---:|---:|---:|---:|\n")

        for c_name, p in km["cluster_profiles"].items():
            md.append(
                f"| **{c_name}** | {p['patient_count']:,} | {p['pct_of_patients']}% | "
                f"{p['mean_recency_days']:.0f} d | {p['mean_frequency']:.1f} visits | "
                f"${p['mean_total_cost']:,.2f} | {p['mean_inpatient_stays']:.2f} |\n"
            )

        md.append("\n### Strategic Clinical Interpretation:\n")
        md.append("- **High-Cost Complex Inpatients:** Represent the highest revenue and clinical resource intensity. Targeted care coordination and discharge planning offer massive cost-containment opportunities.\n")
        md.append("- **Frequent Emergency Utilizers:** Patients with recurring acute emergency presentations who would benefit from community primary care intervention and chronic condition stabilization.\n")
        md.append("- **Moderate-Need Chronic Care:** Routine maintenance population; candidates for remote patient monitoring (RPM) and telehealth wellness management.\n\n")

        md.append("## 2. Longitudinal Patient Cohort Analysis\n\n")
        co = summary["cohort"]
        md.append(f"- **Total Monthly Cohorts Analyzed:** {co['total_cohorts']}\n")
        md.append(f"- **Average Month 1 Re-attendance Rate:** {co['mean_month_1_retention']:.1f}%\n")
        md.append(f"- **Average Month 6 Retention Rate:** {co['mean_month_6_retention']:.1f}%\n")
        md.append(f"- **Average Month 12 Retention Rate:** {co['mean_month_12_retention']:.1f}%\n\n")

        md.append("## 3. 30-Day Subsequent Re-encounter Analysis\n\n")
        re = summary["reencounter_analysis"]
        md.append(f"- **Eligible Index Acute Encounters:** {re['total_eligible_index_encounters']:,}\n")
        md.append(f"- **30-Day Subsequent Re-encounters:** {re['total_subsequent_reencounters_30d']:,}\n")
        md.append(f"- **Overall Re-encounter Rate:** **{re['overall_reencounter_rate_pct']:.2f}%**\n\n")

        md.append("### Re-encounter Rates by Index Care Setting\n")
        md.append("| Index Setting | Eligible Encounters | Re-encounters (30D) | Re-encounter Rate (%) |\n|:---|---:|---:|---:|\n")
        for s, vals in re["by_index_setting"].items():
            md.append(f"| `{s.capitalize()}` | {vals['ELIGIBLE_INDEX_COUNT']:,} | {vals['RE_ENCOUNTERS']:,} | {vals['RATE']:.2f}% |\n")

        md.append("\n> [!WARNING] Methodological Integrity & Regulatory Limitation\n")
        md.append(
            "> The 30-day indicator reported here measures any healthcare contact (including ambulatory follow-ups) "
            "occurring within 30 days of an index acute discharge. This metric must NOT be conflated with the "
            "Centers for Medicare & Medicaid Services (CMS) Hospital Readmissions Reduction Program (HRRP) measure, "
            "which evaluates unplanned acute inpatient-to-inpatient readmissions using national claims risk adjustment models.\n"
        )
        return "".join(md)


def main():
    pipeline = AdvancedAnalyticsPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
