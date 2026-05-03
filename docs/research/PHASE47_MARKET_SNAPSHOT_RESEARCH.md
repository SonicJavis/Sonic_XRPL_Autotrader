# Phase 47 Market Snapshot Engine — Research Baseline

**Last updated**: 2026-05-03  
**Phase**: 47 — V2 Capability-Aware Market Snapshot Engine  
**Methodology**: Offline review of primary sources. No live network queries.

---

## Important Disclaimer

This document records the research baseline for Phase 47 implementation.
All architecture decisions are offline-only, fixture-backed, and non-executing.
No wallet seeds, private keys, signing, or live submission are referenced.

---

## 1. XRPL RPC Methods Used by Market Snapshot Engine

### 1.1 account_info

**Source**: https://xrpl.org/account_info.html  
**Date checked**: 2026-05-03  
**Key points**:
- Returns AccountRoot ledger object for an account.
- `Balance` field is XRP in drops (string).
- `Flags` field encodes account-level flags (e.g., lsfDefaultRipple, lsfRequireDestTag).
- `OwnerCount` is the number of objects owned by the account.
- `PreviousTxnID` is the hash of the most recent transaction modifying this account.
- Response includes `validated: true` if the data is from a validated ledger.
- Must use `ledger_index: "validated"` to get confirmed data.

**Architecture impact**: AccountContext module reads account_info fixtures. Flags must be parsed per protocol spec. Balance is in drops — convert to XRP for display only.  
**Status**: Implemented now (offline fixture reads only)

---

### 1.2 account_lines

**Source**: https://xrpl.org/account_lines.html  
**Date checked**: 2026-05-03  
**Key points**:
- Returns trust lines for an account.
- Each line has: `account` (counterparty/issuer), `currency`, `balance`, `limit`, `limit_peer`.
- `no_ripple` flag affects XRP/IOU routing.
- `freeze` flag means account has frozen the line.
- `authorized` flag indicates trustline authorization.
- Response paginates with `marker` for large sets.
- `balance` is positive if account holds that currency, negative if issuer owes account.

**Architecture impact**: TrustlineContext reads account_lines fixtures. NoRipple and freeze flags must be surfaced in snapshot. Clawback relevance must be checked against issuer account flags.  
**Status**: Implemented now (offline fixture reads only)

---

### 1.3 book_offers

**Source**: https://xrpl.org/book_offers.html  
**Date checked**: 2026-05-03  
**Key points**:
- Returns best offers from an orderbook for a given asset pair.
- `taker_gets` and `taker_pays` define the asset pair.
- Offers are sorted by quality (best first).
- Each offer has: `Account`, `TakerGets`, `TakerPays`, `quality`.
- `quality` = TakerPays / TakerGets (price per unit of TakerGets).
- Offer amounts may be partially consumed.
- `limit` parameter (default 300) controls how many offers to return.

**Architecture impact**: OrderbookSnapshot reads book_offers fixture data. Bid/ask extraction and spread_bps calculation are computed from offer quality values.  
**Status**: Implemented now (offline fixture reads only)

---

### 1.4 amm_info

**Source**: https://xrpl.org/amm_info.html  
**Date checked**: 2026-05-03  
**Key points**:
- Returns AMM pool state for a given asset pair.
- Requires AMM amendment to be enabled.
- Returns: `amount` (Asset A reserves), `amount2` (Asset B reserves), `trading_fee`, `lp_token`, `amm_account`.
- `trading_fee` is in units of 1/100,000 (e.g., 500 = 0.5%).
- `lp_token` is the LP token issued to liquidity providers.
- AMMClawback amendment allows clawback of assets held in AMM by issuer.

**Architecture impact**: AMMSnapshot reads amm_info fixture data. Capability check for AMM amendment is required before processing. AMMClawback flag must be surfaced if issuer has clawback enabled.  
**Status**: Implemented now (offline fixture reads only)

---

### 1.5 Transaction Metadata and AffectedNodes

