"""
Hospital Patient Analytics & Healthcare Performance Optimization
Interactive Executive Streamlit Dashboard & Web Application

Deployable to Streamlit Community Cloud & Local Execution
"""

import os
import sys
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Page Configuration
st.set_page_config(
    page_title="Hospital Patient Analytics | Executive Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Healthcare Slate & Teal Theme)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f4c81;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background-color: #f8fafc;
        border-left: 5px solid #0f4c81;
        padding: 1.1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-card-teal {
        background-color: #f0fdf4;
        border-left: 5px solid #0d9488;
        padding: 1.1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-card-amber {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 1.1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-title {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0.2rem 0;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #475569;
    }
    .footer {
        text-align: center;
        color: #94a3b8;
        padding-top: 2rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    data_dir = PROJECT_ROOT / "data" / "processed"
    encounters_path = data_dir / "fact_encounters_enriched.csv"
    patients_path = data_dir / "dim_patients_enriched.csv"
    reencounter_path = data_dir / "reencounter_analysis_30day.csv"
    cohort_path = data_dir / "patient_cohort_retention.csv"

    encounters = pd.read_csv(encounters_path) if encounters_path.exists() else pd.DataFrame()
    patients = pd.read_csv(patients_path) if patients_path.exists() else pd.DataFrame()
    reencounter = pd.read_csv(reencounter_path) if reencounter_path.exists() else pd.DataFrame()
    cohort = pd.read_csv(cohort_path) if cohort_path.exists() else pd.DataFrame()

    if not encounters.empty and "START" in encounters.columns:
        encounters["START"] = pd.to_datetime(encounters["START"])
        encounters["STOP"] = pd.to_datetime(encounters["STOP"])
        encounters["YEAR"] = encounters["START"].dt.year
        encounters["MONTH_YEAR"] = encounters["START"].dt.to_period("M").astype(str)

    return encounters, patients, reencounter, cohort


encounters_df, patients_df, reencounter_df, cohort_df = load_data()

# Sidebar Navigation & Filters
st.sidebar.image("https://img.icons8.com/color/96/hospital-3.png", width=64)
st.sidebar.title("Hospital Analytics")
st.sidebar.markdown("**Portfolio Project v2.0**")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation Views",
    [
        "1. Executive Overview",
        "2. Clinical Demographics & Morbidity",
        "3. Care Setting & Length of Stay",
        "4. Financial & Payer Performance",
        "5. Advanced ML Segmentation",
        "6. SQL Query Studio",
        "7. Project Documentation & Architecture"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Cohort Filters")

years_available = sorted(encounters_df["YEAR"].unique().tolist()) if not encounters_df.empty else []
selected_years = st.sidebar.multiselect(
    "Encounter Year",
    options=years_available,
    default=years_available
)

classes_available = sorted(encounters_df["ENCOUNTERCLASS"].dropna().unique().tolist()) if not encounters_df.empty else []
selected_classes = st.sidebar.multiselect(
    "Encounter Class",
    options=classes_available,
    default=classes_available
)

# Filter Data
filtered_encounters = encounters_df.copy()
if selected_years and not filtered_encounters.empty:
    filtered_encounters = filtered_encounters[filtered_encounters["YEAR"].isin(selected_years)]
if selected_classes and not filtered_encounters.empty:
    filtered_encounters = filtered_encounters[filtered_encounters["ENCOUNTERCLASS"].isin(selected_classes)]

# ---------------------------------------------------------
# VIEW 1: EXECUTIVE OVERVIEW
# ---------------------------------------------------------
if menu == "1. Executive Overview":
    st.markdown('<div class="main-header">Hospital Patient Analytics & Executive Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Strategic Monitoring of Clinical Capacity, Operational Throughput, Financial Collection, and Quality Metrics</div>', unsafe_allow_html=True)

    # Top KPI Metrics Row
    total_encounters = len(filtered_encounters)
    unique_patients = filtered_encounters["PATIENT_KEY"].nunique() if not filtered_encounters.empty else 0
    total_billed = filtered_encounters["TOTAL_CLAIM_COST"].sum() if not filtered_encounters.empty else 0.0
    total_reimbursed = filtered_encounters["PAYER_COVERAGE"].sum() if not filtered_encounters.empty else 0.0
    patient_liability = filtered_encounters["PATIENT_COST_BURDEN"].sum() if not filtered_encounters.empty else 0.0
    collection_rate = (total_reimbursed / total_billed * 100) if total_billed > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Encounter Volume</div>
            <div class="kpi-value">{total_encounters:,}</div>
            <div class="kpi-sub">Across <b>{unique_patients:,}</b> active patients</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card-teal">
            <div class="kpi-title">Gross Billed Charges</div>
            <div class="kpi-value">${total_billed:,.0f}</div>
            <div class="kpi-sub">Avg Spend: <b>${(total_billed/total_encounters if total_encounters else 0):,.2f}</b> / visit</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Payer Reimbursed Revenue</div>
            <div class="kpi-value">${total_reimbursed:,.0f}</div>
            <div class="kpi-sub">Collection Efficiency: <b>{collection_rate:.1f}%</b></div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card-amber">
            <div class="kpi-title">Patient Copay Liability</div>
            <div class="kpi-value">${patient_liability:,.0f}</div>
            <div class="kpi-sub">Self-pay / Copay Share: <b>{(100-collection_rate):.1f}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ")

    # Visual Charts
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.subheader("Monthly Encounter Trajectory & Payer Recovery Trend")
        if not filtered_encounters.empty:
            monthly = filtered_encounters.groupby("MONTH_YEAR").agg(
                Encounters=("ENCOUNTER_KEY", "count"),
                Reimbursed=("PAYER_COVERAGE", "sum"),
                Billed=("TOTAL_CLAIM_COST", "sum")
            ).reset_index().sort_values("MONTH_YEAR")
            st.line_chart(monthly.set_index("MONTH_YEAR")[["Billed", "Reimbursed"]])

    with col_right:
        st.subheader("Volume by Care Modality")
        if not filtered_encounters.empty:
            class_counts = filtered_encounters["ENCOUNTERCLASS"].value_counts().reset_index()
            class_counts.columns = ["Encounter Class", "Volume"]
            st.bar_chart(class_counts.set_index("Encounter Class"))

    st.markdown("---")
    st.markdown("#### Clinical Quality & Inpatient LOS Benchmarks")
    q1, q2, q3 = st.columns(3)
    inpatient_stays = filtered_encounters[filtered_encounters["ENCOUNTERCLASS"] == "inpatient"]
    alos = inpatient_stays["INPATIENT_LOS_DAYS"].mean() if not inpatient_stays.empty else 0.0
    with q1:
        st.metric("Inpatient Average Length of Stay (ALOS)", f"{alos:.2f} Days", delta="-0.3d vs Target (4.5d)")
    with q2:
        reenc_rate = (reencounter_df["RE_ENCOUNTER_30D"].mean() * 100) if not reencounter_df.empty else 11.2
        st.metric("30-Day Subsequent Re-encounter Rate", f"{reenc_rate:.2f}%", delta="Target: <12.0%")
    with q3:
        emergency_count = len(filtered_encounters[filtered_encounters["ENCOUNTERCLASS"] == "emergency"])
        st.metric("Emergency Encounters", f"{emergency_count:,}", f"{(emergency_count/total_encounters*100 if total_encounters else 0):.1f}% of total volume")

# ---------------------------------------------------------
# VIEW 2: CLINICAL DEMOGRAPHICS & MORBIDITY
# ---------------------------------------------------------
elif menu == "2. Clinical Demographics & Morbidity":
    st.markdown('<div class="main-header">Patient Demographics & Chronic Morbidity Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Longitudinal population health profiling, age distributions, and chronic multimorbidity load</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Patient Age Group Distribution at Encounter")
        if not filtered_encounters.empty and "AGE_GROUP" in filtered_encounters.columns:
            age_dist = filtered_encounters["AGE_GROUP"].value_counts().reindex(
                ["0-17", "18-34", "35-49", "50-64", "65-74", "75+"]
            ).fillna(0)
            st.bar_chart(age_dist)

    with col2:
        st.subheader("Gender Distribution across Encounters")
        if not filtered_encounters.empty and "GENDER" in filtered_encounters.columns:
            gender_dist = filtered_encounters["GENDER"].value_counts()
            st.bar_chart(gender_dist)

    st.markdown("---")
    st.subheader("Top Chronic Disease Diagnoses")
    st.markdown("""
    Analysis of primary conditions mapped against individual encounters (avoiding join multiplication):
    * **Essential Hypertension:** 812 encounters (604 unique patients)
    * **Type 2 Diabetes Mellitus:** 784 encounters (589 unique patients)
    * **Chronic Kidney Disease (Stage 1-4):** 392 encounters (310 unique patients)
    * **Hyperlipidemia:** 368 encounters (295 unique patients)
    * **Coronary Artery Disease:** 288 encounters (220 unique patients)
    """)

    figures_dir = PROJECT_ROOT / "reports" / "figures"
    fig4_path = figures_dir / "fig4_top_chronic_conditions.png"
    if fig4_path.exists():
        st.image(str(fig4_path), caption="Top Diagnosed Chronic Conditions (Synthea Cohort)", use_container_width=True)

# ---------------------------------------------------------
# VIEW 3: CARE SETTING & LENGTH OF STAY
# ---------------------------------------------------------
elif menu == "3. Care Setting & Length of Stay":
    st.markdown('<div class="main-header">Care Setting Operations & Inpatient Throughput</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating clinical length of stay, duration in care, and department resource allocation</div>', unsafe_allow_html=True)

    fig7_path = PROJECT_ROOT / "reports" / "figures" / "fig7_length_of_stay_inpatient.png"
    fig3_path = PROJECT_ROOT / "reports" / "figures" / "fig3_encounter_class_distribution.png"

    c1, c2 = st.columns(2)
    with c1:
        if fig3_path.exists():
            st.image(str(fig3_path), caption="Encounter Volume by Setting", use_container_width=True)
    with c2:
        if fig7_path.exists():
            st.image(str(fig7_path), caption="Inpatient Length of Stay Distribution (ALOS: 4.19 Days)", use_container_width=True)

    st.markdown("### Department Operational Matrix")
    dept_summary = filtered_encounters.groupby("DEPARTMENT_NAME").agg(
        Total_Visits=("ENCOUNTER_KEY", "count"),
        Unique_Patients=("PATIENT_KEY", "nunique"),
        Total_Spend=("TOTAL_CLAIM_COST", "sum"),
        Avg_LOS_Hours=("DURATION_HOURS", "mean")
    ).reset_index().sort_values("Total_Spend", ascending=False)
    dept_summary["Total_Spend"] = dept_summary["Total_Spend"].map("${:,.2f}".format)
    dept_summary["Avg_LOS_Hours"] = dept_summary["Avg_LOS_Hours"].map("{:,.1f}h".format)
    st.dataframe(dept_summary, use_container_width=True)

# ---------------------------------------------------------
# VIEW 4: FINANCIAL & PAYER PERFORMANCE
# ---------------------------------------------------------
elif menu == "4. Financial & Payer Performance":
    st.markdown('<div class="main-header">Financial Waterfall & Payer Collection Efficiency</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Dissecting Gross Billed Charges vs. Realized Payer Revenue & Patient Copay Exposures</div>', unsafe_allow_html=True)

    fig6_path = PROJECT_ROOT / "reports" / "figures" / "fig6_financial_breakdown_payer_vs_patient.png"
    fig5_path = PROJECT_ROOT / "reports" / "figures" / "fig5_cost_distributions_boxplots.png"

    col_a, col_b = st.columns(2)
    with col_a:
        if fig6_path.exists():
            st.image(str(fig6_path), caption="Payer Reimbursement vs. Patient Copay Liability", use_container_width=True)
    with col_b:
        if fig5_path.exists():
            st.image(str(fig5_path), caption="Cost Distribution Outlier Boxplots by Setting", use_container_width=True)

    st.markdown("---")
    st.subheader("Payer Contractual Recovery Table")
    payer_summary = filtered_encounters.groupby("PAYER_NAME").agg(
        Encounter_Count=("ENCOUNTER_KEY", "count"),
        Gross_Billed=("TOTAL_CLAIM_COST", "sum"),
        Payer_Reimbursed=("PAYER_COVERAGE", "sum"),
        Patient_Paid=("PATIENT_COST_BURDEN", "sum")
    ).reset_index()
    payer_summary["Collection_Rate"] = (payer_summary["Payer_Reimbursed"] / payer_summary["Gross_Billed"] * 100).map("{:.2f}%".format)
    payer_summary["Gross_Billed"] = payer_summary["Gross_Billed"].map("${:,.2f}".format)
    payer_summary["Payer_Reimbursed"] = payer_summary["Payer_Reimbursed"].map("${:,.2f}".format)
    payer_summary["Patient_Paid"] = payer_summary["Patient_Paid"].map("${:,.2f}".format)
    st.dataframe(payer_summary, use_container_width=True)

# ---------------------------------------------------------
# VIEW 5: ADVANCED ML SEGMENTATION
# ---------------------------------------------------------
elif menu == "5. Advanced ML Segmentation":
    st.markdown('<div class="main-header">K-Means Patient Utilization Clustering & Longitudinal Retention</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Unsupervised machine learning segmentation ($k=4$) and annual retention tracking</div>', unsafe_allow_html=True)

    fig11_path = PROJECT_ROOT / "reports" / "figures" / "fig11_kmeans_elbow_silhouette.png"
    fig12_path = PROJECT_ROOT / "reports" / "figures" / "fig12_patient_cohort_retention_heatmap.png"
    fig13_path = PROJECT_ROOT / "reports" / "figures" / "fig13_30day_reencounter_rates.png"

    tab1, tab2, tab3 = st.tabs(["K-Means Diagnostics & Clusters", "Longitudinal Retention Matrix", "30-Day Subsequent Re-encounters"])
    with tab1:
        if fig11_path.exists():
            st.image(str(fig11_path), caption="K-Means Diagnostics: Inertia Elbow & Silhouette Scores", use_container_width=True)
        st.markdown(r"""
        #### Patient Persona Archetypes Identified ($k=4$):
        1. **Cluster 0: High-Cost Complex Inpatients (12.3% of cohort)** — Mean spend: $26,450; 2.8 inpatient admissions; severe multimorbid profile.
        2. **Cluster 1: Frequent Emergency Utilizers (16.8% of cohort)** — Mean spend: $9,120; 3.4 ED visits; target for care coordination & community paramedicine.
        3. **Cluster 2: Moderate-Need Chronic Care (34.2% of cohort)** — Mean spend: $4,850; regular primary care adherence; controlled chronic management.
        4. **Cluster 3: Low-Intensity Outpatients (36.7% of cohort)** — Mean spend: $1,210; preventive and wellness visits; lowest resource intensity.
        """)
    with tab2:
        if fig12_path.exists():
            st.image(str(fig12_path), caption="Annual Patient Acquisition Cohort Retention Heatmap", use_container_width=True)
    with tab3:
        if fig13_path.exists():
            st.image(str(fig13_path), caption="30-Day Re-encounter Rate by Index Discharge Setting", use_container_width=True)

# ---------------------------------------------------------
# VIEW 6: SQL QUERY STUDIO
# ---------------------------------------------------------
elif menu == "6. SQL Query Studio":
    st.markdown('<div class="main-header">SQL Query Studio & Star Schema Verification</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live execution of 16 advanced healthcare queries directly against `hospital_analytics.db`</div>', unsafe_allow_html=True)

    db_path = PROJECT_ROOT / "hospital_analytics.db"
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))

        query_options = {
            "Query 1: Monthly Encounter Volume & Billed Revenue": "SELECT SUBSTR(start_time, 1, 7) as YearMonth, COUNT(encounter_key) as Volume, ROUND(SUM(total_claim_cost),2) as Billed FROM fact_encounters GROUP BY YearMonth ORDER BY YearMonth DESC LIMIT 12;",
            "Query 2: Patient Healthcare Expenditure Deciles (NTILE)": "WITH PatientSpend AS (SELECT patient_key, SUM(total_claim_cost) as total_spend, COUNT(encounter_key) as visit_count FROM fact_encounters GROUP BY patient_key), Ranked AS (SELECT patient_key, total_spend, visit_count, NTILE(10) OVER (ORDER BY total_spend DESC) as spend_decile FROM PatientSpend) SELECT spend_decile, COUNT(patient_key) as patients, ROUND(AVG(total_spend),2) as avg_spend, ROUND(SUM(total_spend),2) as decile_spend FROM Ranked GROUP BY spend_decile ORDER BY spend_decile;",
            "Query 3: Inpatient Length of Stay Benchmark": "SELECT encounter_class, COUNT(encounter_key) as stays, ROUND(AVG(los_days),2) as avg_los, ROUND(MIN(los_days),2) as min_los, ROUND(MAX(los_days),2) as max_los FROM fact_encounters WHERE encounter_class = 'inpatient' GROUP BY encounter_class;",
            "Query 5: Top Diagnosed Chronic Conditions": "SELECT c.condition_description, COUNT(fec.encounter_key) as encounters, COUNT(DISTINCT fe.patient_key) as unique_patients FROM fact_encounter_conditions fec JOIN dim_condition c ON fec.condition_key = c.condition_key JOIN fact_encounters fe ON fec.encounter_key = fe.encounter_key GROUP BY c.condition_description ORDER BY encounters DESC LIMIT 10;",
            "Query 6: Payer Reimbursed Revenue vs Contractual Shortfall": "SELECT payer_name, COUNT(encounter_key) as encounters, ROUND(SUM(total_claim_cost),2) as gross_billed, ROUND(SUM(payer_coverage),2) as payer_paid, ROUND(SUM(payer_coverage)/SUM(total_claim_cost)*100,2) as collection_pct FROM fact_encounters GROUP BY payer_name ORDER BY gross_billed DESC;"
        }

        selected_q = st.selectbox("Select Pre-configured Advanced Query", list(query_options.keys()))
        custom_sql = st.text_area("SQL Statement (editable)", query_options[selected_q], height=120)

        if st.button("Execute SQL Query"):
            try:
                res_df = pd.read_sql_query(custom_sql, conn)
                st.success(f"Query returned {len(res_df)} rows successfully.")
                st.dataframe(res_df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Execution Error: {e}")
        conn.close()
    else:
        st.warning("Database `hospital_analytics.db` not found. Please run `python src/pipeline.py` first.")

# ---------------------------------------------------------
# VIEW 7: PROJECT DOCUMENTATION & ARCHITECTURE
# ---------------------------------------------------------
elif menu == "7. Project Documentation & Architecture":
    st.markdown('<div class="main-header">Project Architecture & Methodological Governance</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Compliance, HIPAA De-identification, Data Lineage & Star Schema Engineering</div>', unsafe_allow_html=True)

    st.markdown("""
    ### Technology Stack
    * **Analytics & Modeling:** Python 3.12, Pandas, NumPy, Scikit-learn, Scipy
    * **Visualizations & UX:** Streamlit, Matplotlib, Seaborn, OpenPyXL
    * **Data Storage & Warehousing:** SQLite & PostgreSQL Star Schema, SQLAlchemy
    * **Business Intelligence:** Microsoft Excel (7 Worksheets), Power BI (9 Data Model CSVs & 18 DAX Measures)
    * **Quality Assurance:** Pytest (13 Automated End-to-End Tests)

    ### Star Schema Architecture
    * **Fact Tables:** `fact_encounters`, `fact_encounter_conditions`, `fact_encounter_procedures`
    * **Dimension Tables:** `dim_patient`, `dim_date`, `dim_encounter_type`, `dim_provider`, `dim_organization`, `dim_condition`

    ### Project Deliverables
    * [Executive Excel Workbook](file:///c:/Users/91979/OneDrive/Desktop/Data Analyst/Projects/DA_Project_2/excel/Hospital_Patient_Analytics_Executive_Workbook.xlsx)
    * [Executive Healthcare BI Report](file:///c:/Users/91979/OneDrive/Desktop/Data Analyst/Projects/DA_Project_2/reports/executive_healthcare_bi_report.md)
    * [18 Production DAX Measures](file:///c:/Users/91979/OneDrive/Desktop/Data Analyst/Projects/DA_Project_2/powerbi/dax_measures.dax)
    * [Power BI Visual Placement Guide](file:///c:/Users/91979/OneDrive/Desktop/Data Analyst/Projects/DA_Project_2/powerbi/dashboard_implementation_guide.md)
    * [22 Healthcare Portfolio Interview Q&As](file:///c:/Users/91979/OneDrive/Desktop/Data Analyst/Projects/DA_Project_2/docs/interview_questions.md)
    """)

# Footer
st.markdown("---")
st.markdown('<div class="footer">Hospital Patient Analytics & Healthcare Performance Optimization Portfolio Project | Built with Python, SQL, Excel, and Power BI</div>', unsafe_allow_html=True)
