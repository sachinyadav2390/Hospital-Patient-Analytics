# Hospital Patient Analytics — Advanced Healthcare Analytics Report

## 1. Unsupervised Machine Learning: K-Means Patient Segmentation

**Optimal Cluster Count:** `k = 4` (Evaluated using Inertia Elbow and Silhouette Coefficients)

| Cluster Archetype | Patient Volume | % Share | Mean Recency (Days) | Mean Lifetime Visits | Mean Total Cost ($) | Mean Inpatient Stays |
|:---|---:|---:|---:|---:|---:|---:|
| **Moderate-Need Chronic Care** | 243 | 20.2% | 828 d | 2.3 visits | $3,091.51 | 0.12 |
| **Frequent Emergency Utilizers** | 238 | 19.8% | 170 d | 7.7 visits | $5,738.64 | 0.03 |
| **Low-Intensity Outpatients** | 493 | 41.1% | 210 d | 3.7 visits | $2,419.17 | 0.11 |
| **High-Cost Complex Inpatients** | 226 | 18.8% | 179 d | 7.7 visits | $26,532.99 | 1.33 |

### Strategic Clinical Interpretation:
- **High-Cost Complex Inpatients:** Represent the highest revenue and clinical resource intensity. Targeted care coordination and discharge planning offer massive cost-containment opportunities.
- **Frequent Emergency Utilizers:** Patients with recurring acute emergency presentations who would benefit from community primary care intervention and chronic condition stabilization.
- **Moderate-Need Chronic Care:** Routine maintenance population; candidates for remote patient monitoring (RPM) and telehealth wellness management.

## 2. Longitudinal Patient Cohort Analysis

- **Total Monthly Cohorts Analyzed:** 48
- **Average Month 1 Re-attendance Rate:** 6.8%
- **Average Month 6 Retention Rate:** 6.0%
- **Average Month 12 Retention Rate:** 5.7%

## 3. 30-Day Subsequent Re-encounter Analysis

- **Eligible Index Acute Encounters:** 1,014
- **30-Day Subsequent Re-encounters:** 131
- **Overall Re-encounter Rate:** **12.92%**

### Re-encounter Rates by Index Care Setting
| Index Setting | Eligible Encounters | Re-encounters (30D) | Re-encounter Rate (%) |
|:---|---:|---:|---:|
| `Emergency` | 624 | 80 | 12.82% |
| `Inpatient` | 390 | 51 | 13.08% |

> [!WARNING] Methodological Integrity & Regulatory Limitation
> The 30-day indicator reported here measures any healthcare contact (including ambulatory follow-ups) occurring within 30 days of an index acute discharge. This metric must NOT be conflated with the Centers for Medicare & Medicaid Services (CMS) Hospital Readmissions Reduction Program (HRRP) measure, which evaluates unplanned acute inpatient-to-inpatient readmissions using national claims risk adjustment models.
