Align workspace_success.schema.json and src/contract_model.py so structural validation lives in schema and semantic validation remains in contract_model.py.

Required:
1. Review all validators in src/contract_model.py.
2. Move shape/type/required-field enforcement into workspace_success.schema.json where possible.
3. Keep only semantic/domain rules in src/contract_model.py.
4. Ensure every success_condition variant accepted by contract_model.py is represented in schema, and vice versa.
5. Add tests proving schema and contract_model stay aligned.
6. Fail closed on any schema/model drift.