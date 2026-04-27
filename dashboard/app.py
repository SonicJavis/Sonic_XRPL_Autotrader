from __future__ import annotations

import random

import streamlit as st

def main() -> None:
	st.set_page_config(page_title="Sonic XRPL Autotrader", page_icon="S", layout="wide")

	st.title("Sonic XRPL Autotrader Dashboard")
	st.caption("Local scaffold dashboard for status and quick sanity checks.")

	col1, col2, col3 = st.columns(3)
	col1.metric("Bot Status", "READY")
	col2.metric("Network", "Testnet")
	col3.metric("Last Signal", random.choice(["BUY", "SELL", "HOLD"]))

	st.subheader("Recent Prices")
	prices = [round(0.5 + random.uniform(-0.08, 0.08), 4) for _ in range(50)]
	st.line_chart(prices)


if __name__ == "__main__":
	main()
