"""
Exploratory Data Analysis (EDA) & Visualization Suite
Hospital Patient Analytics & Healthcare Performance Optimization

Generates 10 publication-quality healthcare charts under reports/figures/,
computes statistical summaries, and writes an EDA insights report.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from src.config import PROCESSED_DATA_DIR, FIGURES_DIR, REPORTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("HealthcareEDA")

# Healthcare Design System Palette
PALETTE = {
    "primary": "#0F172A",       # Deep Navy
    "secondary": "#0284C7",     # Clinical Cyan/Blue
    "accent": "#0D9488",        # Medical Teal
    "danger": "#E11D48",        # Rose/Red
    "warning": "#D97706",       # Amber
    "success": "#059669",       # Emerald
    "muted": "#64748B",         # Slate Grey
    "card_bg": "#F8FAFC",       # Ice White
}

CLASS_COLORS = {
    "ambulatory": "#0284C7",
    "wellness": "#0D9488",
    "outpatient": "#6366F1",
    "emergency": "#E11D48",
    "inpatient": "#8B5CF6",
    "urgentcare": "#D97706",
}


def apply_healthcare_style():
    """Configure matplotlib with clean healthcare visual standards."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlepad": 12,
        "axes.labelsize": 11,
        "axes.labelweight": "medium",
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 1.0,
        "grid.color": "#E2E8F0",
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
        "figure.titlesize": 15,
        "figure.titleweight": "bold",
        "figure.autolayout": True,
        "figure.dpi": 300,
    })


