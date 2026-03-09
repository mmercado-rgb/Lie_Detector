The workspace now runs as follows:

python scripts/preflight.py workspace.success.json → VALID
python scripts/run_agent.py workspace.success.json → executes and writes artifacts
python scripts/verify.py workspace.success.json → FAIL

No tampering has occurred.

Please inspect:
.artifacts/verify_result.json
workspace.success.json
scripts/verify.py
.artifacts/tests-pass.exitcode.txt
.artifacts/lint-pass.exitcode.txt

Question:
Why does the verifier return FAIL on a clean baseline, and which specific condition or integrity check is causing it?