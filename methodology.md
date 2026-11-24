# Analytical & Engineering Methodology
## Hospital Patient Analytics & Healthcare Performance Optimization

### 1. Data Ingestion & Immutability Standard
Raw data is ingested directly from MITRE Synthea CSV outputs without in-place modification. The raw landing zone (`data/raw/`) is strictly treated as an immutable append-only data store. Data schema verification enforces required columns and logs missing values and duplicate keys.

---

### 2. Data Cleaning & De-Identification Protocol
1. **Deduplication:** Primary key deduplication ensures 1:1 entity validity for patients and encounters.
2. **De-Identification:** Strip direct PII fields (SSN, Driver's License, Passport, First/Last Name, Street Address, Phone) in compliance with HIPAA Safe Harbor standards.
3. **Surrogate Key Generation:** Compute SHA-256 salted hashes of original identifiers, truncated to 12 uppercase hex characters with prefix `PT_`.
4. **Chronological Realignment:** Enforce `STOP >= START` and `START >= BIRTHDATE`. Encounters scheduled prior to birth or with inverted timestamps are logically adjusted or dropped.
5. **Cost Sanitization:** Enforce non-negative amounts across base cost, gross claims, payer coverage, and patient payments.

---

### 3. Feature Engineering & Clinical Metric Formulas
- **Exact Age at Encounter:**
  $$\text{Age} = \left\lfloor \frac{\text{Encounter Start Date} - \text{Patient Birth Date}}{365.25} \right\rfloor$$
- **Encounter Duration & Inpatient Length of Stay (LOS):**
  $$\text{Duration (Hours)} = \frac{\text{Encounter Stop} - \text{Encounter Start}}{3600}$$
  $$\text{LOS (Days)} = \frac{\text{Inpatient Discharge} - \text{Inpatient Admission}}{86400}$$
- **Revenue Decomposition:**
  $$\text{Patient Responsibility} = \max\left(0, \text{Total Claim Cost} - \text{Payer Coverage}\right)$$
  $$\text{Payer Collection Ratio} = \frac{\text{Payer Coverage}}{\text{Total Claim Cost}}$$

---

### 4. Advanced Analytics & Machine Learning Methodology

#### 4.1 K-Means Healthcare Utilization Clustering
- **Feature Vector:** Recency (days since last visit), Frequency (lifetime visits), Monetary (lifetime billed charges), Inpatient count, Emergency count.
- **Preprocessing:** Standardized with `StandardScaler` ($\mu = 0$, $\sigma = 1$).
- **Model Selection Diagnostics:**
  - Inertia Elbow method evaluated across $k \in [2, 6]$.
  - Silhouette coefficients calculated to measure inter-cluster separation and intra-cluster cohesion.
  - Optimal selection: $k = 4$, balancing mathematical separation with clinical interpretability.
- **Reproducibility:** Seed fixed at `RANDOM_STATE = 42`.

#### 4.2 Longitudinal Cohort Retention Analysis
- **Cohort Inception:** Defined by calendar month of patient's first recorded encounter.
- **Retention Index:**
  $$\text{Retention Rate}_{c, m} = \frac{\text{Unique Active Patients in Month } m}{\text{Total Patients in Inception Month } c} \times 100$$

#### 4.3 30-Day Post-Acute Re-encounter Indicator
- **Eligibility:** Patient must have an index acute stay (Inpatient or Emergency) and must have survived past discharge.
- **Window:** Any subsequent encounter occurring within $[1, 30]$ days following index discharge timestamp.
- **Methodological Scope:** Evaluates general system re-encounter rates across all outpatient and acute modalities.
