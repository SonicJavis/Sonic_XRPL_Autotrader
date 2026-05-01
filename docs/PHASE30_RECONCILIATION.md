# Phase 30: Simulation vs Reality Reconciliation

## Core Purpose
Phase 30 serves as the truth measurement layer for the XRPL Autotrader. It introduces an analytical suite to perform a read-only comparison between our hosted application's simulation estimates and the actual real-world outcomes logged by the execution prototype. 

This is a **purely analytical** module. There is no auto-calibration, no background submission or execution logic change, and no mutation of historical data.

## The XRPL Truth Model (Mandatory Rules)
The reconciliation strictly adheres to the reality of the XRP Ledger:
1. **Submitted ≠ Validated**: A transaction being submitted successfully (`tesSUCCESS`) merely means the transaction was applied to the current working ledger successfully. It does *not* mean the expected outcome was achieved (e.g., a pathfinding payment might still fail due to liquidity constraints in the next validated ledger, or an offer might be partially filled).
2. **Metadata is Reality**: The actual state of an outcome (delivered amount, final fee paid, fill quality) can only be truly ascertained by analyzing the transaction metadata (`meta`) after it has been included in a validated ledger. 
3. **Payments**: The actual delivered amount must be derived from `meta.delivered_amount`. The base `Amount` field cannot be trusted to reflect the actual delivery for path-dependent payments.
4. **Missing Metadata**: If metadata is missing for a transaction (e.g. only the manual `tesSUCCESS` status was recorded by the user), the system *must not* infer fill quality or attempt to guess the outcome. It simply marks the record as `LIMITED` or `INSUFFICIENT_REALITY_DATA`.

## Why No Auto-Calibration?
This system is an advisory intelligence platform, not an automated trading bot. Allowing the system to auto-calibrate based on reality drift creates dangerous feedback loops where the execution engine might silently start relaxing safety boundaries or adjusting slippage assumptions without explicit user approval. Thus, all reconciliation output is strictly for human review.

## Limitations of Current Lifecycle Tracking
Since the execution prototype currently relies on manual updates from the user (e.g., manual insertion of the transaction hash and `tesSUCCESS` status), there may be significant gaps in reality data. In many cases, we may only have the manual status and lack the deep on-chain metadata needed to analyze partial fills or precise slippage. The reconciliation engine is designed to handle this gracefully by throwing `MISSING_METADATA` and `INSUFFICIENT_REALITY_DATA` flags rather than failing or guessing.

## How to Safely Interpret Reports
- **Status Match Rate**: Indicates how often the simulation's expected status matched the actual outcome's status. Keep in mind that `tesSUCCESS` does not equal "expected fill achieved".
- **Drift Flags**: These highlight specific areas where reality deviated from expectation (e.g. `FEE_MISMATCH`, `LIQUIDITY_OVERESTIMATION`, `TX_NOT_VALIDATED`).
- **Append-only Structure**: Reconciliation reports are output to timestamped folders. They represent a point-in-time analysis and should not be used to drive automated downstream decisions.
