# XRPL Research Baseline — Phase 45

**Last updated**: 2026-05-02  
**Phase**: 45 — V2 Foundation Architecture Rebuild  
**Methodology**: Offline review of primary sources. Live network state not queried.

---

## Important Disclaimer

This is a research baseline only. Protocol status on mainnet changes via validator voting.
Do not make live trading decisions based solely on this document.
Always query the live network for current amendment and ledger state.

---

## 1. XRPL Amendments

**Source**: https://xrpl.org/known-amendments.html  
**Date checked**: 2026-05-02 (offline research)

### Enabled on Mainnet

| Amendment | XLS | Source | Architecture Impact | Status |
|-----------|-----|--------|---------------------|--------|
| AMM | XLS-30 | https://xrpl.org/known-amendments.html#amm | AMM pools queryable; paper/sim trading can model AMM fills | Implemented (feature-gated for sim) |
| AMMClawback | XLS-73 | https://xrpl.org/known-amendments.html#ammclawback | Risk layer must check issuer clawback on AMM assets | Feature-gated |
| Clawback | — | https://xrpl.org/known-amendments.html#clawback | Intelligence layer must flag clawback-enabled tokens | Feature-gated |
| Credentials | XLS-70 | https://xrpl.org/known-amendments.html#credentials | Required for PermissionedDEX; risk layer integration point | Feature-gated |
| DID | — | https://xrpl.org/known-amendments.html#did | On-chain identity objects; research-only for trading | Research-only |
| DeepFreeze | — | https://xrpl.org/known-amendments.html#deepfreeze | Risk layer must check deep-freeze status of trust lines | Feature-gated |
| ExpandedSignerList | — | https://xrpl.org/known-amendments.html#expandedsignerlist | Larger multisig lists; relevant only if wallet construction enabled | Research-only |
| MPTokensV1 | — | https://xrpl.org/known-amendments.html#mptokensv1 | MPT issuances queryable; intelligence layer integration | Feature-gated |
| PriceOracle | XLS-47 | https://xrpl.org/known-amendments.html#priceoracle | On-chain oracle prices ingested by intelligence layer | Feature-gated |

### Feature-Gated / Not on Mainnet

| Amendment | XLS | Status | Architecture Impact |
|-----------|-----|--------|---------------------|
| LendingProtocol | XLS-66 | Draft/voting | Not on mainnet; feature gate required |
| SingleAssetVault | XLS-65 | Draft/voting | Not on mainnet; feature gate required |
| PermissionedDEX | XLS-81 | Draft/voting | Requires Credentials; not on mainnet |
| PermissionedDomains | — | Draft/voting | Not on mainnet |
| TokenEscrow | XLS-85 | Draft/voting | Not on mainnet |

### Obsolete — Do Not Build Against

| Amendment | Reason |
|-----------|--------|
| Batch | Obsolete per xrpl.org/known-amendments.html |
| PermissionDelegation | Obsolete |
| fixBatchInnerSigs | Obsolete |

---

## 2. AMM — XLS-30

**Source**: https://github.com/XRPLF/XRPL-Standards/discussions/78  
**Status**: Implemented (enabled on mainnet)

**Key points**:
- AMM pools use constant-product formula (x * y = k)
- `amm_info` RPC returns pool state
- Trading fee: set in pool creation, typically 0.05%–1.0% (in thousandths, 500 = 0.5%)
- LP tokens have a deterministic currency code
- AMMClawback (XLS-73) allows issuers to claw from AMM pools if enabled

**Architecture impact**: Implemented as feature-gated capability. Simulation uses AMM impact model placeholder. Full AMM constant-product math is Phase 48.

---

## 3. MPT — Multi-Purpose Tokens

**Source**: https://xrpl.org/known-amendments.html#mptokensv1  
**XLS**: MPTokensV1 (no explicit XLS number assigned)  
**Status**: Enabled on mainnet

**Key points**:
- MPTs are a more compact alternative to IOUs for fungible tokens
- MPT issuances have a unique `MPTIssuanceID`
- Holders can be queried via `mpt_holders` RPC
- Transferability is configurable by issuer

**Architecture impact**: Intelligence layer should profile MPT issuances. V2 providers include `get_mpt_holders()` interface.

---

## 4. Price Oracle — XLS-47

