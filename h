[33mcommit d59e8696010887f1a9235ff23ad7a460982df3da[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mmain[m[33m)[m
Author: Maxi Mercado <mmercado@enhancedpsychiatry.com>
Date:   Mon Mar 9 04:24:34 2026 +0000

    Truth-bound workspace bootstrap: add contract preflight, executor, verifier, artifact integrity tests, and verification harness

 .codex/config.toml                                |   4 [32m+[m
 .devcontainer/Dockerfile                          |   2 [32m+[m
 .devcontainer/devcontainer.json                   |  46 [32m++[m
 .gitignore                                        |  50 [32m+[m[31m-[m
 .truth/latest_run_id.txt                          |   1 [32m+[m
 ARCHITECTURE.md                                   |   4 [32m+[m[31m-[m
 README.md                                         |  10 [32m+[m[31m-[m
 docs/questions/quest1.md                          |  83 [32m++++[m
 docs/questions/quest2.md                          |  17 [32m+[m
 docs/questions/quest3.md                          |  38 [32m++[m
 docs/questions/quest4.md                          |  28 [32m++[m
 docs/work_orders/Wo_freshness.md                  |  60 [32m+++[m
 .../work_orders/wo_Admission Gate Integrity v1.md |  62 [32m+++[m
 .../wo_Truth-Bound Workspace Bootstrap.md         | 474 [32m+++++++++[m[31m----------[m
 docs/work_orders/wo_removethejson.md              |  37 [32m++[m
 docs/work_orders/wo_verify.md                     |   9 [32m+[m
 scripts/preflight.py                              |   8 [32m+[m[31m-[m
 scripts/run_agent.py                              |  38 [32m+[m[31m-[m
 scripts/verify.py                                 |  98 [32m+++[m[31m-[m
 src/contract_model.py                             |  32 [32m+[m[31m-[m
 src/integrity.py                                  | 261 [32m++++++++++[m
 tests/helpers.py                                  |   2 [32m+[m
 tests/test_preflight.py                           |  25 [32m+[m
 tests/test_run_agent.py                           |  51 [32m++[m
 tests/test_smoke.py                               |   2 [32m+[m
 tests/test_verify.py                              | 106 [32m+++++[m
 workspace.success.json                            |  91 [32m++[m[31m--[m
 27 files changed, 1305 insertions(+), 334 deletions(-)
