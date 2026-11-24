# Hospital Patient Analytics — Data Cleaning & Pseudonymization Audit Report

## Executive Summary
This document details every cleaning transformation, de-identification rule, and business validation applied to the raw Synthea healthcare data pipeline.

## Pipeline Table Metrics

| Table Name | Raw Records | Cleaned Records | Retention Rate | Status |
|:---|---:|---:|---:|:---|
| `patients` | 1,200 | 1,200 | 100.0% | ✅ Cleaned |
| `encounters` | 5,960 | 5,960 | 100.0% | ✅ Cleaned |
| `conditions` | 4,501 | 4,501 | 100.0% | ✅ Cleaned |
| `procedures` | 2,970 | 2,970 | 100.0% | ✅ Cleaned |
| `medications` | 3,585 | 3,585 | 100.0% | ✅ Cleaned |
| `observations` | 26,780 | 26,780 | 100.0% | ✅ Cleaned |
| `organizations` | 6 | 6 | 100.0% | ✅ Cleaned |
| `providers` | 48 | 48 | 100.0% | ✅ Cleaned |

## Audit Trail of Applied Cleaning Rules

| Target Table | Cleaning Rule | Affected Rows | Clinical & Operational Rationale |
|:---|:---|---:|:---|
| `patients` | Deduplicate on Id | 0 | Ensure 1:1 patient entity integrity. |
| `patients` | Remove direct PII identifiers | 1,200 | Removed 9 direct identifier columns (SSN, DRIVERS, PASSPORT, PREFIX, FIRST, LAST, SUFFIX, MAIDEN, ADDRESS) to ensure HIPAA de-identification standards. |
| `patients` | Validate birth dates | 0 | Removed records with missing or future birth dates. |
| `patients` | Validate death dates against birth date | 0 | Nullified death dates occurring prior to birth. |
| `encounters` | Deduplicate encounter Id | 0 | Ensure unique encounter identity. |
| `encounters` | Enforce Patient Referential Integrity | 0 | Dropped encounters without valid matching patient record. |
| `encounters` | Drop null timestamps | 0 | Encounters require valid start and stop timestamps. |
| `encounters` | Correct inverted encounter timestamps (STOP < START) | 0 | Adjusted stop time to start time + 30 mins for logical operational validity. |
| `encounters` | Enforce encounter START >= patient BIRTHDATE | 32 | Adjusted encounters scheduled prior to birth date to post-birth date. |
| `conditions` | Filter orphaned patient keys | 0 | Removed conditions records without matching patient. |
| `conditions` | Filter orphaned encounter records | 0 | Removed conditions records referencing non-existent encounters. |
| `procedures` | Filter orphaned patient keys | 0 | Removed procedures records without matching patient. |
| `procedures` | Filter orphaned encounter records | 0 | Removed procedures records referencing non-existent encounters. |
| `medications` | Filter orphaned patient keys | 0 | Removed medications records without matching patient. |
| `medications` | Filter orphaned encounter records | 0 | Removed medications records referencing non-existent encounters. |
| `observations` | Filter orphaned patient keys | 0 | Removed observations records without matching patient. |
| `observations` | Filter orphaned encounter records | 0 | Removed observations records referencing non-existent encounters. |

## Pseudonymization & De-Identification Protocol
- **Direct Identifiers Stripped:** SSN, Driver's License, Passport, First/Last Name, Maiden Name, Exact Street Address, Phone.
- **Surrogate Key Derivation:** SHA-256 salted hash truncated to 12 hex characters prefixed with `PT_`.
- **HIPAA Safe Harbor Compliance:** All direct individual identifiers are permanently excluded from analytical datasets while retaining demographic fields (Birth year/month, Gender, Race, Ethnicity, County/Zip) essential for population health.
