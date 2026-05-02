import streamlit as st
import json
from pathlib import Path

def load_dashboard_data():
    # Attempt to load the latest campaign dashboard data
    reports_dir = Path("reports/campaigns")
    if not reports_dir.exists():
        return None
        
    # Get latest campaign dir by time (assuming dir modification or just searching)
    camps = sorted([d for d in reports_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime)
    if not camps:
        return None
        
    latest_camp = camps[-1]
    dash_file = latest_camp / "campaign_dashboard_data.json"
    if dash_file.exists():
        with open(dash_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def main():
    st.set_page_config(page_title="Phase 39: Campaign Trust Dashboard", layout="wide")
    
    st.title("Phase 39: Operator Trust Dashboard & Campaign Runner")
    
    dash = load_dashboard_data()
    if not dash:
        st.warning("No campaign dashboard data found. Run the Campaign Runner CLI to generate a campaign.")
        return
        
    st.error(dash.get("safety_statement", "PAPER ONLY. NO WALLET. NO SIGNING. NO SUBMISSION. NO XAMAN PAYLOAD CREATION. LIVE TRADING FORBIDDEN."))
    
    # 1. Campaign Overview
    st.header("1. Campaign Overview")
    c_info = dash.get("campaign", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Campaign Status", c_info.get("status", "Unknown").upper())
    col2.metric("Cycle", f"{c_info.get('current_cycle', 0)} / {c_info.get('max_cycles', 0)}")
    col3.metric("Trust Score", str(dash.get("trust_score", "N/A")))
    col4.metric("Governor Decision", dash.get("governor_decision", "N/A").upper())
    
    st.caption(f"Campaign ID: `{c_info.get('campaign_id', 'Unknown')}`")
    
    # 2. Paper Performance
    st.header("2. Paper Performance")
    p_info = dash.get("paper_summary", {})
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Paper Balance (XRP)", p_info.get("balance", 0.0))
    p2.metric("Paper PnL (XRP)", p_info.get("pnl", 0.0))
    p3.metric("Open Positions", p_info.get("open", 0))
    p4.metric("Closed Positions", p_info.get("closed", 0))
    
    # 3. Risk Governor
    st.header("3. Risk Governor")
    r_info = dash.get("risk_summary", {})
    if r_info.get("critical"):
        st.error(f"Critical Failures: {', '.join(r_info.get('critical'))}")
    elif r_info.get("triggered"):
        st.warning(f"Triggered Warnings: {', '.join(r_info.get('triggered'))}")
    else:
        st.success("No risk rules triggered.")
        
    # 4. Strategy Leaderboard
    st.header("4. Strategy Leaderboard")
    s_info = dash.get("strategy_summary", {})
    st.write(f"**Best Performing Strategy:** {s_info.get('best_strategy')}")
    st.write(f"Unknown Outcome Rate: {s_info.get('unknown_rate', 0.0)}%")
    st.write(f"Metadata-Backed Success Rate: {s_info.get('metadata_backed_rate', 0.0)}%")
    
    if s_info.get("ranked"):
        st.table([{"Strategy": r.get("strategy_id"), "Score": r.get("risk_adjusted_score"), "Win Rate": r.get("win_rate")} for r in s_info.get("ranked")])
        
    # 5. Trade Journal
    st.header("5. Trade Journal Preview")
    tj = dash.get("trade_journal_preview", [])
    if tj:
        st.table([{"Candidate": t.get("candidate_id"), "Outcome": t.get("outcome"), "PnL %": t.get("paper_pnl_pct")} for t in tj])
    else:
        st.write("No trades logged yet.")
        
    # 6. Protocol Context
    st.header("6. Protocol Context Observed")
    for c in dash.get("protocol_context", []):
        st.write(f"- {c}")
        
    # 7. Limitations
    st.header("7. Limitations")
    for l in dash.get("limitations", []):
        st.write(f"- {l}")
        
    # 8. Market Fixtures (Phase 40 Optional)
    m_info = dash.get("market_fixture_summary")
    if m_info:
        st.header("8. Market Fixture Quality (Phase 40)")
        mq = m_info.get("quality_report", {})
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Quality Score", mq.get("quality_score", "N/A"))
        col2.metric("Assets Covered", mq.get("assets_covered", 0))
        col3.metric("Price Snapshots", mq.get("total_price_snapshots", 0))
        col4.metric("Liquidity Snapshots", mq.get("total_liquidity_snapshots", 0))
        
        if mq.get("warnings"):
            st.warning(f"Fixture Warnings: {', '.join(mq.get('warnings'))}")
            
    # 9. Backtest Dataset Quality (Phase 42 Optional)
    ds_info = dash.get("backtest_dataset_summary")
    if ds_info:
        st.header("9. Backtest Dataset Quality (Phase 42)")
        dq = ds_info.get("quality_report", {})
        dm = ds_info.get("manifest", {})
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Dataset Quality", dq.get("quality_score", "N/A"))
        col2.metric("Assets", dm.get("asset_count", 0))
        col3.metric("Candidates", dm.get("candidate_count", 0))
        col4.metric("Leakage Events", dq.get("future_leakage_count", 0))
        
        st.write(f"**Dataset ID:** `{dm.get('dataset_id')}`")
        st.write(f"**Version:** {dm.get('dataset_version')}")
        st.write(f"**Split Strategy:** {dm.get('split_strategy')}")
        
        if dq.get("critical_issues"):
            st.error(f"Critical Issues: {', '.join(dq.get('critical_issues'))}")
        if dq.get("warnings"):
            st.warning(f"Dataset Warnings: {', '.join(dq.get('warnings'))}")
        if dm.get("limitations"):
            st.info(f"Dataset Limitations: {', '.join(dm.get('limitations'))}")

    # 10. Strategy Tournament (Phase 43 Optional)
    ts_info = dash.get("tournament_summary")
    if ts_info:
        st.header("10. Strategy Tournament (Phase 43)")
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Dataset Quality", ts_info.get("dataset_quality_score", "N/A"))
        t2.metric("Strategies Evaluated", ts_info.get("strategies_evaluated", 0))
        t3.metric("Windows Evaluated", ts_info.get("windows_evaluated", 0))
        t4.metric("Critical Warnings", ts_info.get("critical_warning_count", 0))

        st.write(f"**Best Strategy:** `{ts_info.get('best_strategy_id') or 'N/A'}`")
        st.write(f"**Live Trading Readiness:** {ts_info.get('live_trading_readiness', '0/100')}")

        rec_counts = ts_info.get("recommendation_counts", {})
        if rec_counts:
            st.write("**Promotion Breakdown:**")
            for status, count in rec_counts.items():
                st.write(f"- {status}: {count}")

        if ts_info.get("critical_warning_count", 0) > 0:
            st.error(f"Critical overfitting warnings detected: {ts_info.get('critical_warning_count')}. Human review mandatory.")
        else:
            st.success("No critical overfitting warnings.")

        for lim in ts_info.get("limitations", []):
            st.caption(f"⚠ {lim}")

if __name__ == "__main__":
    main()
