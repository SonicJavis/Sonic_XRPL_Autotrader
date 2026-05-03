# Roadmap

---

## Phase 45 — V2 Foundation Architecture Rebuild ✅ (this phase)

Establish the V2 package foundation, protocol capability matrix, provider contracts,
execution domain models, simulation interfaces, reconciliation bridge, and CLI.
All existing tests preserved. Live trading blocked.

---

## Phase 46 — Provider Integration and Offline Fixture Expansion

- Implement `XRPLRippledProvider` (optional live network read — no submission)
- Implement `ClioProvider` (historical data read via Clio WebSocket)
- Expand fixture library for common account/ledger/AMM states
- Add provider health monitoring and failover tests
- All fixtures loadable offline

---

## Phase 47 — XRPL Capability-Aware Market Snapshot Engine

- Implement capability-aware market data ingestion from LedgerProvider
- AMM pool snapshots (using `amm_info`)
- Orderbook depth snapshots (using `book_offers`)
- Price Oracle ingestion (using `get_aggregate_price`)
- MPT issuance snapshots
- Market snapshot caching and staleness management

---

## Phase 48 — Dependency Audit / Supply-Chain Guardrails ✅

Read-only audit of Python and Node dependency supply chain.
Detects compromised xrpl.js versions. Runs pip check and pip-audit.
Produces CI artifact reports. No runtime trading behaviour changed.

---

## Phase 49 — Strategy Signal Contracts over Market Snapshots

- MPT issuer profiling
- Clawback and freeze risk scoring
- AMMClawback risk assessment
- DeepFreeze trust-line risk
- Token trust score enrichment

---

## Phase 50 — Strategy Signal Contracts

- Implement first concrete strategy (e.g. simple AMM arbitrage signal)
- Strategy backtesting harness using walk-forward replay (Phase 44)
- Strategy registry with version tracking
- Signal confidence calibration

---

## Phase 51 — Risk Engine and Portfolio Constraints

- Position sizing constraints
- Portfolio-level risk limits
- Multi-asset exposure constraints
- Circuit breaker integration with strategy layer
- Risk approval audit trail

---

## Phase 52 — Realistic Simulation and Replay Harness

- AMM impact model using real pool state from fixtures
- Orderbook depth model using real fixture depth
- Fee escalation model (real load factor from fixture)
- Full end-to-end simulation pipeline with fixture-backed providers
- Deterministic replay across Phase 44 walk-forward dataset

---

## Phase 53 — Paper Trading Sandbox

- Full paper trading mode with realistic fill models
- Paper trade persistence (SQLite storage)
- Paper trade performance reporting
- Reconciliation V2 integration for paper vs simulated comparison

---

## Phase 54 — Reconciliation V2 and Execution Quality Reports

- Full V2 reconciliation pipeline
- Execution quality reports (fill rate, slippage, fee accuracy)
- Comparison with Phase 30 legacy reconciliation where applicable
- Exportable reports (JSON, Markdown)

---

## Phase 55 — Local Dashboard / Operator Console

- Streamlit dashboard integration with V2
- V2 health, capabilities, recent simulations display
- Paper trade P&L tracker
- Safety status panel

---

## Phase 56 — Live Readiness Checklist Only

- Structural verification checklist
- Provider connectivity tests (read-only)
- Amendment status verification
- Risk policy review
- **No live submission enabled in this phase**

---

## Phase 57 — Security Review Before Any Live Trading

- External or internal security audit
- Live guard review and sign-off
- Dependency audit
- Submission path implementation (behind new safety gates)
- **First phase where live trading may be considered**
