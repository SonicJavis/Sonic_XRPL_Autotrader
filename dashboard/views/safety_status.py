from __future__ import annotations

import streamlit as st

from dashboard.lib.safety_loader import load_safety_snapshot
from dashboard.lib.ui_components import (
    render_artifact_expander,
    render_page_header,
    render_status_card,
    status_to_color,
)


def main() -> None:
    st.set_page_config(page_title="Safety Status", page_icon="S", layout="wide")
    payload = load_safety_snapshot()

    render_page_header(
        "Safety Status",
        "Fail-closed runtime and audit state for the paper-only deployment.",
    )

    overall_status = payload.get("overall_status", "review")
    st.metric("Overall Safety Posture", status_to_color(overall_status))

    cols = st.columns(3)
    items = list(payload.get("checks", {}).items())
    for idx, (label, data) in enumerate(items):
        status = data.get("status", "review")
        reason = data.get("reason", "Evidence unavailable")
        with cols[idx % 3]:
            render_status_card(label, status, reason)

    st.subheader("Evidence")
    rows = []
    for key, artifact in payload.get("artifacts", {}).items():
        path = artifact.get("path")
        found = artifact.get("found", False)
        linked_check = {
            "phase56": "Kill Switch State",
            "phase55": "Safety Scan",
            "audit_validator_report": "Audit Validator",
            "dependency_audit_report": "Dependency Audit",
        }.get(key)
        check_status = payload.get("checks", {}).get(linked_check, {}).get("status", "review")
        rows.append(
            {
                "artifact": key,
                "path": path,
                "found": "yes" if found else "no",
                "status": check_status.upper(),
            }
        )
    st.dataframe(rows, use_container_width=True)

    render_artifact_expander("Raw Safety Evidence", payload.get("raw"))
    st.caption("Any missing or failed safety evidence must be treated as non-green.")


if __name__ == "__main__":
    main()
