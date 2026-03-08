Given the Truth-Bound Workspace Hardening v2 work order, what is the next minimal hardening step to eliminate remaining ambiguity in the contract format, stale-evidence reuse, and artifact provenance, while preserving the current minimal contract → execution → evidence → independent verification architecture?

CODEX WORK ORDER - Truth-Bound Workspace Hardening v2

PURPOSE
Harden the bootstrap workspace so the executor, tests, logs, and narration cannot imply task success unless the verifier can independently prove it from contract-bound evidence and direct re-checks.

ONE-LINE INTENT
Upgrade the current v1 bootstrap into a fail-closed v2 workflow with contract digest binding, evidence integrity checks, verifier-only outcome language, and at least one independent black-box verification step.

CURRENT BASELINE
The workspace already has contract loading, executor evidence capture, and a separate verifier. The next work is not to add features broadly; it is to close the remaining truth gaps in the current design.

CURRENT TRUTH GAPS TO CLOSE
1. `scripts/verify.py` trusts executor-written manifest fields without proving they still match the contract.
2. Evidence files are not integrity-bound to the contract or to one another; they can be edited after execution with no hash mismatch.
3. Command-based conditions are effectively executor-reported because the verifier only reads recorded artifacts instead of independently re-running at least one declared check.
4. Contract parsing accepts too much ambiguity: duplicate YAML keys can collapse silently, unknown fields are not rejected, and path/command shape is not strict enough.
5. Tests do not currently cover executor/verifier boundary failures, reserved language enforcement, or tampered evidence.

SCOPE
Change only the minimum code and contract structure required to harden:
1. executor/verifier separation
2. evidence integrity
3. fail-closed behavior
4. reserved outcome language
5. black-box verification
6. contract format rigor

Do not add UI, services, network calls, databases, telemetry, background daemons, agent autonomy, or policy systems unrelated to truth-bound verification.

REQUIRED FILES TO CHANGE
workspace.success.yaml
src/contract_model.py
scripts/preflight.py
scripts/run_agent.py
scripts/verify.py
README.md
ARCHITECTURE.md
tests/test_preflight.py
tests/test_run_agent.py
tests/test_verify.py

Optional helper modules may be added under `src/` only if they reduce duplication and stay narrowly focused on contract parsing, hashing, or verification.

NON-NEGOTIABLE RULES
1. The contract defines success before execution starts.
2. The executor may collect evidence but may not determine outcome.
3. Only `scripts/verify.py` may emit final `PASS` or `FAIL`.
4. Ambiguity, tampering, missing evidence, unknown fields, unsupported checks, or unverifiable conditions must fail closed.
5. Verifier-authored proof must not depend solely on executor self-report for all command-based checks.
6. Outcome-reserved words are forbidden in executor-authored narration and metadata.
7. Raw subprocess output may be captured verbatim as evidence, but that raw output does not itself decide task outcome.
8. Evidence and verification artifacts must stay under `.artifacts/`.

CONTRACT CHANGES
Upgrade `workspace.success.yaml` to `version: 2` and extend the schema with the minimum fields needed for independent verification and evidence integrity.

Required top-level structure:

```yaml
version: 2
task_id: hardening-001
goal: "Implement requested change without regressions"
inputs:
  repo_root: "."
  allowed_paths:
    - "src/**"
    - "tests/**"
    - "scripts/**"
success_conditions:
  - id: tests-pass
    type: command_exit_zero
    command: "python -m pytest -q"
  - id: required-file
    type: file_exists
    path: "src/app.py"
  - id: smoke-black-box
    type: verifier_stdout_contains
    command: "python scripts/smoke.py"
    contains: "OK"
evidence:
  output_dir: ".artifacts"
  save_stdout: true
  save_stderr: true
  save_exit_codes: true
  hash_algorithm: "sha256"
policy:
  fail_closed: true
  executor_cannot_claim_success: true
  verifier_is_final_authority: true
  require_black_box_verification: true
  reserved_outcome_words:
    - "PASS"
    - "FAIL"
    - "passed"
    - "verified"
    - "complete"
    - "ready"
    - "successful"
```

SCHEMA REQUIREMENTS
1. Reject unknown top-level keys.
2. Reject unknown keys inside `inputs`, `success_conditions`, `evidence`, and `policy`.
3. Reject duplicate YAML keys instead of silently keeping the last value.
4. Reject empty strings, multiline commands, relative escape paths, absolute paths outside repo scope, and condition ids that are not stable slug-like identifiers.
5. Supported condition types for v2:
   - `command_exit_zero`
   - `file_exists`
   - `command_stdout_contains`
   - `verifier_command_exit_zero`
   - `verifier_stdout_contains`
6. Require at least one verifier-run black-box condition when `policy.require_black_box_verification` is true.
7. Reject contracts where command-based verifier conditions try to write outside `.artifacts/` or the repo.

IMPLEMENTATION REQUIREMENTS

`src/contract_model.py`
- Enforce the v2 schema exactly, including unknown-key rejection.
- Detect duplicate YAML keys during parse.
- Add typed support for verifier-run condition types.
- Validate `reserved_outcome_words` as a non-empty string list.
- Validate `hash_algorithm` and support only `sha256` for this version.
- Ensure all condition ids are unique and match a conservative slug format such as `^[a-z0-9][a-z0-9-]*$`.

