# Hospital Patient Analytics — Data Ingestion & Inventory Audit
**Dataset:** MITRE Synthea Synthetic Healthcare Simulation
**Total Tables:** 8

| Table Name | Row Count | Column Count | Primary Key | PK Duplicates | Missing Req Cols | Schema Status |
|:---|---:|---:|:---|---:|:---|:---|
| `patients` | 1,200 | 26 | `Id` | 0 | None | ✅ PASS |
| `encounters` | 5,960 | 15 | `Id` | 0 | None | ✅ PASS |
| `conditions` | 4,501 | 6 | `Composite / Event` | 0 | None | ✅ PASS |
| `procedures` | 2,970 | 8 | `Composite / Event` | 0 | None | ✅ PASS |
| `medications` | 3,585 | 13 | `Composite / Event` | 0 | None | ✅ PASS |
| `observations` | 26,780 | 8 | `Composite / Event` | 0 | None | ✅ PASS |
| `organizations` | 6 | 11 | `Id` | 0 | None | ✅ PASS |
| `providers` | 48 | 12 | `Id` | 0 | None | ✅ PASS |

## Missing Values Profile

### Table `patients`
| Column | Missing Rows | Null % |
|:---|---:|---:|
| `DEATHDATE` | 1,175 | 97.92% |
| `SUFFIX` | 1,200 | 100.00% |
| `MAIDEN` | 1,023 | 85.25% |

### Table `conditions`
| Column | Missing Rows | Null % |
|:---|---:|---:|
| `STOP` | 3,207 | 71.25% |

