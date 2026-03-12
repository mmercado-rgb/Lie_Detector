# Energy Ledger Experiment Framework

## Purpose

This repository implements a **deterministic energy-accounting framework** for evaluating experimental or simulated runs.

It does **not generate physical models itself**.
Instead, it provides an **audit pipeline** that answers one question:

**Does the energy accounting of a run close?**

The framework converts traces and boundary states into a standardized ledger, computes an energy residual, and classifies the result.

---

# System Overview

```
        ┌─────────────────────┐
        │ Scenario Generator  │
        │ or Measurement Data │
        └──────────┬──────────┘
                   │
                   ▼
            ┌─────────────┐
            │ run_to_ledger│
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │ energy_ledger│
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │ residual     │
            │ classification│
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │ batch_runner │
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │results_schema│
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │ analyze_runs │
            └─────────────┘
```

---

# Pipeline

```
scenario generator / measurement
        ↓
run_to_ledger
        ↓
energy_ledger
        ↓
compute_residual
        ↓
classify_run
        ↓
batch_runner
        ↓
results_schema
        ↓
analyze_runs
```

---

# Repository Structure

```
energy_ledger.py
run_to_ledger.py
simulation_stub.py
simulation_variants.py
batch_runner.py
results_schema.py
analyze_runs.py

tests/
  test_energy_ledger.py
  test_run_to_ledger.py
  test_simulation_stub.py
  test_simulation_variants.py
  test_batch_runner.py
  test_results_schema.py

examples/
  ledger_examples.py
```

---

# Core Modules

## energy_ledger.py

Pure deterministic energy accounting.

Functions:

* `compute_stored_energy(state)`
* `integrate_power(trace)`
* `compute_residual(ledger)`
* `classify_run(ledger, tau)`

This module contains **no physics interpretation**, only accounting logic.

---

## run_to_ledger.py

Converts raw run data into the canonical ledger format.

```
run_data
   ↓
build_ledger()
   ↓
ledger
```

Ledger schema:

```
{
  "E_driver": float,
  "E_load": float,
  "E_R": float,
  "E_rad": float,
  "E_parasitic": float,
  "E_stored_t0": float,
  "E_stored_t1": float
}
```

---

## simulation_stub.py

Provides a deterministic single-run example used to verify the pipeline.

---

## simulation_variants.py

Provides three deterministic scenario generators:

* closed system
* underaccounted energy
* apparent excess energy

These scenarios are used to verify classification logic.

---

## batch_runner.py

Executes multiple runs through the accounting pipeline.

```
run_data_list
      ↓
run_batch()
      ↓
[{ledger,residual,label}, ...]
```

---

## results_schema.py

Validates and normalizes output records.

Ensures result structure and numeric validity.

---

## analyze_runs.py

Produces summary statistics across runs:

* total runs
* number closed
* number underaccounted
* number apparent excess

---

# Residual Equation

Energy closure is evaluated using the residual:

```
ρ = E_driver - (
    E_load
    + E_R
    + E_rad
    + E_parasitic
    + (E_stored_t1 - E_stored_t0)
)
```

Where

```
ΔE_stored = E_stored_t1 − E_stored_t0
```

---

# Classification

Given tolerance `tau`:

```
|ρ| ≤ τ      → CLOSED
ρ > τ        → UNDERACCOUNTED
ρ < −τ       → APPARENT_EXCESS
```

---

# What This Framework Proves

If all tests pass, the framework guarantees:

* deterministic energy accounting
* consistent ledger construction
* correct residual calculation
* deterministic classification
* batch execution stability
* reproducible experimental evaluation

---

# What This Framework Does NOT Do

This system does **not**:

* simulate physics
* validate experimental setups
* prove or disprove free-energy claims
* model specific circuits

It provides **a deterministic accounting layer** for evaluating runs.

---

# Design Philosophy

### Accounting First

The framework separates **energy accounting** from **physical modeling**.

Simulations and experiments often include many assumptions and measurement errors.
This system isolates the accounting layer so the evaluation remains objective.

---

### Deterministic Infrastructure

All modules are deterministic:

* no randomness
* no heuristics
* no hidden inference

This ensures:

* reproducibility
* reliable testing
* stable experiment infrastructure

---

### Explicit Energy Boundaries

Every run must explicitly declare energy flows:

* driver input
* load extraction
* resistive loss
* radiation loss
* parasitic loss
* stored energy change

If energy is missing from these categories, it appears in the **residual**.

---

### Separation of Concerns

The system is intentionally layered:

```
generation → accounting → execution → validation → analysis
```

Each layer has a single responsibility, reducing drift and simplifying debugging.

---

# Minimal Example

Run the deterministic scenarios:

```
python examples/ledger_examples.py
```

---

# Running Tests

```
pytest -q
```

All tests passing indicates the accounting pipeline is functioning correctly.

---

# Future Extensions

Potential future modules:

```
tesla_measurement_adapter.py
real_simulator.py
run_metadata.py
dataset_storage.py
visualization.py
parameter_sweep.py
```

These would allow the framework to evaluate real experiments or detailed simulations.

---

# License

This project currently provides research infrastructure for deterministic energy accounting and experimental evaluation.
