# Archived Work Order: Schema Admission Gate

Status: Implemented and retained in current architecture.

Current truth:

- Contracts are loaded through `src.integrity.load_contract_with_integrity_gate(contract_path)`.
- The contract is `workspace.success.json`.
- Schema validation uses `schemas/workspace_success.schema.json` before runtime use.
- `scripts/preflight.py`, `scripts/run_agent.py`, and `scripts/verify.py` all rely on the shared admission gate.
- Invalid contracts fail closed and block execution.

This file is retained as historical context and intentionally trimmed to avoid stale implementation wording.
