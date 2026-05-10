# TASK 4 Dashboard UI Rebuild Research

Date checked: May 10, 2026

## Streamlit docs checked
- `st.Page` + `st.navigation` preferred multipage approach:
  https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation
- Multipage overview:
  https://docs.streamlit.io/develop/concepts/multipage-apps/overview
- `st.Page` API:
  https://docs.streamlit.io/develop/api-reference/navigation/st.page
- `st.navigation` API:
  https://docs.streamlit.io/develop/api-reference/navigation/st.navigation

## Repo files inspected
- `dashboard/streamlit_app.py`
- `dashboard/pages/production_dashboard.py`
- `dashboard/pages/safety_status.py`
- `dashboard/pages/governance_status.py`
- `docker-compose.yml`
- `Dockerfile`
- `deploy/paper-runtime.env`
- `reports/phase47` through `reports/phase56`
- `artifacts/audit_validator_report.json`
- `docs/audit/latest_dependency_audit.json`
- `tests/test_dashboard_import.py`
- `tests/test_dashboard_xrpl.py`

## Problems found
- Landing experience included operational and governance concerns with weak separation.
- Production page surfaced artifact detail too early in flow.
- Repeated missing-state messaging reduced scanability.
- Safety view included details that should be drill-down only.
- Router/entrypoint was not using the preferred `st.Page` + `st.navigation` pattern.

## UI architecture decisions
- Use `st.Page` + `st.navigation` in `dashboard/streamlit_app.py` as primary router.
- Keep page order:
  1. Production Dashboard (default)
  2. Safety Status
  3. Governance Status
- Introduce loader modules under `dashboard/lib/`:
  - `canonical_loader.py`
  - `safety_loader.py`
  - `governance_loader.py`
- Introduce shared formatting/components for compact status-first rendering:
  - `artifact_formatting.py`
  - `ui_components.py`
- Restrict raw JSON to collapsed expanders only.

## Safety implications
- Dashboard remains read-only, artifact-backed, and offline/local-file sourced.
- No execution triggers, no submission controls, no mutation paths added.
- No changes made to:
  - `src/sonic_xrpl/execution/live_guard.py`
  - `app/execution/execution_guard.py`
  - `scripts/safety_grep.py` behavior for this UI rebuild
  - `src/sonic_xrpl/audit/safety_scan.py`

## Final layout chosen
- **Production Dashboard**: compact KPI row, signal status block, artifact availability block, raw signal artifact expander.
- **Safety Status**: overall safety posture + compact status board + evidence table + raw evidence expander.
- **Governance Status**: Phase 53-56 summary cards, lineage list, Phase 56 summary, raw governance expander.
