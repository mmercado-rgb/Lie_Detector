The live experiment shows a verifier integrity gap.

Repro:
1. run_agent.py on workspace.success.yaml
2. verify.py => PASS
3. manually inject .artifacts/unauthorized.txt
4. verify.py => still PASS

Conclusion:
verify.py does not reject undeclared extra files that exist in .artifacts but are absent from evidence_index.json.

This means the verifier currently trusts the index more than the actual artifact directory contents.

Required fix:
Make verification fail closed on any unexpected file in the evidence output directory.

Required rule:
Actual artifact directory contents must exactly match the declared/expected artifact set, excluding only explicitly allowed verifier-owned files if such a list is intentionally defined.

Please implement:
1. a deterministic artifact inventory step in verify.py
2. comparison of on-disk files vs expected indexed files
3. FAIL on any extra file
4. tests covering:
   - baseline pass
   - injected extra file fails
   - missing indexed file fails
   - optionally, allowed internal verifier files pass only if explicitly allowlisted