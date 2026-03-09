# Archived Work Order: Schema-Based Admission

Status: Implemented and retained in current architecture.

Current truth:

- Contract file remains `workspace.success.json`.
- Contract admission is schema-based via `schemas/workspace_success.schema.json`.
- Admission is executed in `src.integrity.load_contract_with_integrity_gate(...)`.
- `scripts/preflight.py` remains a thin wrapper that prints only `VALID` or `INVALID`.
- Contract -> execution -> evidence -> independent verification flow is preserved.

This file is retained as historical context and intentionally trimmed to avoid stale migration wording.
