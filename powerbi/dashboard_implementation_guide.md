# Power BI Dashboard Implementation & UI/UX Design Guide
## Hospital Patient Analytics & Healthcare Performance Optimization

This guide provides end-to-end instructions for implementing the four-page Power BI executive dashboard report.

---

## 1. Visual Identity & Canvas Standards

| Setting | Standard Value | Rationale |
|:---|:---|:---|
| **Canvas Size** | 16:9 Widescreen (1280 × 720 px) | Optimized for modern high-resolution displays and tablet viewing |
| **Primary Theme Color** | Deep Navy (`#0F172A`) | Professional healthcare command-center foundation |
| **Accent / Clinical Blue** | Cyan / Sky Blue (`#0284C7`) | High visibility for primary volume trends |
| **Care Metric Teal** | Medical Teal (`#0D9488`) | Positive/preventive health indicator |
| **Warning / Acute Accent** | Crimson Red (`#E11D48`) | High-alert clinical events (Emergency, Readmission) |
| **Background Fill** | Ice Slate White (`#F8FAFC`) | Reduces glare; ensures accessibility contrast |
| **Card / Visual Container** | Pure White (`#FFFFFF`) | Rounded corners (4px radius), subtle drop shadow |
| **Typography** | Segoe UI Semibold / Regular | Clean, legible healthcare typography hierarchy |

---

## 2. Page 1 — Executive Healthcare Overview

### Purpose:
Provides senior hospital executive leadership (CMO, CFO, COO) with an immediate, high-level summary of operational volume, patient throughput, financial health, and 30-day post-acute re-encounter rates.

### Visual Placement Grid (1280 × 720 Canvas):

```
+---------------------------------------------------------------------------------------------------+
| HEADER BAR: Hospital Patient Analytics — Executive Command Center (Y:0, H:60, W:1280)            |
+---------------------------------------------------------------------------------------------------+
| SLICER BAR: [Date Year-Quarter]  [Care Setting]  [Payer]  [Hospital Facility] (Y:65, H:45, W:1280) |
+---------------------------------------------------------------------------------------------------+
| KPI CARD 1      | KPI CARD 2      | KPI CARD 3      | KPI CARD 4      | KPI CARD 5                |
| Encounters      | Patients        | Gross Charges   | Payer Reimb %   | 30D Re-encounter %        |
| 5,960           | 1,200           | $9.31M          | 83.4%           | 11.2%                     |
| (X:20, W:230)   | (X:270, W:230)  | (X:520, W:230)  | (X:770, W:230)  | (X:1020, W:230) (H:80)    |
+---------------------------------------------------------------------------------------------------+
| VISUAL 1.1: Line & Clustered Column Chart (X:20, Y:205, W:780, H:260)                             |
| Title: Monthly Encounter Volume & Billed Gross Charges Trend                                      |
| X-Axis: Dim_Date[year_month]                                                                      |
| Column Values: [Total Encounters]                                                                 |
| Line Value: [Gross Billed Charges]                                                                |
+--------------------------------------------------+------------------------------------------------+
| VISUAL 1.2: Donut Chart (X:820, Y:205, W:430)    | VISUAL 1.3: Clustered Bar Chart (X:20, Y:480) |
| Title: Encounters by Clinical Care Setting       | Title: Top Clinical Departments by Volume      |
| Legend: Dim_Encounter_Type[display_name]         | Y-Axis: Dim_Provider[clinical_department]      |
| Values: [Total Encounters]                       | X-Axis: [Total Encounters], [Gross Charges]    |
+--------------------------------------------------+------------------------------------------------+
| VISUAL 1.4: Matrix / Summary Table (X:660, Y:480, W:590, H:215)                                    |
| Title: Care Setting Summary (Volume, Cost, LOS, Re-encounters)                                     |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Page 2 — Patient Demographics & Conditions

### Purpose:
Enables population health directors to evaluate patient age brackets, gender distribution, racial diversity, and top chronic illness comorbidities.

### Visual Placement Grid:
1. **Top Slicers (Y:65, H:45):** `Dim_Patient[current_age_group]`, `Dim_Patient[gender]`, `Dim_Patient[race]`, `Dim_Condition[clinical_category]`.
2. **Visual 2.1 — Population Age-Gender Pyramid (X:20, Y:125, W:590, H:320):**
   - Type: Clustered Bar Chart.
   - Y-Axis: `Dim_Patient[current_age_group]` (Ordered: 0-17, 18-34, 35-49, 50-64, 65-79, 80+).
   - X-Axis: `[Total Unique Patients]`.
   - Legend: `Dim_Patient[gender]` (`#0284C7` for M, `#0D9488` for F).
