TASK: Enforce strictly schema-bound contract loading.
GOAL: All contracts must be validated by schemas/workspace_success.schema.json before any runtime use.
REQUIREMENTS:
1. Only this function may load contracts: load_contract_with_integrity_gate(contract_path).
2. Required loading order:
   schema=json.load(schema_path)
   assert_schema_condition_alignment(schema)
   raw_contract=parse_contract_yaml(contract_path)
   validate_with_schema(schema,raw_contract)
   contract=validate_contract(raw_contract)
   return contract
3. Remove or forbid any direct parsing of the contract outside this gate: json.load,json.safe_load,SimpleYamlParser,json.loads(contract file).
4. Ensure scripts/preflight.py,scripts/run_agent.py,scripts/verify.py call load_contract_with_integrity_gate and do not parse JSON themselves.
5. Runtime code must operate only on the typed Contract model,never raw dicts.
6. Fail closed: if schema validation fails,execution must stop immediately.
7. Add a regression test that fails if any runtime file loads the contract outside the gate.
   OUTPUT: Provide modified files,diff,confirmation that all contract loads pass through the schema gate,and test results.