**Source**: https://xrpl.org/transaction-metadata.html  
**Date checked**: 2026-05-03  
**Key points**:
- Metadata is available only in validated ledger transactions.
- `TransactionResult` must be `tesSUCCESS` for the transaction to have applied.
- `tesSUCCESS` without `AffectedNodes` is NOT sufficient truth for PnL attribution.
- `AffectedNodes` contains `CreatedNode`, `ModifiedNode`, `DeletedNode` entries.
- `delivered_amount` in metadata is the authoritative amount delivered; use over `Amount` for Payments.
- For partial payments: always use `delivered_amount`, never `Amount`.
- `AffectedNodes` contain `LedgerEntryType` identifying the modified object type.

**Architecture impact**: MetadataSignal reads from metadata_parser. Insufficient truth flags are required. delivered_amount must be surfaced for Payment type transactions.  
**Status**: Implemented now (offline fixture reads only)

---

### 1.6 MPT (Multi-Purpose Tokens)

**Source**: https://xrpl.org/known-amendments.html#mptokensv1  
**Date checked**: 2026-05-03  
**Key points**:
- MPTokensV1 amendment is ENABLED on mainnet.
- MPT issuances are identified by a 64-character MPTokenIssuanceID.
- Holders can be queried via ledger_entry for MPTokenIssuance objects.
- MPTs support custom metadata, transfer fees, and holder restrictions.
- MPTs are separate from IOU trust lines — different data structures.

**Architecture impact**: MPTSnapshot reads MPT holder fixture data. Capability check for MPTokensV1 is required. Holder count and sample are surfaced in snapshot.  
**Status**: Implemented now (offline fixture reads only)

---

## 2. XRPL Amendment Status — Phase 47 Verification

**Source**: https://xrpl.org/known-amendments.html  
**Date checked**: 2026-05-03

The following amendments are confirmed ENABLED on XRPL mainnet as of this research baseline:

| Amendment | XLS | Architecture Impact for Phase 47 |
|-----------|-----|----------------------------------|
| AMM | XLS-30 | AMM pool snapshots enabled; capability check required |
| AMMClawback | XLS-73 | Clawback risk must be surfaced in AMM snapshot |
| Clawback | — | Token clawback risk surfaced in trustline/asset context |
| Credentials | XLS-70 | On-chain credentials; research-only for market snapshot |
| DID | — | Research-only for market snapshot |
| DeepFreeze | — | Freeze state surfaced in trustline context |
| MPTokensV1 | — | MPT holder snapshots enabled; capability check required |
| PriceOracle | XLS-47 | Oracle prices research-only in this phase |

Feature-gated (NOT on mainnet — snapshot must NOT assume these):

| Amendment | Reason |
|-----------|--------|
| LendingProtocol (XLS-66) | Not yet mainnet |
| SingleAssetVault (XLS-65) | Not yet mainnet |
| PermissionedDEX (XLS-81) | Not yet mainnet |
| PermissionedDomains | Not yet mainnet |
| TokenEscrow (XLS-85) | Not yet mainnet |

Obsolete (MUST NOT build against):

| Amendment | Reason |
|-----------|--------|
| Batch | Obsolete per xrpl.org/known-amendments.html |
| fixBatchInnerSigs | Obsolete per xrpl.org/known-amendments.html |
| PermissionDelegation | Obsolete per xrpl.org/known-amendments.html |

Research-only (XRPL mainnet does NOT have these):

| Amendment | Reason |
|-----------|--------|
| HooksOnMainnet | Hooks are Xahau-only, NOT on XRPL mainnet |
| XahauHooks | Separate chain |
| SmartContractsXLS101 | Proposal only |

---

## 3. xrpl-py Security Status

**Source**: https://github.com/XRPLF/xrpl-py/releases  
**Date checked**: 2026-05-03

- No known security advisories for xrpl-py at time of Phase 47 research.
- Project uses xrpl-py for offline data model classes only (no live signing/submission in Phase 47).
- xrpl.js versions 4.2.1, 4.2.2, 4.2.3, 4.2.4, 2.14.2 were compromised (supply chain attack).
- Safe xrpl.js versions: ≥ 4.2.5 or ≥ 2.14.3.
- This project does not use xrpl.js — no JS dependency risk.

