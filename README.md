# Truth-Bound Workspace Bootstrap

A minimal Python project for experimenting with truth-bound task execution.

The core design goal is simple: execution is not allowed to decide whether it succeeded. The system separates contract admission, task execution, evidence generation, and independent verification so success claims must survive a verifier outside the executor.

## What It Does

- Validates a declared success contract before execution starts
- Executes the declared work and writes evidence artifacts
- Re-checks outcomes from evidence during independent verification
- Rejects stale or tampered artifacts

## Repository Layout

- `scripts/preflight.py`: contract admission only, returns `VALID` or `INVALID`
- `scripts/run_agent.py`: execution and evidence generation
- `scripts/verify.py`: independent verification, returns `PASS` or `FAIL`
- `schemas/workspace_success.schema.json`: authoritative contract schema
- `workspace.success.json`: example valid contract

## Quick Start

Create a virtual environment, install developer dependencies, and run the checks:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
pytest -q
python -m ruff check .
```

Then run the full proof pipeline:

```bash
python scripts/preflight.py workspace.success.json
python scripts/run_agent.py workspace.success.json
python scripts/verify.py workspace.success.json
```

Expected verifier output for a clean run:

```text
PASS
```

## Docker

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

## Architecture

```text
Contract admission
    ->
Execution
    ->
Evidence generation
    ->
Independent verification
    ->
Verdict
```

Only `scripts/verify.py` is allowed to emit the final success verdict.

## Optional Integrity Lock

The `.truth/lock.json` mechanism is an advanced integrity feature that can pin verifier/runtime behavior to specific file hashes and command resolutions. It is optional and not required for the core workflow.

## Limits

This repository is an experiment, not a production assurance system. It does not claim to solve hallucination, reliability, or safety in general. It demonstrates a narrower principle: execution should not control verification.

## Project Documents

- `ARCHITECTURE.md`
- `SECURITY.md`
- `DISCLAIMER.md`
- `docs/proof_matrix.md`

## License

MIT. See `LICENSE`.
