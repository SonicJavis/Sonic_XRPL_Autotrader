from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.lib.artifact_formatting import normalize_display_value


STATUS_COLORS = {
    "pass": "🟢 PASS",
    "fail": "🔴 FAIL",
    "warn": "🟠 WARN",
    "unknown": "⚪ UNKNOWN",
    "unavailable": "⚪ Unavailable",
}


def status_to_color(status: str) -> str:
    return STATUS_COLORS.get(status.lower(), STATUS_COLORS["unknown"])


def render_page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)


def render_kpi_card(label: str, value: Any, helper: str | None = None, status: str = "neutral") -> None:
    shown = normalize_display_value(value)
    st.metric(label, shown)
    if helper:
        st.caption(helper)
    if status in {"pass", "fail", "warn", "unknown"}:
        st.caption(status_to_color(status))


def render_status_card(title: str, status: str, reason: str) -> None:
    st.metric(title, status_to_color(status))
    st.caption(reason)


def render_artifact_expander(title: str, artifact: Any, source_path: str | None = None) -> None:
    with st.expander(title, expanded=False):
        if source_path:
            st.caption(f"Source: {source_path}")
        if artifact is None:
            st.caption("Unavailable")
        else:
            st.json(artifact)
