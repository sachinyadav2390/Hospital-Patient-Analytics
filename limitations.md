# Project Limitations & Healthcare Governance Disclaimers
## Hospital Patient Analytics & Healthcare Performance Optimization

### 1. Synthetic Healthcare Data Caveats (MITRE Synthea)
- **Synthetic Nature:** All records are generated using the MITRE Synthea open-source synthetic patient generator. While clinically modeled after Massachusetts epidemiological curves, individual records do not represent real human biology or clinical records.
- **Rule-Based Physiological Simulation:** Observations (blood pressure, glucose, BMI) follow algorithmic distributions and do not reflect idiosyncratic clinical complications or complex poly-pathological drug interactions.

---

### 2. Operational & Attribution Boundaries
- **Clinical Department Mapping:** Hospital departments (e.g., Department of Internal Medicine, Heart & Vascular Institute) are mapped via the attending practitioner's primary medical specialty. This approximates clinical cost centers but does not mirror internal hospital general ledger (GL) departmental charge allocations.
- **No Direct Bed Occupancy or Waiting Times:** The source dataset does not contain physical hospital room IDs, bed turn turnaround logs, or ED triage triage-to-physician wait times. In strict adherence to analytical integrity, we do not fabricate bed occupancy rates or waiting times without direct source field backing.

---

### 3. Regulatory & Quality Measure Distinctions
- **30-Day Re-encounter Rate vs. CMS HRRP Readmissions:**  
  The 30-day indicator reported here measures whether an acute patient had *any* subsequent healthcare contact (including routine primary care follow-up or planned elective therapy) within 30 days post-discharge.  
  > [!IMPORTANT]
  > This is **NOT** equivalent to the Centers for Medicare & Medicaid Services (CMS) Hospital Readmissions Reduction Program (HRRP) measure. CMS HRRP strictly defines unplanned, all-cause acute inpatient readmissions to any short-stay acute hospital and adjusts for patient age, comorbid conditions, and elective procedure exclusions using hierarchical generalized linear models.

---

### 4. Financial & Revenue Cycle Boundaries
- **Gross Billed Charges vs. Net Collections:**  
  The `total_claim_cost` field represents gross chargemaster billed amounts. In actual healthcare finance, contractual allowances, statutory fee schedules (Medicare MS-DRG, Medicaid APG), and commercial carve-outs discount billed charges significantly. Net recognized revenue typically represents 20% to 35% of gross billed charges in commercial settings.
