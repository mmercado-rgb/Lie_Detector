CODEX PATCH — Remove Misleading Lock Dependency
PURPOSE
Remove the .truth/lock.json admission dependency introduced by the previous patch and keep the execution gate fix without adding a file-lock concept.
ONE-LINE INTENT
run_agent.py must reject invalid contracts by reusing the same strict contract validation path as preflight.py, without requiring .truth/lock.json to exist.
REASON
I do not want a lock-file concept added to the workspace. lock.json is misleading and introduces an extra dependency not required by the original minimal architecture.
REQUIRED CHANGE
1. remove the requirement that .truth/lock.json exist for preflight.py or run_agent.py to accept a valid contract
2. keep the admission-gate fix: invalid contracts must still block execution
3. make scripts/run_agent.py use the same strict contract validation path as scripts/preflight.py
4. do not introduce any file-lock or lock-manifest requirement
5. keep scope minimal
FILES IN SCOPE
scripts/preflight.py
scripts/run_agent.py
src/integrity.py
src/contract_model.py
tests/test_preflight.py
tests/test_run_agent.py
ACCEPTANCE CRITERIA
1. a schema-valid workspace.success.yaml can pass preflight without requiring .truth/lock.json
2. invalid contracts still cause preflight to print INVALID and exit nonzero
3. invalid contracts still cause run_agent.py to exit nonzero
4. invalid contracts still cause run_agent.py to create no fresh executor artifacts
5. no lock-file dependency remains
EXACT COMMANDS TO RUN
rm -rf .artifacts/*
python scripts/preflight.py workspace.success.yaml; echo $?
python scripts/run_agent.py workspace.success.yaml; echo $?
find .artifacts -maxdepth 2 -type f | sort
OUTPUT FORMAT
Return only:
1. files changed
2. concise implementation summary
3. exact commands to run
4. blockers