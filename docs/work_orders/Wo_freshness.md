CODEX WORK ORDER — Freshness Binding Hardening v1
PURPOSE
Close the proven replay gap in the truth-bound workspace by preventing a previously valid .artifacts bundle from passing verification under the same contract bytes in a later run.
ONE-LINE INTENT
Add minimal run-instance freshness binding so verify.py rejects cross-run replay of stale evidence even when artifact hashes, manifest, and contract hash are internally consistent.
PROVEN GAP
Live replay experiment showed:
1. Run A under a contract produced .artifacts and verify.py returned PASS
2. Run B changed runtime state under the same contract and verify.py returned FAIL
3. Replacing current .artifacts with saved Run A artifacts caused verify.py to return PASS again
Conclusion:
Current architecture detects tampering but does not detect cross-run replay under the same contract.
SCOPE
Change only the minimum code and contract structure required to bind executor evidence to a unique run instance.
Do not add UI, services, network calls, databases, telemetry, background daemons, external signers, KMS, TSA, or policy systems.
GOAL
After this change, replaying a previously valid .artifacts bundle from an earlier run under the same contract must cause verify.py to return FAIL.
MINIMAL DESIGN REQUIREMENT
Introduce a per-run unique run identifier generated at execution time and bound into executor evidence and verification.
The verifier must reject evidence if the run binding is missing, inconsistent, or replayed.
ALLOWED IMPLEMENTATION SHAPE
Use one minimal run-instance binding mechanism, such as:
- executor-generated run_id plus verifier-checked freshness marker stored in evidence
or
- canonical run manifest digest that includes a unique run_id and is checked by verifier
Pick the smallest deterministic design that makes replayed stale bundles fail.
NON-NEGOTIABLE RULES
1. Contract still defines success before execution.
2. Executor still may not declare PASS or FAIL.
3. Only verify.py may emit final PASS or FAIL.
4. Tamper detection must remain intact.
5. Missing or malformed run binding must fail closed.
6. Replayed stale evidence from a prior run under the same contract must fail.
FILES IN SCOPE
workspace.success.json
src/contract_model.py
scripts/run_agent.py
scripts/verify.py
README.md
ARCHITECTURE.md
tests/test_run_agent.py
tests/test_verify.py
SUCCESS CRITERIA
1. Clean valid run still passes.
2. Existing tamper test still fails on modified artifact bytes.
3. Replaying a previously valid .artifacts bundle under the same contract now fails.
4. Implementation remains minimal and local.
REQUIRED TEST
Add one focused replay regression test proving:
- Run A produces PASS
- runtime state changes under same contract
- replacing .artifacts with Run A bundle
- verify.py returns FAIL because run-instance freshness binding rejects replay
OUTPUT FORMAT
Return only:
1. files changed
2. concise implementation summary
3. exact commands to run
4. blockers
Do not include narrative claims of success beyond executed work.