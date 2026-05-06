# Phase 49 — FirstLedger Signal Research

Date checked: 2026-05-06. Phase 49 is evidence/signal only: no wallet, Xaman payload, signing, submission, auto-buy, live order placement, background loop, or live FirstLedger polling was added.

## Repository-local findings

| Source | Key point | Architecture impact | Status |
|---|---|---|---|
| `AGENTS.md` | Work must preserve simulation/live separation, avoid secrets, and run safety grep. | Signal contracts keep `live_execution_allowed=False` and remain offline. | Implemented now |
| `README.md` | Project remains safety-first and simulation-oriented. | Signals are advisory inputs for future simulation/paper phases, not execution. | Implemented now |
| `docs/AGENT_WORKFLOW.md` | GitHub branch/PR workflow is documented. | Phase branch and PR workflow used where credentials permit. | Implemented now |
| `docs/ROADMAP.md` | Phase 48/49 naming needed reconciliation after FirstLedger boundary work. | Updated roadmap to name Phase 49 as evidence-backed FirstLedger candidate risk + signal contracts. | Implemented now |
| `docs/PHASE_LEDGER.md` | Phase 48 and dependency audit addendum are recorded. | Added Phase 49 entry and rollback notes. | Implemented now |
| `docs/V2_ARCHITECTURE.md` | V2 layers separate ingestion/market/protocol/risk/strategy/execution. | Added `src/sonic_xrpl/signals/` as a non-executing evidence layer. | Implemented now |
| `docs/SAFETY_MODEL.md` | Live trading boundary must remain blocked. | Signal model hard-codes live execution denial. | Implemented now |
| `docs/PROJECT_BLUEPRINT.md` | Project plans phased architecture and safety. | Phase 49 prepares future simulation/paper decisions only. | Implemented now |
| `docs/PHASE48_FIRSTLEDGER_DISCOVERY.md` | FirstLedger parser is strict and source-backed; missing `observed_at` remains missing. | Evidence layer preserves `observed_at_missing` and does not synthesize event times. | Implemented now |
| `execution_prototype/discovery/firstledger_reader.py` | Parser accepts only rows with issuer, currency, ledger, tx hash, and supported event type. | Phase 49 consumes parser events and separately models rejected/incomplete rows as insufficient evidence. | Implemented now |
| `tests/test_firstledger_reader.py` | Strict tests prove fake launches are not invented and missing `observed_at` stays missing. | Added signal tests that extend this boundary. | Implemented now |
| `src/sonic_xrpl/market/` | Phase 47 market snapshots are offline fixture snapshots with quality limitations. | Signal scoring credits market context only when an explicit snapshot matches a candidate. | Implemented now |
| `src/sonic_xrpl/protocol/` | Capability matrix and amendments gate protocol assumptions. | Scoring remains conservative around trustline/protocol risk. | Implemented now |
| `src/sonic_xrpl/risk/` | Risk/pretrade modules do not authorize Phase 49 execution. | Signals are not wired into pretrade execution. | Research-only |
| `src/sonic_xrpl/execution/live_guard.py` | Live execution guard blocks live network execution. | Not modified except tests cover signal layer remains non-executing. | Implemented now |

## XRPL primary-source findings

