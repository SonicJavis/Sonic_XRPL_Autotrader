# TASK 4 Operator Dashboard Unification

## Summary
Task 4 rebuilds the operator dashboard into a strictly read-only, operator-first interface with separated concerns:
- Production metrics on landing page
- Safety board on dedicated page
- Governance lineage on dedicated page

No execution controls, signing paths, submission paths, or mutation controls were added.

## Information Architecture
- Router: `dashboard/streamlit_app.py` using `st.Page` + `st.navigation` when available.
- Default page: **Production Dashboard**
- Additional pages:
  - **Safety Status**
  - **Governance Status**

## Data Source Policy
All values are loaded from immutable local artifacts only:
- `reports/phase47` ... `reports/phase56`
- `artifacts/audit_validator_report.json`
- `docs/audit/latest_dependency_audit.json`

No network calls are used by dashboard loaders.
No file writes are performed by dashboard loaders.

## Page Contracts

### Production Dashboard
- KPI row:
  - Alpha Score (24h proxy)
  - Risk Decisions Blocked
  - Risk Decisions Allowed
  - Paper PnL Attribution
- Signal review summary
- Artifact availability summary
- Raw signal artifact in collapsed expander only

### Safety Status
- Overall pass/fail posture
- Compact status cards:
  - Kill Switch State
  - ExecutionGuard
  - live_guard
  - Audit Validator
  - Safety Scan
  - Dependency Audit
- Evidence table
- Raw safety evidence in collapsed expander only

### Governance Status
- Summary cards:
  - Calibration Queue
  - Proposal Records
  - Approval Records
  - Phase 56 Items
- Phase 53-56 lineage list
- Phase 56 plan summary
- Raw governance artifacts in collapsed expander only

## Safety Notes
- Dashboard remains observation-only.
- Runtime guards and scanner modules were not modified.
- Any missing safety evidence must be treated as non-green.

## Known limitation
Some production KPIs depend on available report fields and can display `Unavailable` when source-backed values are absent.
