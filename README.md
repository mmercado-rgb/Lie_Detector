# Truth-Bound Workspace Bootstrap

A minimal Python project for experimenting with **truth-bound task execution**.

The core design goal is simple: **execution is not allowed to decide whether it succeeded**.
The system separates contract admission, task execution, evidence generation, and independent verification so success claims must survive a verifier outside the executor.

A **truth-bound workflow** is one where success claims must be derived from verifiable evidence rather than asserted by the executor.

Many systems allow executors to report their own success. This project explores a stricter model where success must be verified independently from produced artifacts.

In this repository a **“lie”** means any claim about execution that cannot be verified from the produced evidence.

---

# Execution Model

```
Contract admission
    →
Execution
    →
Evidence generation
    →
Independent verification
    →
Verdict
```

Only the verifier is allowed to decide whether a run succeeded.

---

# What It Does

* Validates a declared success contract before execution starts
* Executes the declared work and writes evidence artifacts
* Re-checks outcomes from evidence during independent verification
* Rejects tampered artifacts and artifacts replayed from previous runs

---

# Repository Layout

* `scripts/preflight.py` — contract admission only, returns `VALID` or `INVALID`
* `scripts/run_agent.py` — execution and evidence generation
* `scripts/verify.py` — independent verification, returns `PASS` or `FAIL`
* `schemas/workspace_success.schema.json` — authoritative contract schema
* `workspace.success.json` — example valid contract

---

# Quick Start

Create a virtual environment and install developer dependencies.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
pytest -q
python -m ruff check .
```

# Ways to Break It

This repository is intentionally small so reviewers can attempt to violate the execution–verification separation.

Some simple experiments:

### 1. Tamper With Evidence

Run a successful pipeline first.

```bash
python scripts/preflight.py workspace.success.json
python scripts/run_agent.py workspace.success.json
```

Then modify any file under `.artifacts/` before verification.

Example:

```bash
echo "tamper" >> .artifacts/some_file
```

Verification should fail:

```bash
python scripts/verify.py workspace.success.json
```

Expected result:

```
FAIL
```

---

### 2. Replay Artifacts From a Previous Run

Run the pipeline once and save the `.artifacts/` directory.

Then execute the agent again but replace the newly generated artifacts with the old ones before verification.

Verification should detect the replay and fail.

---

### 3. Modify the Contract After Execution

Run the agent normally:

```bash
python scripts/run_agent.py workspace.success.json
```

Then edit the contract file before verification.

Example change:

* alter a declared success condition
* change a command
* alter an artifact reference

Verification should fail because the evidence no longer matches the declared contract.

---

### 4. Introduce Undeclared Artifacts

Add a file to `.artifacts/` that was not declared by the contract.

Verification should fail due to artifact closure checks.

---

### 5. Break Declared Success Conditions

Modify a command or expected output in the contract so that the declared condition cannot be satisfied.

The executor may run successfully, but verification should still return:

```
FAIL
```

---

### What Should Not Be Possible

A successful verification (`PASS`) should require that:

* the contract was valid at admission
* the executor produced evidence matching the contract
* the evidence artifacts are untampered
* the artifacts correspond to the current run
* verification independently confirms the declared conditions

If you discover a way to produce `PASS` while violating these assumptions, that would indicate a flaw in the model.


Run the proof pipeline:

```bash
python scripts/preflight.py workspace.success.json
python scripts/run_agent.py workspace.success.json
python scripts/verify.py workspace.success.json
```

Expected verifier output for a clean run:

```
PASS
```

---
Try the Example Contracts

The repository includes three contracts that demonstrate different outcomes.

Valid contract (expected PASS)
python scripts/preflight.py workspace.success.json
python scripts/run_agent.py workspace.success.json
python scripts/verify.py workspace.success.json

Expected result:

PASS
Invalid contract (blocked at admission)
python scripts/preflight.py workspace.invalid.json

Expected result:

INVALID

Execution will not start.

Execution failure (verification FAIL)
python scripts/preflight.py workspace.execfail.json
python scripts/run_agent.py workspace.execfail.json
python scripts/verify.py workspace.execfail.json

Expected result:

FAIL

The executor runs, but verification rejects the result.

# Docker

Build the container:

```bash
docker build -f .devcontainer/Dockerfile -t lie-detector:truth-bound .
```

Run the proof pipeline inside the container:

```bash
docker run --rm -it \
  -v "$(pwd):/workspaces/Lie_Detector" \
  -w /workspaces/Lie_Detector \
  lie-detector:truth-bound \
  bash scripts/prove.sh
```

---

# Optional Integrity Lock

The `.truth/lock.json` mechanism is an advanced integrity feature that can pin verifier/runtime behavior to specific file hashes and command resolutions.

It is optional and not required for the core workflow.

---

# Limits

This repository is an experiment, not a production assurance system.

It does **not** claim to solve hallucination, reliability, or safety in general.

It demonstrates a narrower principle:

**execution should not control verification.**

---

# Project Documents

* `ARCHITECTURE.md`
* `SECURITY.md`
* `DISCLAIMER.md`
* `docs/proof_matrix.md`

---

# Feedback Welcome

This project is experimental and feedback from engineers, security researchers, and verification practitioners is welcome.

Particularly useful feedback areas include:

* weaknesses in the execution/verification separation
* possible artifact replay or tampering paths
* contract validation gaps
* integrity assumptions in the verifier
* architectural simplifications

Issues and discussion are encouraged.

---

# License

MIT. See `LICENSE`.

---

# Repository Structure

```
Lie_Detector/
├── schemas/                  # authoritative contract schema
├── scripts/                  # admission, execution, verification entrypoints
│   ├── preflight.py
│   ├── run_agent.py
│   └── verify.py
├── src/                      # contract, integrity, and evidence logic
│   ├── contract_model.py
│   ├── evidence.py
│   └── integrity.py
├── tests/                    # proof and regression coverage
├── docs/                     # proof matrix, work orders, questions
├── .truth/                   # optional integrity state
├── workspace.success.json    # valid example contract
├── workspace.invalid.json    # invalid example contract
└── workspace.execfail.json   # failing execution example
```


