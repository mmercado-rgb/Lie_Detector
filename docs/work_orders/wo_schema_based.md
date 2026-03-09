Update the truth-bound workspace bootstrap so contract admission is truly schema-based.

Current state
- We now have black-box tests proving the pipeline works through the real programs:
  - scripts/preflight.py
  - scripts/run_agent.py
  - scripts/verify.py
- Added/validated tests cover:
  - valid contract accepted
  - clean execution passes verification
  - extra undeclared artifact fails verification
  - missing declared artifact fails verification
- Important parser finding:
  - the current contract loader/parser does not reliably support inline JSON list syntax
  - block-list JSON syntax is currently required
- preflight.py is only a thin wrapper:
  - it calls src.integrity.load_contract_with_integrity_gate(contract_path)
  - so schema validation must be added in the integrity loading path, not only at the CLI wrapper

Required change
Make contract admission truly schema-based.

Implement
1. Add a formal schema file for workspace.success.json, e.g.
   - schemas/workspace_success.schema.json
2. Validate the loaded contract against that schema inside:
   - src/integrity.py
   - specifically in or under load_contract_with_integrity_gate(...)
3. Keep preflight.py behavior the same:
   - VALID on success
   - INVALID on failure
   - nonzero exit on invalid contract
4. Use a real JSON loader for contract parsing before schema validation.
5. Preserve existing semantic/integrity checks after schema validation.
6. Fail closed on:
   - wrong types
   - missing required fields
   - unknown top-level fields
   - malformed success_conditions entries
7. Keep workspace.success.json as the contract instance file; do not replace it with JSON.

Schema scope
The schema must cover at minimum:
- version
- task_id
- goal
- inputs.repo_root
- inputs.allowed_paths
- success_conditions
- evidence
- policy

Success condition variants currently needed
- command_exit_zero
- command_stdout_contains
- file_exists
- verifier_stdout_contains

Policy/evidence fields should be explicitly typed and required where already enforced.

Tests required
Add or update tests so we prove:
1. valid workspace.success.json passes preflight
2. malformed type in contract fails preflight
3. missing required field fails preflight
4. unknown extra field fails preflight
5. existing black-box verifier integrity tests still pass

Constraints
- Minimal diff
- Do not redesign the pipeline
- Do not weaken current integrity behavior
- Keep preflight/run_agent/verify contract flow intact
- Keep output deterministic and fail-closed

Return format
1. Findings
2. Files changed
3. Schema added
4. Loader/integrity changes
5. Tests added/updated
6. Exact commands run
7. Result