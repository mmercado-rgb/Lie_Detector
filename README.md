# Truth-Bound Workspace Bootstrap

This workspace uses a contract-first flow:

Contract -> Execution -> Evidence -> Independent Verification -> Final Verdict

`workspace.success.yaml` is the only declared source of measurable success. The contract is loaded before execution and bound to evidence with a `sha256` digest.

`scripts/run_agent.py` executes only executor-run command conditions. It writes raw stdout, stderr, exit codes, metadata, `execution_manifest.json`, and `evidence_index.json` under `.artifacts/`. It does not decide task outcome and it does not run verifier-only checks.

`scripts/verify.py` loads the contract from disk, recomputes the contract digest, verifies artifact hashes, rejects tampered or missing evidence, re-checks file conditions from disk state, and executes verifier-run black-box checks under `.artifacts/verify/`.

Only `scripts/verify.py` may emit the final `PASS` or `FAIL`.

## Commands

```powershell
python scripts/preflight.py workspace.success.yaml
python scripts/run_agent.py workspace.success.yaml
python scripts/verify.py workspace.success.yaml
python -m pytest -q
```