---

## 4. XRPL Standards Referenced

| XLS | Title | Status | Phase 47 Impact |
|-----|-------|--------|-----------------|
| XLS-30 | AMM | Enabled | AMM snapshot capability |
| XLS-47 | Price Oracle | Enabled | Research-only in this phase |
| XLS-65 | Single Asset Vault | Draft | Not implemented; feature-gated |
| XLS-66 | Lending | Draft | Not implemented; feature-gated |
| XLS-70 | Credentials | Enabled | Research-only for snapshot |
| XLS-73 | AMMClawback | Enabled | Clawback risk flag in AMM snapshot |
| XLS-81 | Permissioned DEX | Draft | Not implemented; feature-gated |
| XLS-85 | Token Escrow | Draft | Not implemented; feature-gated |

---

## 5. Clio-Specific Notes

**Source**: https://github.com/XRPLF/clio  
**Date checked**: 2026-05-03

- Clio supports `tx_type` filter on `account_tx` requests (Clio-only behavior).
- Phase 47 does not depend on Clio-specific behavior; fixture data is pre-fetched.
- For historical reads, Clio is preferred over rippled when available.

---

## 6. Hooks / Xahau Architecture Decision

**Source**: https://xahau.network/docs, https://xrpl.org/known-amendments.html  
**Date checked**: 2026-05-03

- Hooks are NOT available on XRPL mainnet. They exist only on Xahau.
- Xahau is a separate chain from XRPL mainnet with a different ledger history.
- Phase 47 architecture does NOT include Hooks or Xahau logic.
- Xahau snapshot context must NOT improve XRPL mainnet confidence scores.
- Any future Hooks support requires a separate feature gate and provider abstraction.

---

## 7. Market Snapshot Architecture Decisions

### 7.1 Deterministic Snapshot IDs

Snapshot IDs are computed as SHA-256 of the canonical sorted JSON of the snapshot manifest plus timestamp. This ensures reproducibility and auditability.

**Status**: Implemented now

### 7.2 Capability-Awareness

Every snapshot section checks the relevant protocol capability before building:
- AMM section: requires `AMM` amendment to be ENABLED
- MPT section: requires `MPTokensV1` amendment to be ENABLED
- Trustline clawback: requires `Clawback` amendment context
- DeepFreeze: requires `DeepFreeze` amendment context

If a capability is not ENABLED, the section is marked with a limitation instead of being omitted or failing.

**Status**: Implemented now

### 7.3 Quality Scoring

The quality score (0–100) reflects how much useful data is available in the snapshot for downstream simulation or research use. Key deductions:
- Missing metadata: −20 per missing metadata file
- tesSUCCESS with no AffectedNodes: −15
- Missing AMM data when AMM is requested: −10
- Missing orderbook data: −10
- MPT requested but data unavailable: −5
- Capability mismatch warnings: −5 each

Score thresholds:
- ≥ 80: `usable_for_simulation`
- ≥ 50: `usable_for_research`
- ≥ 20: `insufficient_data`
- < 20: `rejected`

**Status**: Implemented now

### 7.4 Same-Ticker / Different-Issuer Rule

The snapshot engine must NEVER collapse two IOU assets with the same currency code but different issuers into a single asset. Each `(currency, issuer)` pair is a distinct asset.

**Status**: Implemented now (enforced in AssetSnapshot construction)

### 7.5 No Live Calls

The snapshot engine is entirely offline. No network calls, no signing, no submission, no auto-calibration, no daemon loops.

**Status**: Enforced — no live providers in this module

---

## 8. Safety Model Compliance

The following safety rules are confirmed for Phase 47:

- No wallet seed or private key handling
- No signing logic
- No Xaman payload creation
- No transaction submission
- No autofill
- No submitAndWait
- No live buy/sell or order placement
- No live trading or testnet trading
- No auto-calibration or model mutation
- No background daemon loops
- No live network calls

All market snapshot operations are offline fixture reads only.
