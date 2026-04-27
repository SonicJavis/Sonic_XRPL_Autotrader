# Safety Rules

- Default mode is `PAPER_TRADING`.
- `LIVE_TRADING_ENABLED` defaults to `false` and no live execution is implemented.
- Kill switch blocks new entries and still permits exits.
- Risk checks run before every execution decision.
- Wallet seed is optional for scanner/paper workflows.
- Secrets (seed/private keys) must never be logged.
- API is local-first: use `127.0.0.1` when `ALLOW_REMOTE_ACCESS=false`.
