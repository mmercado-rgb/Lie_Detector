CODEX PATCH — Admission Gate Integrity v1
PURPOSE
Close the execution-gate bypass so an invalid contract cannot produce fresh executor artifacts.
ONE-LINE INTENT
Make scripts/run_agent.py hard-refuse invalid contracts before any execution or artifact creation.
OBSERVED DEFECT
python scripts/preflight.py workspace.success.yaml prints INVALID and exits nonzero
python scripts/run_agent.py workspace.success.yaml still executes declared executor-run conditions, writes fresh artifacts under .artifacts, and exits 0
REQUIRED CHANGE
1. scripts/run_agent.py must load and validate the contract before doing any execution work
2. if contract validation fails, run_agent.py must exit nonzero
3. if contract validation fails, run_agent.py must not execute any condition
4. if contract validation fails, run_agent.py must not write any fresh executor-authored artifact under .artifacts
5. keep existing architecture unchanged
6. keep scope minimal
PREFERRED IMPLEMENTATION
Reuse the same contract validation path already used by preflight.py rather than duplicating logic
If needed, extract shared validation into a narrow helper under src/ so both preflight.py and run_agent.py call the same validation entrypoint
Do not add new dependencies
FILES IN SCOPE
scripts/run_agent.py
scripts/preflight.py
src/contract_model.py
tests/test_run_agent.py
tests/test_preflight.py
MINIMAL TEST TO ADD
Add one focused test proving:
- invalid contract causes run_agent.py to exit nonzero
- invalid contract causes no fresh executor artifacts to be created in .artifacts except an optional preexisting static placeholder such as .gitkeep
LIVE FAILURE TO MATCH
Observed live behavior:
- preflight exit code = 1
- run_agent exit code = 0
- fresh artifacts were written:
  .artifacts/evidence_index.json
  .artifacts/execution_manifest.json
  .artifacts/lint-pass.exitcode.txt
  .artifacts/lint-pass.meta.json
  .artifacts/lint-pass.stderr.txt
  .artifacts/lint-pass.stdout.txt
  .artifacts/tests-pass.exitcode.txt
  .artifacts/tests-pass.meta.json
  .artifacts/tests-pass.stderr.txt
  .artifacts/tests-pass.stdout.txt
ACCEPTANCE CRITERIA
1. python scripts/preflight.py workspace.success.yaml on an invalid contract prints INVALID and exits nonzero
2. python scripts/run_agent.py workspace.success.yaml on the same invalid contract exits nonzero
3. run_agent.py on an invalid contract creates no fresh executor-authored artifacts
4. valid-contract behavior remains unchanged
EXACT COMMANDS TO RUN
rm -rf .artifacts/*
python scripts/preflight.py workspace.success.yaml; echo $?
python scripts/run_agent.py workspace.success.yaml; echo $?
find .artifacts -maxdepth 2 -type f | sort
python -m pytest -q
OUTPUT FORMAT
Return only:
1. files changed
2. concise implementation summary
3. exact commands to run
4. blockers
Do not include narrative claims of success beyond executed work.