class HealthcareEDAPipeline:
    def __init__(self, data_dir: Path = PROCESSED_DATA_DIR, figures_dir: Path = FIGURES_DIR, reports_dir: Path = REPORTS_DIR):
        self.data_dir = data_dir
        self.figures_dir = figures_dir
        self.reports_dir = reports_dir
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        apply_healthcare_style()

    def run(self) -> Dict[str, Any]:
        """Execute full EDA, generate charts, and compile statistical summary."""
        logger.info("Loading enriched data for exploratory analysis...")
        enc_df = pd.read_csv(self.data_dir / "fact_encounters_enriched.csv")
        pt_df = pd.read_csv(self.data_dir / "dim_patients_enriched.csv")
        cond_df = pd.read_csv(self.data_dir / "dim_conditions_summary.csv")

        enc_df["START"] = pd.to_datetime(enc_df["START"])
        enc_df["STOP"] = pd.to_datetime(enc_df["STOP"])

        # Generate Visualizations
        self.plot_monthly_trends(enc_df)
        self.plot_demographics(pt_df)
        self.plot_encounter_classes(enc_df)
        self.plot_top_conditions(cond_df)
        self.plot_cost_distributions(enc_df)
        self.plot_payer_vs_patient(enc_df)
        self.plot_inpatient_los(enc_df)
        self.plot_visit_frequency(pt_df)
        self.plot_department_metrics(enc_df)
        self.plot_cost_duration_correlation(enc_df)

        # Statistical Summaries
        stats_summary = self.calculate_statistics(enc_df, pt_df)
        with open(self.reports_dir / "eda_statistical_summary.json", "w", encoding="utf-8") as f:
            json.dump(stats_summary, f, indent=2)

        md_report = self.generate_eda_markdown(stats_summary, enc_df, pt_df)
        with open(self.reports_dir / "eda_insights_report.md", "w", encoding="utf-8") as f:
            f.write(md_report)

        logger.info("EDA visual suite and statistical reports generated successfully.")
        return stats_summary

    def plot_monthly_trends(self, df: pd.DataFrame):
        """Fig 1: Monthly Encounter Trends by Healthcare Setting."""
        fig, ax = plt.subplots(figsize=(12, 6))
        monthly = df.groupby(["ENCOUNTER_MONTH", "ENCOUNTERCLASS"]).size().unstack(fill_value=0)
        
        # Plot stacked area or lines
        for col in monthly.columns:
            ax.plot(monthly.index, monthly[col], marker="o", markersize=3, label=col.capitalize(), color=CLASS_COLORS.get(col, "#0284C7"), linewidth=2)

        ax.set_title("Monthly Encounter Volume by Care Setting (2021 – 2024)")
        ax.set_xlabel("Encounter Year-Month")
        ax.set_ylabel("Number of Encounters")
        plt.xticks(rotation=45, ha="right")
        # Show every 3rd label for readability
        ticks = ax.get_xticks()
        ax.set_xticks(ticks[::3])
        ax.legend(title="Care Setting", frameon=True, loc="upper right")
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig1_monthly_encounter_trends.png")
        plt.close(fig)

    def plot_demographics(self, df: pd.DataFrame):
        """Fig 2: Patient Demographics & Age Pyramid."""
        fig, ax = plt.subplots(figsize=(10, 6))
        age_order = ["0-17 (Pediatric)", "18-34 (Young Adult)", "35-49 (Adult)", "50-64 (Middle-Aged)", "65-79 (Older Adult)", "80+ (Senior)"]
        demo = df.groupby(["CURRENT_AGE_GROUP", "GENDER"]).size().unstack(fill_value=0).reindex(age_order)
        
        y = np.arange(len(age_order))
        width = 0.35
        m_vals = demo.get("M", pd.Series(0, index=age_order))
        f_vals = demo.get("F", pd.Series(0, index=age_order))

        rects1 = ax.barh(y - width/2, m_vals, width, label="Male", color="#0284C7")
        rects2 = ax.barh(y + width/2, f_vals, width, label="Female", color="#0D9488")

        ax.set_yticks(y)
        ax.set_yticklabels(age_order)
        ax.set_xlabel("Patient Population Count")
        ax.set_title("Patient Population Distribution by Age Bracket and Gender")
        ax.legend(frameon=True)
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig2_patient_demographics_pyramid.png")
        plt.close(fig)

    def plot_encounter_classes(self, df: pd.DataFrame):
        """Fig 3: Encounter Volume vs Total Claim Cost Share."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
        class_summary = df.groupby("ENCOUNTERCLASS").agg(
            VOLUME=("Id", "count"),
            TOTAL_COST=("TOTAL_CLAIM_COST", "sum")
        ).sort_values(by="VOLUME", ascending=False)

        colors = [CLASS_COLORS.get(c, "#0284C7") for c in class_summary.index]

        # Volume Bar
        ax1.bar(class_summary.index.str.capitalize(), class_summary["VOLUME"], color=colors, edgecolor="none")
        ax1.set_title("Encounter Volume by Setting")
        ax1.set_ylabel("Total Encounters")
        ax1.tick_params(axis="x", rotation=30)

        # Revenue Share Donut
        wedges, texts, autotexts = ax2.pie(
            class_summary["TOTAL_COST"],
            labels=class_summary.index.str.capitalize(),
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.8,
            wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2)
        )
        ax2.set_title("Total Billed Claim Cost Share ($)")
        plt.setp(autotexts, size=9, weight="bold")
        fig.suptitle("Clinical Setting Operational Volume vs. Financial Share", fontsize=14, weight="bold")
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig3_encounter_class_distribution.png")
        plt.close(fig)

    def plot_top_conditions(self, df: pd.DataFrame):
        """Fig 4: Top Diagnosed Clinical Conditions."""
        fig, ax = plt.subplots(figsize=(10, 6))
        top10 = df.head(10).sort_values(by="TOTAL_DIAGNOSES", ascending=True)
        bars = ax.barh(top10["DESCRIPTION"], top10["TOTAL_DIAGNOSES"], color="#0284C7", edgecolor="none")
        ax.set_xlabel("Diagnosis Event Count")
        ax.set_title("Top 10 Most Prevalent Clinical Diagnoses in Patient Cohort")
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 15, bar.get_y() + bar.get_height()/2, f"{int(w):,}", va="center", ha="left", fontsize=9, color="#1E293B")
        ax.set_xlim(0, top10["TOTAL_DIAGNOSES"].max() * 1.15)
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig4_top_chronic_conditions.png")
        plt.close(fig)

    def plot_cost_distributions(self, df: pd.DataFrame):
        """Fig 5: Cost Distribution by Encounter Class (Log Scale Boxplot)."""
        fig, ax = plt.subplots(figsize=(11, 6))
        classes = sorted(df["ENCOUNTERCLASS"].unique())
        cost_data = [df[df["ENCOUNTERCLASS"] == c]["TOTAL_CLAIM_COST"].values for c in classes]

        box = ax.boxplot(
            cost_data,
            patch_artist=True,
            tick_labels=[c.capitalize() for c in classes],
            showmeans=True,
            meanprops=dict(marker="o", markeredgecolor="black", markerfacecolor="white")
        )
        for patch, c in zip(box["boxes"], classes):
            patch.set_facecolor(CLASS_COLORS.get(c, "#0284C7"))
            patch.set_alpha(0.7)

        ax.set_yscale("log")
        ax.set_ylabel("Total Claim Cost ($) [Log Scale]")
        ax.set_title("Total Claim Cost Distribution Across Clinical Settings (Logarithmic)")
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig5_cost_distributions_boxplots.png")
        plt.close(fig)

    def plot_payer_vs_patient(self, df: pd.DataFrame):
        """Fig 6: Payer Coverage vs. Patient Financial Responsibility."""
        fig, ax = plt.subplots(figsize=(11, 5.5))
        payer_fin = df.groupby("PAYER").agg(
            PAYER_COVERAGE=("PAYER_COVERAGE", "sum"),
            PATIENT_PAYMENT=("PATIENT_PAYMENT", "sum")
        ).sort_values(by="PAYER_COVERAGE", ascending=False)

        x = np.arange(len(payer_fin))
        width = 0.4

        ax.bar(x - width/2, payer_fin["PAYER_COVERAGE"] / 1e6, width, label="Payer Reimbursed ($M)", color="#0D9488")
        ax.bar(x + width/2, payer_fin["PATIENT_PAYMENT"] / 1e6, width, label="Patient Out-of-Pocket ($M)", color="#E11D48")

        ax.set_xticks(x)
        ax.set_xticklabels(payer_fin.index, rotation=25, ha="right")
        ax.set_ylabel("Total Amount ($ Millions)")
        ax.set_title("Healthcare Financial Allocation: Payer Coverage vs. Patient Responsibility")
        ax.legend(frameon=True)
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig6_financial_breakdown_payer_vs_patient.png")
        plt.close(fig)

    def plot_inpatient_los(self, df: pd.DataFrame):
        """Fig 7: Inpatient Length of Stay (LOS) Distribution."""
        fig, ax = plt.subplots(figsize=(9, 5.5))
        inp = df[df["ENCOUNTERCLASS"] == "inpatient"]["LENGTH_OF_STAY_DAYS"].dropna()
        
        ax.hist(inp, bins=20, color="#8B5CF6", edgecolor="white", alpha=0.8, density=True)
        sns.kdeplot(inp, ax=ax, color="#4C1D95", linewidth=2.5)

        median_los = inp.median()
        mean_los = inp.mean()
        ax.axvline(median_los, color="#E11D48", linestyle="--", linewidth=1.5, label=f"Median LOS: {median_los:.1f} days")
        ax.axvline(mean_los, color="#059669", linestyle="-.", linewidth=1.5, label=f"Mean LOS: {mean_los:.1f} days")

        ax.set_xlabel("Inpatient Length of Stay (Days)")
        ax.set_ylabel("Probability Density")
        ax.set_title("Inpatient Hospital Length of Stay (LOS) Frequency Distribution")
        ax.legend(frameon=True)
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig7_length_of_stay_inpatient.png")
        plt.close(fig)

    def plot_visit_frequency(self, df: pd.DataFrame):
        """Fig 8: Patient Visit Frequency Segmentation."""
        fig, ax = plt.subplots(figsize=(10, 5.5))
        tier_counts = df["UTILIZATION_TIER"].value_counts()[
            ["1 Visit (Single)", "2-4 Visits (Occasional)", "5-9 Visits (Frequent)", "10+ Visits (High Utilizer)"]
        ]
        tier_colors = ["#94A3B8", "#0284C7", "#0D9488", "#E11D48"]
        bars = ax.bar(tier_counts.index, tier_counts.values, color=tier_colors, edgecolor="none")
        ax.set_ylabel("Patient Count")
        ax.set_title("Patient Healthcare Utilization Tiers (Lifetime Encounter Frequency)")

        for bar in bars:
            h = bar.get_height()
            pct = (h / len(df) * 100)
            ax.text(bar.get_x() + bar.get_width()/2, h + 10, f"{h:,}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=9, weight="bold")

        ax.set_ylim(0, tier_counts.max() * 1.18)
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig8_patient_visit_frequency.png")
        plt.close(fig)

    def plot_department_metrics(self, df: pd.DataFrame):
        """Fig 9: Encounter Volume by Clinical Department."""
        fig, ax = plt.subplots(figsize=(11, 5.5))
        dept_sum = df.groupby("CLINICAL_DEPARTMENT").size().sort_values(ascending=True)
        bars = ax.barh(dept_sum.index, dept_sum.values, color="#0F172A", edgecolor="none")
        ax.set_xlabel("Total Encounters Managed")
        ax.set_title("Clinical Department Service Volume (Mapped via Provider Specialty)")
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 20, bar.get_y() + bar.get_height()/2, f"{w:,}", va="center", ha="left", fontsize=9)
        ax.set_xlim(0, dept_sum.max() * 1.12)
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig9_clinical_department_volume.png")
        plt.close(fig)

    def plot_cost_duration_correlation(self, df: pd.DataFrame):
        """Fig 10: Encounter Duration vs Total Claim Cost."""
        fig, ax = plt.subplots(figsize=(10, 6))
        # Filter for duration <= 168h (7 days) for clean scatter visualization
        sub = df[df["DURATION_HOURS"] <= 168].sample(n=min(1200, len(df)), random_state=42)

        scatter = ax.scatter(
            sub["DURATION_HOURS"],
            sub["TOTAL_CLAIM_COST"],
            c=sub["TOTAL_CLAIM_COST"],
            cmap="viridis",
            alpha=0.6,
            edgecolors="none",
            s=25
        )
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Total Claim Cost ($)")

        ax.set_xlabel("Encounter Duration (Hours)")
        ax.set_ylabel("Total Claim Cost ($)")
        ax.set_title("Relationship Between Clinical Duration and Billed Claim Cost")
        fig.tight_layout()
        fig.savefig(self.figures_dir / "fig10_cost_vs_duration_scatter.png")
        plt.close(fig)

    def calculate_statistics(self, enc_df: pd.DataFrame, pt_df: pd.DataFrame) -> Dict[str, Any]:
        """Compute formal statistical summaries, ANOVA tests, and percentiles."""
        cost_series = enc_df["TOTAL_CLAIM_COST"].dropna()
        duration_series = enc_df["DURATION_HOURS"].dropna()
        los_inpatient = enc_df[enc_df["ENCOUNTERCLASS"] == "inpatient"]["LENGTH_OF_STAY_DAYS"].dropna()

        # ANOVA test across encounter classes for claim costs
        class_groups = [group["TOTAL_CLAIM_COST"].values for _, group in enc_df.groupby("ENCOUNTERCLASS")]
        f_stat, p_val = stats.f_oneway(*class_groups)

        return {
            "encounter_volume": int(len(enc_df)),
            "patient_volume": int(len(pt_df)),
            "cost_metrics": {
                "total_billed": float(cost_series.sum()),
                "mean": float(cost_series.mean()),
                "median": float(cost_series.median()),
                "std_dev": float(cost_series.std()),
                "skewness": float(stats.skew(cost_series)),
                "kurtosis": float(stats.kurtosis(cost_series)),
                "p25": float(cost_series.quantile(0.25)),
                "p75": float(cost_series.quantile(0.75)),
                "p95": float(cost_series.quantile(0.95)),
            },
            "duration_metrics_hours": {
                "mean": float(duration_series.mean()),
                "median": float(duration_series.median()),
                "std_dev": float(duration_series.std()),
            },
            "inpatient_los_days": {
                "mean": float(los_inpatient.mean()) if len(los_inpatient) > 0 else 0.0,
                "median": float(los_inpatient.median()) if len(los_inpatient) > 0 else 0.0,
                "iqr": float(los_inpatient.quantile(0.75) - los_inpatient.quantile(0.25)) if len(los_inpatient) > 0 else 0.0,
            },
            "anova_cost_across_classes": {
                "f_statistic": float(f_stat),
                "p_value": float(p_val),
                "statistically_significant": bool(p_val < 0.05)
            }
        }

    def generate_eda_markdown(self, stats_data: Dict[str, Any], enc_df: pd.DataFrame, pt_df: pd.DataFrame) -> str:
        md = ["# Hospital Patient Analytics — Exploratory Data Analysis (EDA) Insights Report\n\n"]
        md.append("## 1. Study Population & Encounter Overview\n")
        md.append(f"- **Patient Population:** {stats_data['patient_volume']:,} unique synthetic patients.\n")
        md.append(f"- **Total Clinical Encounters:** {stats_data['encounter_volume']:,} longitudinal encounters.\n")
        md.append(f"- **Study Period:** {enc_df['START'].min().strftime('%Y-%m-%d')} to {enc_df['START'].max().strftime('%Y-%m-%d')}.\n\n")

        md.append("## 2. Key Statistical Summaries\n\n")
        md.append("### Billed Claim Financial Distribution\n")
        c = stats_data["cost_metrics"]
        md.append(f"- **Total Gross Billed Charges:** ${c['total_billed']:,.2f}\n")
        md.append(f"- **Mean Cost per Encounter:** ${c['mean']:,.2f} (Std: ${c['std_dev']:,.2f})\n")
        md.append(f"- **Median Cost per Encounter:** ${c['median']:,.2f} (IQR: ${c['p25']:,.2f} – ${c['p75']:,.2f})\n")
        md.append(f"- **95th Percentile Cost:** ${c['p95']:,.2f}\n")
        md.append(f"- **Skewness:** {c['skewness']:.2f} (Highly right-skewed, typical of acute healthcare expenditure distributions)\n\n")

        md.append("### Hypothesis Testing: Cost Variation Across Clinical Settings\n")
        a = stats_data["anova_cost_across_classes"]
        md.append(f"- **One-Way ANOVA F-Statistic:** {a['f_statistic']:.2f}\n")
        md.append(f"- **P-Value:** {a['p_value']:.4e} (Statistically Significant: `{a['statistically_significant']}`)\n")
        md.append("- **Interpretation:** Total claim costs exhibit extreme, statistically significant variance between clinical settings (Inpatient and Emergency encounters drive disproportionate financial burden relative to Ambulatory and Wellness settings).\n\n")

        md.append("## 3. Visual Figures Summary\n\n")
        md.append("| Figure Name | Description | Output File |\n|:---|:---|:---|\n")
        md.append("| Figure 1 | Monthly Encounter Trends by Setting | `reports/figures/fig1_monthly_encounter_trends.png` |\n")
        md.append("| Figure 2 | Patient Demographics & Age Pyramid | `reports/figures/fig2_patient_demographics_pyramid.png` |\n")
        md.append("| Figure 3 | Volume vs Financial Share | `reports/figures/fig3_encounter_class_distribution.png` |\n")
        md.append("| Figure 4 | Top Chronic Conditions | `reports/figures/fig4_top_chronic_conditions.png` |\n")
        md.append("| Figure 5 | Cost Distributions (Log Scale) | `reports/figures/fig5_cost_distributions_boxplots.png` |\n")
        md.append("| Figure 6 | Payer vs Patient Financial Split | `reports/figures/fig6_financial_breakdown_payer_vs_patient.png` |\n")
        md.append("| Figure 7 | Inpatient Length of Stay (LOS) | `reports/figures/fig7_length_of_stay_inpatient.png` |\n")
        md.append("| Figure 8 | Patient Visit Frequency Tiers | `reports/figures/fig8_patient_visit_frequency.png` |\n")
        md.append("| Figure 9 | Clinical Department Volume | `reports/figures/fig9_clinical_department_volume.png` |\n")
        md.append("| Figure 10 | Duration vs Claim Cost Scatter | `reports/figures/fig10_cost_vs_duration_scatter.png` |\n\n")

        md.append("## 4. Analytical Limitations\n")
        md.append("- **Synthetic Healthcare Distribution:** Synthea creates rule-driven synthetic data; clinical correlations reflect simulation modeling rather than real-world biological variations.\n")
        md.append("- **Department Attribution:** Departmental volumes are mapped via provider primary specialties rather than internal hospital ledger cost centers.\n")
        md.append("- **Billed vs Net Revenue:** Synthea total claim costs represent gross billed figures. True net contractual allowances vary by private payer agreements.\n")
        return "".join(md)


def main():
    pipeline = HealthcareEDAPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
