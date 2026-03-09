# Truth-Bound Execution Proof Matrix

This document records the reproducible verification behavior of the workspace.

Architecture:

Contract → Execution → Evidence → Independent Verification → Verdict

The verifier is the only component allowed to emit PASS or FAIL.

---

## Test Environment

Python 3.11  
pytest  
Local execution

Run tests:

pytest -q

Current result:

34 passed

---

# Proof Matrix

## 1. Clean Run

Command:

python scripts/preflight.py workspace.success.json
rm -rf .artifacts
python scripts/run_agent.py workspace.success.json
python scripts/verify.py workspace.success.json

Expected:

VALID
PASS

Meaning:

A valid contract with correct execution produces PASS.

---

## 2. Invalid Contract

Modify contract with unknown field.

Command:

python scripts/preflight.py workspace.invalid.json

Expected:

INVALID

Execution must not run.

Artifacts must not be created.

---

## 3. Tampered Evidence

Modify an artifact.

Command:

echo "tamper" >> .artifacts/evidence_index.json
python scripts/verify.py workspace.success.json

Expected:

FAIL

Meaning:

Evidence tampering is detected.

---

## 4. Replay Attack

Replay artifacts from a previous run.

Command:

cp -r .artifacts .artifacts_copy
python scripts/run_agent.py workspace.success.json
mv .artifacts_copy .artifacts
python scripts/verify.py workspace.success.json

Expected:

FAIL

Meaning:

Artifact replay is rejected.

---

## 5. Failing Execution Condition

Break a declared success condition.

Command:

python scripts/run_agent.py workspace.execfail.json
python scripts/verify.py workspace.execfail.json

Expected:

FAIL

Meaning:

A valid contract with failing execution produces FAIL.

---

# Verified Properties

Contract admission gate enforced.

Execution cannot proceed with invalid contracts.

Evidence tampering detected.

Artifact replay detected.

Declared execution failures detected.

Independent verifier determines final PASS/FAIL.

---

# Current Test Status

pytest suite: 34 passing tests