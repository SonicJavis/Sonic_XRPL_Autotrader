# XRPL Notes

This phase uses XRPL read-only primitives:

- JSON-RPC wrappers for account/lines/book/server state queries.
- WebSocket ledger stream subscription placeholder.
- Transaction builders are placeholders for future phases.

`submit_transaction` intentionally raises `NotImplementedError` in this phase.
No live submission path is provided.
