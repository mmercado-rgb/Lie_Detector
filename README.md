Truth-Bound Workspace Bootstrap

A minimal execution framework for testing truth-bound software task execution.

The system separates execution from verification so that success claims cannot be produced by the same component that performs the work.

Execution results are accepted only if they survive independent verification against declared conditions.

Quick Proof (Recommended)

Run the full verification pipeline:

bash scripts/prove.sh

This performs:

environment setup

contract admission

test execution

agent execution
Here is the **properly formatted Markdown (`README.md`) version**. It keeps the same content but uses standard Markdown structure (headings, lists, code blocks) so GitHub renders it correctly.

````markdown
# Truth-Bound Workspace Bootstrap

A minimal execution framework for testing **truth-bound software task execution**.

The system separates **execution from verification** so that success claims cannot be produced by the same component that performs the work.

Execution results are accepted only if they survive **independent verification against declared conditions**.

---

# Quick Proof (Recommended)

Run the full verification pipeline:

```bash
bash scripts/prove.sh
````

This performs:

1. environment setup
2. contract admission
3. test execution
4. agent execution
5. evidence collection
6. independent verification

Expected final output:

```
PASS
```

If any declared condition fails, verification returns:

```
FAIL
```

---

# Reproducible Docker Run

Build container:

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

Docker execution ensures the same environment can reproduce the proof.

---

# Execution Architecture

Flow:

```
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

The core idea is **separation of authority**.

Execution does not determine success.
Verification determines success.

---

# Contract and Schema

Current contract and schema:

**Contract file**

```
workspace.success.json
```

**Authoritative schema**

```
schemas/workspace_success.schema.json
```

**Contract loading path**

```
src.integrity.load_contract_with_integrity_gate(...)
```

Contracts declare **what success means before execution begins**.

Invalid contracts block execution.

---

# Command Boundaries

Each stage has a strict responsibility boundary.

## Admission

```
scripts/preflight.py
```

Purpose:

* validate contract structure
* ensure schema compliance

Output:

```
VALID
```

or

```
INVALID
```

This script performs **no execution**.

---

## Execution

```
scripts/run_agent.py
```

Responsibilities:

* execute declared success conditions
* generate evidence artifacts

Artifacts are written to:

```
.artifacts/
```

This stage **does not produce PASS or FAIL**.

---

## Independent Verification

```
scripts/verify.py
```

Responsibilities:

* validate artifact integrity
* re-evaluate declared success conditions
* detect tampering or replay

Only this stage may emit:

```
PASS
```

or

```
FAIL
```

---

# Required Proof Behavior

The architecture enforces the following invariants.

Invalid contracts:

```
execution blocked
```

Clean execution:

```
PASS
```

Tampered artifacts:

```
FAIL
```

Replayed artifacts:

```
FAIL
```

Failed declared conditions:

```
FAIL
```

The execution system **cannot declare its own success**.

---

# Manual Command Interface

The pipeline can also be run step-by-step.

```bash
python scripts/preflight.py workspace.success.json
python scripts/run_agent.py workspace.success.json
python scripts/verify.py workspace.success.json
python -m pytest -q
```

---

# What This Experiment Demonstrates

This repository demonstrates a minimal architecture where:

* success conditions are declared **before execution**
* execution produces **evidence artifacts**
* verification is **independent of execution**
* claims of success must survive **external verification**

The goal is to explore mechanisms that reduce:

* false success claims
* unverifiable execution
* self-reported task completion

---

# What This Experiment Does NOT Prove

This repository **does not claim to solve**:

* all forms of AI hallucination
* all agent reliability issues
* all sources of experimental bias
* all sources of test manipulation

Instead it demonstrates a narrow architectural principle:

```
execution should not control verification
```

Verification must be **separate, reproducible, and evidence-based**.

---

# Optional Integrity Lock Mechanism

⚠ **Advanced feature**

The `.truth/lock.json` mechanism can bind runtime behavior to specific:

* file hashes
* verifier paths
* command resolutions

This can enforce **stronger integrity guarantees** but may restrict runtime flexibility.

This feature is **not required for the core architecture**.

Use it only if you understand the implications.

---

# License

See `LICENSE`.

---

# Security

See `SECURITY.md`.

---

# Disclaimer

See `DISCLAIMER.md`.

```

If you'd like, I can also show **one small GitHub README improvement used by research repos**: adding a **visual architecture diagram block** so people understand the system in ~5 seconds instead of reading the whole document.
```

evidence collection

independent verification

Expected final output:

PASS

If any declared condition fails, verification returns:

FAIL
Reproducible Docker Run

Build container:

docker build -f .devcontainer/Dockerfile -t lie-detector:truth-bound .

Run the proof pipeline inside the container:

docker run --rm -it \
-v "$(pwd):/workspaces/Lie_Detector" \
-w /workspaces/Lie_Detector \
lie-detector:truth-bound \
bash scripts/prove.sh

Docker execution ensures the same environment can reproduce the proof.

Execution Architecture

Flow:

Contract admission
    ->
Execution
    ->
Evidence generation
    ->
Independent verification
    ->
Verdict

The core idea is separation of authority.

Execution does not determine success.
Verification determines success.

Contract and Schema

Current contract and schema:

Contract file
workspace.success.json

Authoritative schema
schemas/workspace_success.schema.json

Contract loading path
src.integrity.load_contract_with_integrity_gate(...)

Contracts declare what success means before execution begins.

Invalid contracts block execution.

Command Boundaries

Each stage has a strict responsibility boundary.

Admission
scripts/preflight.py

Purpose:

validate contract structure

ensure schema compliance

Output:

VALID

or

INVALID

This script performs no execution.

Execution
scripts/run_agent.py

Responsibilities:

execute declared success conditions

generate evidence artifacts

Artifacts are written to:

.artifacts/

This stage does not produce PASS or FAIL.

Independent Verification
scripts/verify.py

Responsibilities:

validate artifact integrity

re-evaluate declared success conditions

detect tampering or replay

Only this stage may emit:

PASS

or

FAIL
Required Proof Behavior

The architecture enforces the following invariants.

Invalid contracts:

execution blocked

Clean execution:

PASS

Tampered artifacts:

FAIL

Replayed artifacts:

FAIL

Failed declared conditions:

FAIL

The execution system cannot declare its own success.

Manual Command Interface

The pipeline can also be run step-by-step.

python scripts/preflight.py workspace.success.json
python scripts/run_agent.py workspace.success.json
python scripts/verify.py workspace.success.json
python -m pytest -q
What This Experiment Demonstrates

This repository demonstrates a minimal architecture where:

success conditions are declared before execution

execution produces evidence artifacts

verification is independent of execution

claims of success must survive external verification

The goal is to explore mechanisms that reduce:

false success claims

unverifiable execution

self-reported task completion

What This Experiment Does NOT Prove

This repository does not claim to solve:

all forms of AI hallucination

all agent reliability issues

all sources of experimental bias

all sources of test manipulation

Instead it demonstrates a narrow architectural principle:

execution should not control verification

Verification must be separate, reproducible, and evidence-based.

Optional Integrity Lock Mechanism

⚠ Advanced feature.

The .truth/lock.json mechanism can bind runtime behavior to specific:

file hashes

verifier paths

command resolutions

This can enforce stronger integrity guarantees but may restrict runtime flexibility.

This feature is not required for the core architecture.

Use it only if you understand the implications.

## License

See LICENSE.

## Security

See SECURITY.md.

## Disclaimer

See DISCLAIMER.md.