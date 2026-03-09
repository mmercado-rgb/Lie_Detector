Problem:
Repository tests are failing because run_agent_main(...) returns exit code 2 instead of 0.

Evidence:
All failing tests show:

AssertionError: assert 2 == 0
where 2 = run_agent_main(...)

run_agent.py returns 2 only when an exception occurs:

except Exception:
    print("execution error")
    return 2

Tests execute the agent inside a temporary workspace:

monkeypatch.chdir(tmp_path)
run_agent_main(["run_agent.py", str(contract_path)])

But run_agent.py determines repo_root using:

REPO_ROOT = Path(__file__).resolve().parents[1]

So the agent assumes the repository root is where the code lives rather than the workspace containing workspace.success.json.

This causes run_agent to fail when tests run in tmp_path.

Task:
Modify run_agent.py so the workspace root is derived from the contract path instead of the script location.

Expected behavior:
repo_root should resolve to the directory containing workspace.success.json so run_agent works inside temporary test workspaces.

Goal:
Make run_agent_main(["run_agent.py", contract_path]) succeed inside pytest tmp_path environments and return 0 when execution succeeds.

Provide the minimal patch to run_agent.py.