3. **Visual 2.2 — Top 10 Chronic Diagnoses (X:630, Y:125, W:620, H:320):**
   - Type: Horizontal Bar Chart.
   - Y-Axis: `Dim_Condition[condition_name]`.
   - X-Axis: `[Diagnosed Chronic Condition Count]`.
   - Data Labels: On (Inside End).
4. **Visual 2.3 — Patient Utilization Tiers (X:20, Y:465, W:400, H:230):**
   - Type: Treemap.
   - Group: `Dim_Patient[utilization_tier]`.
   - Values: `[Total Unique Patients]`.
5. **Visual 2.4 — Multimorbidity vs. Lifetime Cost Scatter (X:440, Y:465, W:810, H:230):**
   - Type: Scatter Plot.
   - X-Axis: `Dim_Patient[total_lifetime_encounters]`.
   - Y-Axis: `Dim_Patient[total_lifetime_claim_cost]`.
   - Details: `Dim_Patient[patient_key]`.
   - Legend: `Dim_Patient[cluster_name]`.

---

## 4. Page 3 — Hospital Encounter Operations & Flow

### Purpose:
Assists Chief Medical Officers and Operations Directors in tracking length of stay, emergency vs. scheduled admissions, intake time-of-day dynamics, and 30-day post-acute re-encounter rates.

### Visual Placement Grid:
1. **KPI Cards (Y:125, H:75):**
   - `[Average Encounter Duration (Hours)]`: 10.4 Hours.
   - `[Average Inpatient Length of Stay (Days)]`: 4.8 Days.
   - `[Emergency Department Visits]`: Volume & % of Total.
   - `[30-Day Re-encounter Rate %]`: With conditional color alert (>15% = Red, <=15% = Emerald).
2. **Visual 3.1 — Inpatient Length of Stay by Clinical Department (X:20, Y:215, W:600, H:250):**
   - Type: Column Chart with Target Line.
   - X-Axis: `Dim_Provider[clinical_department]`.
   - Y-Axis: `[Average Inpatient Length of Stay (Days)]`.
3. **Visual 3.2 — 30-Day Re-encounter Rate by Index Setting & Age (X:640, Y:215, W:610, H:250):**
   - Type: Clustered Column Chart.
   - X-Axis: `Fact_Encounters[age_group]`.
   - Y-Axis: `[30-Day Re-encounter Rate %]`.
   - Legend: `Fact_Encounters[encounter_class]`.
4. **Visual 3.3 — Weekly Intake Arrival Heatmap (X:20, Y:480, W:1230, H:215):**
   - Type: Matrix with Background Heatmap.
   - Rows: `Dim_Date[day_name]` (Monday through Sunday).
   - Columns: `Fact_Encounters[start_hour]` (0 to 23).
   - Values: `[Total Encounters]`.
   - Conditional Formatting: Color scale white to deep teal (`#0D9488`).

---

## 5. Page 4 — Healthcare Cost & Payer Analysis

### Purpose:
Dedicated to Chief Financial Officers and Revenue Cycle Management to evaluate billed charges, insurance collection ratios, patient out-of-pocket bad debt exposure, and high-cost surgical procedures.

### Visual Placement Grid:
1. **Financial Waterfall / Split Card (Y:125, H:75):**
   - `[Gross Billed Charges]`: $9.31M.
   - `[Total Payer Reimbursement]`: $7.76M (83.4%).
   - `[Total Patient Responsibility]`: $1.55M (16.6%).
2. **Visual 4.1 — Payer Reimbursement Performance (X:20, Y:215, W:680, H:250):**
   - Type: 100% Stacked Bar Chart.
   - Y-Axis: `Fact_Encounters[payer]`.
   - X-Axis: `[Total Payer Reimbursement]` vs `[Total Patient Responsibility]`.
3. **Visual 4.2 — Top High-Cost Clinical Procedures (X:720, Y:215, W:530, H:250):**
   - Type: Funnel / Bar Chart.
   - Category: `Fact_Encounter_Procedures[procedure_name]`.
   - Values: Sum of `procedure_cost`.
4. **Visual 4.3 — Patient Financial Decile Pareto Analysis (X:20, Y:480, W:1230, H:215):**
   - Type: Line & Clustered Column Chart.
   - X-Axis: Patient Spend Decile (1 to 10).
   - Column Values: Total Gross Spend in Decile.
   - Line Value: Cumulative Spend Percentage (80/20 Pareto curve).

---

## 6. Accessibility & Interactivity Rules
1. **Cross-Filtering:** Selecting a Clinical Department on Page 1 or Page 3 highlights associated care settings and conditions without blanking out other visuals.
2. **Tooltips:** Custom report tooltips show Average Duration, Diagnosis Count, and Payer Split on hover.
3. **Screen Reader Compliance:** Alt-text provided on every visual container explaining chart takeaway (e.g., "Bar chart showing Essential Hypertension as the top diagnosis with 842 occurrences across 612 unique patients").
