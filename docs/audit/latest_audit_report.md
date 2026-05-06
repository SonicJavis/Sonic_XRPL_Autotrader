# V2 Audit Report

**Timestamp**: 2026-05-06T11:39:26.565682+00:00
**Overall**: ✅ PASSED
**Checks**: 29 passed / 0 failed / 0 warnings

## Check Results

- ✅ `doc:docs/PROJECT_BLUEPRINT.md`: OK: docs/PROJECT_BLUEPRINT.md
- ✅ `doc:docs/V2_ARCHITECTURE.md`: OK: docs/V2_ARCHITECTURE.md
- ✅ `doc:docs/PHASE_LEDGER.md`: OK: docs/PHASE_LEDGER.md
- ✅ `doc:docs/AGENT_OPERATING_RULES.md`: OK: docs/AGENT_OPERATING_RULES.md
- ✅ `doc:docs/SAFETY_MODEL.md`: OK: docs/SAFETY_MODEL.md
- ✅ `doc:docs/ROADMAP.md`: OK: docs/ROADMAP.md
- ✅ `doc:docs/research/XRPL_RESEARCH_BASELINE.md`: OK: docs/research/XRPL_RESEARCH_BASELINE.md
- ✅ `doc:docs/audit/pre_v2_repository_audit.md`: OK: docs/audit/pre_v2_repository_audit.md
- ✅ `doc:docs/audit/latest_audit_report.md`: OK: docs/audit/latest_audit_report.md
- ✅ `doc:docs/audit/latest_audit_report.json`: OK: docs/audit/latest_audit_report.json
- ✅ `doc:docs/PHASE46_PROVIDER_FIXTURES.md`: OK: docs/PHASE46_PROVIDER_FIXTURES.md
- ✅ `doc:docs/research/PHASE46_PROVIDER_FIXTURE_RESEARCH.md`: OK: docs/research/PHASE46_PROVIDER_FIXTURE_RESEARCH.md
- ✅ `import:sonic_xrpl`: OK: sonic_xrpl
- ✅ `import:sonic_xrpl.core.modes`: OK: sonic_xrpl.core.modes
- ✅ `import:sonic_xrpl.core.errors`: OK: sonic_xrpl.core.errors
- ✅ `import:sonic_xrpl.protocol.amendments`: OK: sonic_xrpl.protocol.amendments
- ✅ `import:sonic_xrpl.protocol.capability_matrix`: OK: sonic_xrpl.protocol.capability_matrix
- ✅ `import:sonic_xrpl.execution.live_guard`: OK: sonic_xrpl.execution.live_guard
- ✅ `import:sonic_xrpl.providers.mocks`: OK: sonic_xrpl.providers.mocks
- ✅ `import:sonic_xrpl.reconciliation.legacy_phase30_adapter`: OK: sonic_xrpl.reconciliation.legacy_phase30_adapter
- ✅ `cli:main --help`: OK: CLI --help works
- ✅ `mode:default_is_intelligence_only`: Default mode: intelligence_only
- ✅ `live_guard:submit_blocked`: OK: assert_can_submit(LIVE) raises as expected
- ✅ `capability_matrix:exists`: OK: 20 capabilities
- ✅ `capability_matrix:obsolete_not_enabled`: OK: no obsolete amendments marked enabled
- ✅ `reconciliation:bridge_exists`: OK: legacy_phase30_adapter.py exists
- ✅ `reconciliation:bridge_importable`: OK: LEGACY_AVAILABLE=True
- ✅ `dep:xrpl.js check`: No package.json/lockfile found — no xrpl.js to check
- ✅ `security:no_seed_impl`: OK: no seed/private-key implementation found in src/sonic_xrpl/