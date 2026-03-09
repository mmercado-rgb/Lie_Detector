# Truth-Bound Workspace Bootstrap

Flow:

Contract admission -> Execution -> Evidence -> Independent verification -> Verdict

Current contract and schema:

- Contract file: `workspace.success.json`
- Authoritative schema: `schemas/workspace_success.schema.json`
- Contract loading path: `src.integrity.load_contract_with_integrity_gate(...)`

Command boundaries:

- `scripts/preflight.py` is a thin admission entrypoint and prints only `VALID` or `INVALID`.
- `scripts/run_agent.py` executes only executor-run conditions and writes evidence under `.artifacts/`.
- `scripts/verify.py` independently validates integrity and conditions.
- Only `scripts/verify.py` may emit final `PASS` or `FAIL`.

Required proof behavior:

- Invalid contracts block execution.
- Clean run passes verification.
- Tampered artifacts fail verification.
- Replayed artifacts fail verification.
- Failing declared execution conditions fail verification.

Commands:

```powershell
python scripts/preflight.py workspace.success.json
python scripts/run_agent.py workspace.success.json
python scripts/verify.py workspace.success.json
python -m pytest -q
```

## WARNING: Optional integrity lock mechanism

The `.truth/lock.json` feature can bind verifier/runtime behavior to specific file hashes and command resolutions.  
This mechanism is **not required** for the core truth-bound verification architecture.  
It is provided as an advanced integrity control and may restrict or pin runtime components.  
Use only if you understand the implications.