**Source**: https://github.com/XRPLF/XRPL-Standards/discussions/119  
**Status**: Enabled on mainnet

**Key points**:
- Oracle objects stored on-chain with up to 10 price pairs
- Multiple providers can publish for the same pair
- `get_aggregate_price` RPC for aggregated oracle prices
- Oracle data has staleness timestamps

**Architecture impact**: Intelligence layer can ingest oracle prices as confidence signal. Phase 47 work.

---

## 5. Clio

**Source**: https://github.com/XRPLF/clio  
**Date checked**: 2026-05-02 (offline)

**Key points**:
- Clio is a read-only historical data server for XRPL
- Optimised for API queries, not for transaction submission
- Exposes same WebSocket API surface as rippled for read operations
- Does NOT support transaction submission

**Architecture impact (critical)**: Architecture Rule #3 — Clio is historical/read provider ONLY. HistoricalProvider interface is for Clio. SubmissionProvider is blocked.

---

## 6. Compromised xrpl.js Versions

**Source**: Community security disclosure; NPM advisory database  
**Date checked**: 2026-05-02

**Compromised versions** (supply-chain attack):
- 4.2.1
- 4.2.2
- 4.2.3
- 4.2.4
- 2.14.2

**Architecture impact**: V2 audit `dependency_check.py` verifies package.json and lockfiles do not contain these versions. This repo has no package.json/lockfile as of Phase 45.

**Safe xrpl.js versions**: 2.14.3+, 4.2.5+

---

## 7. xrpl-py Current State

**Source**: https://github.com/XRPLF/xrpl-py  
**Current version in this repo**: 4.5.0 (as of Phase 45)  
**Minimum safe version**: 2.6.0

**Key points**:
- xrpl-py 4.x supports all mainnet amendments through Phase 45
- No known supply-chain issues as of this research
- Provides WebSocket client, transaction building, signing (not used in V2)

**Architecture impact**: V2 uses xrpl-py for read operations only. No signing or submission via xrpl-py in Phase 45.

---

## 8. Xahau / Hooks

**Source**: https://xahau.network/docs, https://docs.xahau.org  
**Date checked**: 2026-05-02

**Key points**:
- Hooks are smart contract logic attached to XRPL accounts
- Hooks are NOT on XRPL mainnet — Xahau is a separate fork/chain
- Xahau mainnet is live but separate from XRPL mainnet
- Hook language: C/WebAssembly
- Hooks cannot be tested on XRPL testnet/devnet

**Architecture impact**: Xahau/Hooks is RESEARCH_ONLY in Phase 45. A separate Xahau research provider may be added in future phases if explicitly requested. No Hooks logic in V2.

---

## 9. XLS Standards Summary

| XLS | Name | Status | Phase 45 Treatment |
|-----|------|--------|---------------------|
| XLS-30 | AMM | Mainnet | Implemented — capability matrix, sim model placeholder |
| XLS-47 | Price Oracles | Mainnet | Feature-gated — intelligence layer Phase 47 |
| XLS-65 | Single Asset Vault | Draft | Feature-gated |
| XLS-66 | Lending Protocol | Draft | Feature-gated |
| XLS-70 | Credentials | Mainnet | Feature-gated — needed for PermissionedDEX |
| XLS-73 | AMMClawback | Mainnet | Feature-gated — risk layer integration |
| XLS-81 | Permissioned DEX | Draft | Feature-gated |
| XLS-85 | Token Escrow | Draft | Feature-gated |
| XLS-87 | Token Pre-Authorization | Research | Research-only |
| XLS-91 | Beneficiary | Research | Research-only |
| XLS-92 | Sub-Accounts | Research | Research-only |
| XLS-101 | Smart Contracts | Research | Research-only |

---

## 10. Open Research Items

- Passkeys on XRPL: proposal stage, no XLS number assigned
- Nested multisigning: extended ExpandedSignerList functionality
- Smart MPTs: MPT variant with programmable constraints
- Stealth addresses: privacy layer proposal

All above are RESEARCH_ONLY in Phase 45.

---

## Sources Used

1. https://xrpl.org/known-amendments.html
2. https://github.com/XRPLF/XRPL-Standards
3. https://github.com/XRPLF/rippled
4. https://github.com/XRPLF/clio
5. https://github.com/XRPLF/xrpl-py
6. https://xahau.network/docs
7. https://docs.xahau.org
