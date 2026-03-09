# Authority Boundaries

Workflow:

Contract admission -> Execution -> Evidence -> Independent verification -> Verdict

Components:

- Contract: strict JSON contract at `workspace.success.json`, validated against `schemas/workspace_success.schema.json` through `src.integrity.load_contract_with_integrity_gate(...)`.
- Preflight: `scripts/preflight.py` is an admission check only; output is `VALID` or `INVALID`.
- Executor: `scripts/run_agent.py` runs executor-bound checks and writes evidence artifacts.
- Verifier: `scripts/verify.py` revalidates contract binding, evidence integrity, freshness, and verifier-run conditions.

Enforcement:

- Invalid contracts fail closed and block execution.
- Evidence is contract-bound and integrity-checked.
- Replayed stale artifacts are rejected.
- Declared failing execution conditions produce verifier `FAIL`.
- Only `scripts/verify.py` may print final `PASS` or `FAIL`.

## WARNING: Optional integrity lock mechanism

The `.truth/lock.json` feature can bind verifier/runtime behavior to specific file hashes and command resolutions.  
This mechanism is **not required** for the core truth-bound verification architecture.  
It is provided as an advanced integrity control and may restrict or pin runtime components.  
Use only if you understand the implications.