| Source URL | Date checked | Key point | Architecture impact | Status |
|---|---:|---|---|---|
| https://xrpl.org/known-amendments.html | 2026-05-06 | Known amendments are the primary reference for protocol feature availability. | Do not assume protocol features without capability evidence. | Implemented now |
| https://xrpl.org/docs/concepts/networks-and-servers/amendments | 2026-05-06 | Protocol amendments require network activation before applications rely on them. | Feature-gate future strategy/risk code. | Feature-gated |
| https://xrpl.org/docs/concepts/tokens/decentralized-exchange/automated-market-makers | 2026-05-06 | XRPL AMMs provide DEX liquidity and use constant-product-like mechanics. | Do not infer liquidity without explicit AMM/snapshot evidence. | Implemented now |
| https://xrpl.org/docs/concepts/tokens | 2026-05-06 | XRPL supports trust line tokens, MPTs, and NFTs; token semantics differ. | Candidate currency/issuer evidence must be explicit. | Implemented now |
| https://xrpl.org/docs/concepts/tokens/fungible-tokens/trust-line-tokens | 2026-05-06 | Trust line tokens require trust lines and have issuer/account-level settings. | Issuer/trustline risk cannot be guessed from a symbol alone. | Implemented now |
| https://xrpl.org/docs/references/protocol/transactions/types/trustset/ | 2026-05-06 | TrustSet creates or modifies trust lines and includes freeze/no-ripple flags. | Trustline risk evidence is only scored when source-backed. | Implemented now |
| https://xrpl.org/docs/concepts/tokens/fungible-tokens/clawing-back-tokens | 2026-05-06 | Clawback is issuer-controlled and must be enabled under protocol rules. | Clawback risk is a penalty only when explicit evidence exists. | Implemented now |
| https://xrpl.org/docs/references/protocol/transactions/types/ammclawback | 2026-05-06 | AMMClawback can claw issued tokens from AMM pool positions when enabled. | AMM pool “safe liquidity” must not be claimed from incomplete data. | Implemented now |
| https://xrpl.org/docs/concepts/tokens/fungible-tokens/freezes/ | 2026-05-06 | Issuers can freeze trust line tokens; XRP cannot be frozen. | Freeze evidence is avoid/penalty-level when source-backed. | Implemented now |
| https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens | 2026-05-06 | MPTs have separate issuance IDs and compliance controls. | Do not treat MPTs as ordinary issuer/currency pairs without evidence. | Research-only |
| https://xrpl.org/docs/concepts/decentralized-storage/price-oracles | 2026-05-06 | Price Oracles store on-chain price data supplied by providers. | Future scoring may include oracle evidence, but Phase 49 does not fetch it. | Feature-gated |
| https://xrpl.org/docs/references/protocol/transactions/metadata | 2026-05-06 | Transaction metadata is final only in validated ledgers; delivered amounts require metadata care. | Metadata status is required for high-confidence signals. | Implemented now |
| https://xrpl.org/docs/concepts/payment-types/partial-payments/ | 2026-05-06 | Partial payments require using `delivered_amount` rather than naive Amount assumptions. | Do not infer liquidity/volume from raw payment amount. | Implemented now |
| https://xrpl.org/docs/concepts/transactions/reliable-transaction-submission/ | 2026-05-06 | Reliable submission covers signing/submission lifecycle. | Not used; reinforces that Phase 49 must not submit. | Not applicable |
| https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/account-methods/account_tx/ | 2026-05-06 | `account_tx` returns validated account transactions; some filters are Clio-only. | Historical evidence should record server/API limitations. | Research-only |
| https://github.com/XRPLF/rippled/releases | 2026-05-06 | Release notes are the primary source for latest server behavior and urgent upgrades. | Keep protocol matrix reviewed in later safety phases. | Research-only |
| https://xrpl.org/docs/infrastructure/clio | 2026-05-06 | Clio serves validated historical data but is not a transaction-submitting server. | Future history adapters should distinguish Clio/rippled capabilities. | Research-only |

## GitHub and standards findings

| Source URL | Date checked | Key point | Architecture impact | Status |
|---|---:|---|---|---|
| https://github.com/XRPLF/rippled | 2026-05-06 | Reference server implementation and releases are authoritative for protocol implementation. | Protocol assumptions should cite rippled/XRPL docs. | Research-only |
| https://github.com/XRPLF/clio | 2026-05-06 | Clio is a historical API server; behavior can differ from rippled APIs. | Treat historical account data source as capability-specific. | Research-only |
| https://github.com/XRPLF/xrpl-py | 2026-05-06 | Python client can sign/submit, so imports must not be used casually in signal layer. | Phase 49 does not import client signing/submission. | Implemented now |
| https://github.com/XRPLF/xrpl.js | 2026-05-06 | xrpl.js is a JS client library; supply-chain security matters. | Project is Python-only here; dependency audit remains important. | Research-only |
| https://xrpl.org/blog/2025/vulnerabilitydisclosurereport-bug-apr2025 | 2026-05-06 | Public disclosure documented malicious `xrpl` npm package compromise. | Do not add JS wallet/signing dependencies; keep dependency audit. | Implemented now |
| https://github.com/XRPLF/XRPL-Standards | 2026-05-06 | XLS standards include draft/final statuses; not all are mainnet capabilities. | Standards inform future work but do not override amendment status. | Research-only |
| https://xls.xrpl.org/ | 2026-05-06 | XLS registry lists status and category for XRPL standards. | Treat draft/proposal standards as research-only unless enabled. | Research-only |

## Hooks / Xahau finding

| Source URL | Date checked | Key point | Architecture impact | Status |
|---|---:|---|---|---|
| https://docs.xahau.network/features/network-features/hooks | 2026-05-06 | Hooks are a Xahau feature with SetHook/Invoke transaction types. | Hooks/Xahau are separate ecosystem research and not XRPL mainnet capability for Phase 49. | Not applicable |

## FirstLedger finding

| Source URL | Date checked | Key point | Architecture impact | Status |
|---|---:|---|---|---|
| https://firstledger.net/ | 2026-05-06 | Public web presence exists, but no stable public API contract was verified in this session. | Keep implementation fixture/source-backed only; do not scrape or poll. | Implemented now |
| https://www.reddit.com/r/XRP/search/?q=First%20Ledger | 2026-05-06 | Public discussion exists but is not authoritative candidate data. | Do not use social posts as launch metrics or buy evidence. | Research-only |

## Implementation decisions from research

- Signals are deterministic advisory contracts only.
- `BUY_CANDIDATE` requires explicit candidate fields, validated metadata, no critical limitation, and market snapshot context.
- Missing `observed_at` remains an explicit limitation and is not replaced with processing time.
- Synthetic fixtures are labelled and blocked from `BUY_CANDIDATE`.
- No live FirstLedger API, XRPL client, Xaman integration, signing, submission, auto-buy, wallet handling, or background loop was added.

## Verification TODOs

- Re-check FirstLedger for an official, documented, rate-limited public API before any future adapter.
- Re-check XRPL amendment statuses and latest rippled/Clio release notes before live-network or backtest expansion.
