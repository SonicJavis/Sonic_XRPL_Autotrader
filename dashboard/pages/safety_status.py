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

    st.metric("Overall Safety Posture", status_to_color(payload.get("overall_status", "unknown")))

    cols = st.columns(3)
    items = list(payload.get("checks", {}).items())
    for idx, (label, data) in enumerate(items):
        ok, reason = data
        status = "pass" if ok else "fail"
        with cols[idx % 3]:
            render_status_card(label, status, reason)

    st.subheader("Evidence")
    rows = []
    for key, path in payload.get("artifacts", {}).items():
        raw = payload.get("raw", {}).get(key if key != "phase55" else "phase55")
        rows.append(
            {
                "artifact": key,
                "path": path,
                "found": "yes" if raw is not None else "no",
                "status": "PASS" if raw is not None else "FAIL",
            }
        )
    st.dataframe(rows, use_container_width=True)

    render_artifact_expander("Raw Safety Evidence", payload.get("raw"))
    st.caption("Any missing or failed safety evidence must be treated as non-green.")


if __name__ == "__main__":
    main()
