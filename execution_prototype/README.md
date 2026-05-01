# Air-Gapped XRPL Execution Prototype

This directory is separate from the hosted intelligence platform.

Rules:

- JSON files are the only exchange format.
- The hosted system is not imported.
- The hosted database is not opened.
- Unsigned XRPL transaction JSON is generated deterministically.
- Xaman is used for external user approval.
- The CLI never runs in the background and has no batch mode.
- Submission requires the exact manual phrase `CONFIRM_EXECUTION`.
- Submission also requires explicit acknowledgement of trade type, partial-fill, and price-impact risk.
- Safety gates cannot be overridden.

Example:

```powershell
.venv\Scripts\python.exe -m execution_prototype.cli validate-intent intent.json
.venv\Scripts\python.exe -m execution_prototype.cli wizard-preview intent.json --out wizard_preview.json
.venv\Scripts\python.exe -m execution_prototype.cli build-tx intent.json --out unsigned_tx.json
.venv\Scripts\python.exe -m execution_prototype.cli generate-xaman intent.json --out xaman_payload.json
.venv\Scripts\python.exe -m execution_prototype.cli submit intent.json --confirmation CONFIRM_EXECUTION --understand-type --accept-partial-fill --understand-price-impact
```

Lifecycle tracking:

```powershell
.venv\Scripts\python.exe -m execution_prototype.cli create-session intent.json --confirmation CONFIRM_EXECUTION
.venv\Scripts\python.exe -m execution_prototype.cli show-session <session_id> --confirmation CONFIRM_EXECUTION
.venv\Scripts\python.exe -m execution_prototype.cli mark-signed <session_id> --confirmation CONFIRM_EXECUTION
.venv\Scripts\python.exe -m execution_prototype.cli record-submission <session_id> <tx_hash> --confirmation CONFIRM_EXECUTION
.venv\Scripts\python.exe -m execution_prototype.cli record-result <session_id> tesSUCCESS --confirmation CONFIRM_EXECUTION
.venv\Scripts\python.exe -m execution_prototype.cli mark-validated <session_id> --ledger-index 12345 --confirmation CONFIRM_EXECUTION
```

Warnings:

- XRPL liquidity may change between ledgers.
- Partial fills are normal.
- Path-based payments can fail during ledger validation.
- AMM price impact can shift per ledger.
- The wizard preview is an education and review surface only.
- Payload session tracking records user-provided lifecycle state only.
- Submission is not confirmation; validated ledger inclusion is recorded manually.
- This prototype does not make outcomes certain.
