# Lie Detector

Lie Detector is a small Python research project for experimenting with a truth-bound execution model.

The central rule is strict: the executor is not allowed to declare success. It can run work and write evidence, but only the verifier is allowed to produce the final verdict.

## Purpose

This repository demonstrates a workflow where:

- a success contract is admitted before execution
- the executor produces evidence artifacts
- a separate verifier checks those artifacts
- `PASS` or `FAIL` comes only from verification

In this project, a "lie" is any success claim that is not supported by the recorded evidence.

## Truth-Bound Workflow

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

Authority boundaries:

- `scripts/preflight.py` admits or rejects a contract and prints `VALID` or `INVALID`
- `scripts/run_agent.py` executes declared work and writes evidence
- `scripts/verify.py` is the final authority and prints `PASS` or `FAIL`

The executor cannot claim success. A clean execution run is not the same thing as a verified success.

## Repository Layout

```text
Lie_Detector/
|-- schemas/                      # contract schema
|-- scripts/                      # entrypoints
|   |-- preflight.py
|   |-- run_agent.py
|   `-- verify.py
|-- src/                          # contract, evidence, and integrity logic
|-- tests/                        # regression and proof-oriented tests
|-- docs/                         # proof notes and work orders
|-- .truth/                       # optional integrity state
|-- workspace.success.json        # valid example contract
|-- workspace.invalid.json        # admission failure example
|-- workspace.execfail.json       # verification failure example
`-- ARCHITECTURE.md
```


## Quick Start

Clone the repository and create a virtual environment.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
````

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

### Run the truth-bound verification pipeline

```bash
python scripts/preflight.py workspace.success.json
python scripts/run_agent.py workspace.success.json
python scripts/verify.py workspace.success.json
```

Or use the helper script:

```powershell
.\scripts\reset_truth_state.ps1
```

### Expected outcomes for the included examples

* `workspace.success.json` → `VALID` → execution → `PASS`
* `workspace.invalid.json` → `INVALID` at admission
* `workspace.execfail.json` → admitted → execution → `FAIL`

## Usage Example

Example truth-bound workflow:

```bash
python scripts/preflight.py workspace.success.json
# VALID

python scripts/run_agent.py workspace.success.json
# executor writes evidence under .artifacts/

python scripts/verify.py workspace.success.json
# PASS
```

What this proves:

* the contract was accepted before execution
* the recorded evidence matched the declared work
* the evidence was fresh and untampered at verification time
* the verifier, not the executor, decided the result


## What to Try

Useful adversarial checks include:

- edit files in `.artifacts/` before verification
- replay artifacts from a previous run
- modify the contract after execution
- add undeclared files to the artifact directory
- declare conditions that the executor cannot actually satisfy

The verifier should reject these cases with `FAIL`.

## Limitations

This repository is an experiment, not a production assurance system.

It does not claim to solve:

- hallucination in general
- software correctness in general
- system security in general
- safety-critical validation

It demonstrates a narrower claim: execution should not control verification.

## Development Notes

- The authoritative schema is `schemas/workspace_success.schema.json`
- Architecture notes are in `ARCHITECTURE.md`
- Security reporting guidance is in `SECURITY.md`
- Research and usage limitations are in `DISCLAIMER.md`

## Contributing

Small, focused contributions are preferred. See `CONTRIBUTING.md` for the expected workflow and `CODE_OF_CONDUCT.md` for community standards.

## License

MIT. See `LICENSE`.
