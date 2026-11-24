# Dimensional Data Model Architecture
## Hospital Patient Analytics & Healthcare Performance Optimization

### 1. Conceptual & Dimensional Architecture
The data warehouse architecture follows the **Kimball Dimensional Modeling Methodology**, centered around a high-performance **Star Schema**. 

```
                                +-------------------+
                                |    Dim_Patient    |
                                +-------------------+
                                          | 1
                                          |
                                          | *
+--------------------+ 1        * +-------------------+ *        1 +--------------------+
|      Dim_Date      |------------|  Fact_Encounters  |------------| Dim_Encounter_Type |
+--------------------+            +-------------------+            +--------------------+
                                    | *           | *
                                    |             |
                                  1 |           1 |
               +--------------------+             +--------------------+
               |  Dim_Organization  |             |    Dim_Provider    |
               +--------------------+             +--------------------+
                         | 1                                | *
                         +----------------------------------+
                                        (Facility Affiliation)
```

---

### 2. Multi-Grain Fact & Bridge Architecture

```
                  +-----------------------------------+
                  |          Fact_Encounters          |
                  | (Grain: 1 Row per Completed Visit)|
                  +-----------------------------------+
                        | 1                       | 1
                        |                         |
                        | *                       | *
       +---------------------------------+   +---------------------------------+
       |    Fact_Encounter_Conditions    |   |    Fact_Encounter_Procedures    |
       | (Grain: 1 Row per Diagnosis)    |   | (Grain: 1 Row per Procedure)    |
       +---------------------------------+   +---------------------------------+
                        | *
                        |
                        | 1
              +-------------------+
              |   Dim_Condition   |
              +-------------------+
```

### 3. Design Rationales & Solutions
1. **Preventing Double-Counting in Joins:**  
   In transactional healthcare systems, an inpatient admission often carries multiple ICD/SNOMED diagnostic codes and CPT procedure codes. Joining conditions directly into encounters causes cartesian fan-out, multiplying billed charges. By isolating diagnoses in `Fact_Encounter_Conditions` with foreign keys to `Fact_Encounters` and `Dim_Condition`, financial aggregations remain accurate.
2. **Surrogate Key Implementation:**  
   Natural IDs (such as raw patient UUIDs and social identifiers) are discarded at the staging boundary. Surrogate keys (`patient_key`, `date_key`) improve query join performance and decouple analytical queries from source system key volatility.
3. **Calendar Dimension Integration:**  
   The `date_key` (smart integer `YYYYMMDD`) maps directly to `Dim_Date`, supporting fiscal quarters, day-of-week, weekend flags, and longitudinal moving-average window calculations.