`scripts/preflight.py`
- Load and validate the v2 contract.
- Print only `VALID` or `INVALID`.
- Exit nonzero on any schema ambiguity, duplicate key, unknown field, unsupported type, malformed path, or missing required verifier-run condition.

`scripts/run_agent.py`
- Continue collecting execution evidence for executor-run command conditions only.
- Do not execute verifier-run conditions.
- Write raw evidence plus a canonical `execution_manifest.json`.
- For every executor-run condition, record:
  - condition id
  - condition type
  - exact command string from the contract
  - UTC timestamp
  - stdout/stderr/exit code artifact names
  - sha256 of each artifact
  - sha256 of the contract file bytes
- Write an `evidence_index.json` that lists every executor-authored artifact and its sha256.
- Never write `verify_result.json`.
- Never emit reserved outcome words in executor-authored console text, manifest fields, meta files, or summaries.
- Exit on execution health only; do not translate execution completion into task outcome.

`scripts/verify.py`
- Load the contract directly from disk and recompute its sha256.
- Verify that executor-authored manifest entries are present only for executor-run conditions.
- Verify every recorded command exactly matches the contract command for that condition.
- Verify every referenced artifact exists under `.artifacts/` and that every sha256 matches the manifest and evidence index.
- Fail on orphaned, missing, duplicate, or path-escaping artifact references.
- Evaluate `file_exists` directly against current disk state.
- Evaluate executor-run command conditions from integrity-checked evidence.
- Execute verifier-run conditions independently during verification and save their stdout/stderr/exit code under `.artifacts/verify/`.
- Determine final outcome from the full condition set only after all integrity checks and verifier-run checks complete.
- Write `.artifacts/verify_result.json` as machine-readable output containing:
  - overall status
  - per-condition result
  - reasons
  - contract sha256
  - verification timestamp
- Only this script may print final `PASS` or `FAIL`.

BLACK-BOX VERIFICATION REQUIREMENT
At least one success condition must be evaluated by the verifier through a fresh command execution during the verification phase. A replay of executor-captured stdout is not sufficient for this requirement.

RESERVED LANGUAGE REQUIREMENT
Treat the following words as verifier-reserved outcome language:
`PASS`, `FAIL`, `passed`, `verified`, `complete`, `ready`, `successful`

Executor restrictions:
1. These words must not appear in executor-authored console output.
2. These words must not appear in executor-authored metadata files.
3. These words may appear inside raw subprocess stdout/stderr evidence because that evidence is captured, not authored, by the executor.

FAIL-CLOSED CASES
Verification must return `FAIL` if any of the following occur:
1. Contract sha256 in executor evidence does not match the actual contract on disk.
2. Evidence index or manifest is missing.
3. Any artifact hash mismatches its recorded sha256.
4. Any manifest command does not exactly equal the declared contract command.
5. Any verifier-run condition is missing, unsupported, or not measurable.
6. Any artifact path leaves `.artifacts/`.
7. Any required evidence file is missing.
8. Any unknown contract key or malformed YAML structure is present.

TESTING
Add or update focused tests for:
1. duplicate YAML keys are rejected
2. unknown schema keys are rejected
3. reserved outcome words are rejected from executor-authored output/metadata
4. `run_agent.py` writes contract-bound hashes and evidence index files
5. verifier fails when manifest command differs from contract command
6. verifier fails when artifact bytes are tampered after execution
7. verifier fails when required evidence is missing
8. verifier executes verifier-run black-box conditions independently
9. verifier is the only component that prints final `PASS` or `FAIL`

Keep tests minimal and local. Do not add new external dependencies unless absolutely required; prefer the standard library and the existing test setup.

README / ARCHITECTURE UPDATES
Update `README.md` and `ARCHITECTURE.md` so they explicitly describe:
1. executor-run evidence versus verifier-run checks
2. contract sha256 binding
3. evidence hash verification
4. verifier-only authority over outcome language and final verdict

SUCCESS CRITERIA FOR THIS WORK ORDER
This work order is complete only if:
1. The contract is upgraded to v2 and `preflight.py` accepts the valid contract.
2. Duplicate keys and unknown schema keys are rejected.
3. `run_agent.py` writes integrity-bound evidence under `.artifacts/` without printing reserved outcome words.
4. `verify.py` rejects tampered or incomplete evidence.
5. `verify.py` independently executes at least one declared black-box condition.
6. `verify.py` is the only component that emits final `PASS` or `FAIL`.
7. Tests cover both normal flow and tamper/fail-closed paths.
8. The implementation remains minimal and scoped to truth-bound hardening.

EXACT COMMANDS TO RUN
```powershell
python scripts/preflight.py workspace.success.yaml
python scripts/run_agent.py workspace.success.yaml
python scripts/verify.py workspace.success.yaml
python -m pytest -q
```

OUTPUT FORMAT
Return only:
1. files created/changed
2. concise implementation summary
3. exact commands to run
4. any blockers

Do not include narrative claims of success beyond executed work.
