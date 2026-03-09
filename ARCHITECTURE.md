# Authority Boundaries

## Workflow

Contract -> Execution -> Evidence -> Independent Verification -> Final Verdict

## Components

Contract defines success and reserved outcome language.

Executor runs only executor-bound commands and records evidence.

Filesystem stores the contract-bound evidence set under `.artifacts/`.

Verifier validates hashes, re-checks declared conditions, runs verifier-only black-box commands, and determines outcome.

## Enforcement

- `workspace.success.json` is a strict v2 contract. Unknown keys, duplicate JSON keys, malformed paths, invalid ids, and missing verifier-run checks are rejected by `src/contract_model.py`.
- `scripts/preflight.py` prints only `VALID` or `INVALID`.
- `scripts/run_agent.py` writes executor evidence plus `execution_manifest.json` and `evidence_index.json`, each bound to the contract `sha256`, and records a per-run `run_id` in `.truth/latest_run_id.txt`.
- `scripts/run_agent.py` does not print reserved outcome words and does not emit the final verdict.
- `scripts/verify.py` recomputes the contract hash, verifies artifact integrity, requires artifact `run_id` to match `.truth/latest_run_id.txt`, rejects orphaned or tampered evidence, and writes `.artifacts/verify_result.json`.
- `scripts/verify.py` executes verifier-run black-box checks under `.artifacts/verify/`.
- Only `scripts/verify.py` may print `PASS` or `FAIL`.
