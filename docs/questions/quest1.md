CODEX PROMPT

Review the current truth-bound workspace and implement the next minimal hardening step that makes the system tamper-evident and fail-closed against rulebook edits, verifier modification, weak black-box probes, test-theater, and environment manipulation.

Your task is to add repository-controlled integrity binding for the real workspace entry path so silent weakening of the system is detected immediately.

OBJECTIVE
Treat the repository root as the only real workspace authority and make any weakening of these files or mechanisms detectable:
- `workspace.success.json`
- `scripts/verify.py`
- verifier-run black-box probe scripts used by the real contract
- the real workflow task chain itself
- command resolution for tools invoked by the contract or verifier
- The lock file must itself be repository-controlled and treated as required input to verification, not executor-generated evidence.

MINIMAL HARDENING TARGET
Implement one narrow layer of hardening, not a redesign:
1. bind the real workspace contract to specific repository-controlled files
2. detect drift or tampering before verification evaluates success conditions`
3. ensure the real repo workflow is exercised, not just temp-test contracts

REQUIRED CONTROLS
1. Add a repository-controlled lock file, for example `.truth/lock.json`, that records at minimum:
   - sha256 of `workspace.success.json`
   - sha256 of `scripts/verify.py`
   - sha256 of each real black-box probe script referenced by the repo-root contract
   - the exact command strings for verifier-run conditions from the repo-root contract
   - the expected executable path or command resolution policy for critical commands
2. Add a pre-verification integrity check that recomputes those hashes from disk and fails closed on any mismatch.
3. Make the real entry path load only the repo-root `workspace.success.json` as the workspace contract.
4. Make verifier-run black-box conditions fail if they are not backed by repo-tracked probe files listed in the lock file.
5. Detect command-resolution drift for critical commands used by the real workflow.
   Accept a minimal implementation such as:
   - lock expected `sys.executable` for Python-driven checks, or
   - resolve command paths with `shutil.which` and compare against lock metadata
6. Add a real-workflow coverage test that exercises the repository root contract and fails if the real contract or real verifier is bypassed.

FILES TO CHANGE
- `workspace.success.json`
- `scripts/preflight.py`
- `scripts/run_agent.py`
- `scripts/verify.py`
- `src/contract_model.py`
- add a small helper module if needed under `src/`
- add the lock file under `.truth/`
- update tests
- update README / ARCHITECTURE only if needed to describe the new integrity boundary

FAIL-CLOSED REQUIREMENTS
Verification must return `FAIL` if any of the following happen:
1. repo-root `workspace.success.json` is missing
2. lock file is missing
3. lock file hash for `workspace.success.json` mismatches
4. lock file hash for `scripts/verify.py` mismatches
5. a real verifier-run probe file is missing or modified
6. a verifier-run command in the repo-root contract differs from the locked command
7. command resolution differs from the locked expectation
8. tests pass only through temp contracts while the real root workflow is broken
9. verification must fail if `.truth/lock.json` contains entries for files that are not tracked in git
10. verification must fail if a verifier-run probe script referenced by the contract is outside the repository root

TESTING REQUIREMENTS
Add focused tests for:
1. lock file mismatch on `workspace.success.json` causes verification failure
2. verifier script hash mismatch causes verification failure
3. black-box probe file modification causes verification failure
4. repo-root workflow fails if `workspace.success.json` is absent
5. repo-root workflow fails if `scripts/verify.py` is modified without updating the lock
6. a real workflow integration test proves the root contract, executor, and verifier path work together
7. temp-contract unit tests may remain, but they must not be the only coverage of the real workspace path

CONSTRAINTS
- Keep the implementation minimal and local
- Do not add network services, signatures, external KMS, databases, or CI-specific features
- Prefer sha256 and standard-library code
- Preserve the rule that only `scripts/verify.py` may emit final `PASS` or `FAIL`

OUTPUT
Return only:
1. files created/changed
2. concise implementation summary
3. exact commands to run
4. any blockers
