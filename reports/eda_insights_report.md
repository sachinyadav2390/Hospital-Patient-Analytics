# Hospital Patient Analytics — Exploratory Data Analysis (EDA) Insights Report

## 1. Study Population & Encounter Overview
- **Patient Population:** 1,200 unique synthetic patients.
- **Total Clinical Encounters:** 5,960 longitudinal encounters.
- **Study Period:** 2021-01-01 to 2024-12-30.

## 2. Key Statistical Summaries

### Billed Claim Financial Distribution
- **Total Gross Billed Charges:** $9,306,140.73
- **Mean Cost per Encounter:** $1,561.43 (Std: $4,247.02)
- **Median Cost per Encounter:** $316.73 (IQR: $190.37 – $656.43)
- **95th Percentile Cost:** $8,573.96
- **Skewness:** 4.41 (Highly right-skewed, typical of acute healthcare expenditure distributions)

### Hypothesis Testing: Cost Variation Across Clinical Settings
- **One-Way ANOVA F-Statistic:** 4769.18
- **P-Value:** 0.0000e+00 (Statistically Significant: `True`)
- **Interpretation:** Total claim costs exhibit extreme, statistically significant variance between clinical settings (Inpatient and Emergency encounters drive disproportionate financial burden relative to Ambulatory and Wellness settings).

## 3. Visual Figures Summary

| Figure Name | Description | Output File |
|:---|:---|:---|
| Figure 1 | Monthly Encounter Trends by Setting | `reports/figures/fig1_monthly_encounter_trends.png` |
| Figure 2 | Patient Demographics & Age Pyramid | `reports/figures/fig2_patient_demographics_pyramid.png` |
| Figure 3 | Volume vs Financial Share | `reports/figures/fig3_encounter_class_distribution.png` |
| Figure 4 | Top Chronic Conditions | `reports/figures/fig4_top_chronic_conditions.png` |
| Figure 5 | Cost Distributions (Log Scale) | `reports/figures/fig5_cost_distributions_boxplots.png` |
| Figure 6 | Payer vs Patient Financial Split | `reports/figures/fig6_financial_breakdown_payer_vs_patient.png` |
| Figure 7 | Inpatient Length of Stay (LOS) | `reports/figures/fig7_length_of_stay_inpatient.png` |
| Figure 8 | Patient Visit Frequency Tiers | `reports/figures/fig8_patient_visit_frequency.png` |
| Figure 9 | Clinical Department Volume | `reports/figures/fig9_clinical_department_volume.png` |
| Figure 10 | Duration vs Claim Cost Scatter | `reports/figures/fig10_cost_vs_duration_scatter.png` |

## 4. Analytical Limitations
- **Synthetic Healthcare Distribution:** Synthea creates rule-driven synthetic data; clinical correlations reflect simulation modeling rather than real-world biological variations.
- **Department Attribution:** Departmental volumes are mapped via provider primary specialties rather than internal hospital ledger cost centers.
- **Billed vs Net Revenue:** Synthea total claim costs represent gross billed figures. True net contractual allowances vary by private payer agreements.
