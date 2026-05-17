from __future__ import annotations
import json
from pathlib import Path
from sonic_xrpl.xaman_governance_final_readiness_review_export_spec.models import XamanGovernanceFinalReadinessReviewExportReport, jsonable
from sonic_xrpl.xaman_governance_final_readiness_review_export_spec.traceability import render_traceability_map

def render_xaman_governance_final_readiness_review_export_payload(report: XamanGovernanceFinalReadinessReviewExportReport):
    f=report.spec.safety_flags
    return {"fixture_id":report.fixture_id,"phase":report.spec.phase,"export_package_id":report.spec.export_package_id,"manifest_id":report.spec.manifest.manifest_id,"deterministic_timestamp":report.spec.deterministic_timestamp,"export_readiness_classification":report.export_readiness_classification,"validation_errors":list(report.validation_errors),"blockers":list(report.blockers),
        "spec_only":f.spec_only,"review_export_spec_only":f.review_export_spec_only,"runtime_export_service_allowed":f.runtime_export_service_allowed,"download_service_allowed":f.download_service_allowed,"api_route_allowed":f.api_route_allowed,"dashboard_ui_allowed":f.dashboard_ui_allowed,"safety_bypass_allowed":f.safety_bypass_allowed,"testnet_execution_allowed":f.testnet_execution_allowed,"xaman_payload_creation_allowed":f.xaman_payload_creation_allowed,"xaman_api_calls_allowed":f.xaman_api_calls_allowed,"xaman_sdk_dependency_allowed":f.xaman_sdk_dependency_allowed,"signing_allowed":f.signing_allowed,"submission_allowed":f.submission_allowed,"autofill_allowed":f.autofill_allowed,"wallet_material_allowed":f.wallet_material_allowed,"live_execution_allowed":f.live_execution_allowed,"runtime_mutation_allowed":f.runtime_mutation_allowed,"traceability_map":render_traceability_map(report),"spec":jsonable(report.spec)}

def render_xaman_governance_final_readiness_review_export_json(report):
    return json.dumps(render_xaman_governance_final_readiness_review_export_payload(report),indent=2,sort_keys=True)

def render_xaman_governance_final_readiness_review_export_markdown(report):
    p=render_xaman_governance_final_readiness_review_export_payload(report)
    lines=["# Phase 76 Xaman Governance Final Readiness Review Export Spec","",f"- Fixture: `{p['fixture_id']}`",f"- Export package ID: `{p['export_package_id']}`",f"- Manifest ID: `{p['manifest_id']}`",f"- Export readiness classification: `{p['export_readiness_classification']}`",f"- spec_only: `{p['spec_only']}`",f"- review_export_spec_only: `{p['review_export_spec_only']}`",f"- runtime_export_service_allowed: `{p['runtime_export_service_allowed']}`",f"- download_service_allowed: `{p['download_service_allowed']}`",f"- api_route_allowed: `{p['api_route_allowed']}`",f"- dashboard_ui_allowed: `{p['dashboard_ui_allowed']}`","","## Validation Errors"]
    lines += [f"- {i}" for i in (p["validation_errors"] or ["none"])]
    lines += ["","## Final Confirmation","- Still no live execution.","- Still no testnet execution.","- Still no Xaman payload creation.","- Still no runtime export service.","- Still no download service.","- Still no API/UI export route.","- Still no safety bypass."]
    return "\n".join(lines)

def write_xaman_governance_final_readiness_review_export_reports(report, output_dir: str | Path="reports/phase76"):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    j=out/'latest_xaman_governance_final_readiness_review_export_spec.json'; m=out/'latest_xaman_governance_final_readiness_review_export_spec.md'
    j.write_text(render_xaman_governance_final_readiness_review_export_json(report),encoding='utf-8'); m.write_text(render_xaman_governance_final_readiness_review_export_markdown(report),encoding='utf-8')
    return j,m
