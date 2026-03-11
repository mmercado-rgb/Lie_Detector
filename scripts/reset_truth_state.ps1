# Reset truth-bound artifacts and continuity state, then execute pipeline

Write-Host "Resetting artifacts and continuity state..."

if (Test-Path ".artifacts") {
    Remove-Item -Recurse -Force ".artifacts"
}

if (Test-Path ".truth\latest_run_id.txt") {
    Remove-Item -Force ".truth\latest_run_id.txt"
}

Write-Host "Running preflight..."
python scripts/preflight.py workspace.success.json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running executor..."
python scripts/run_agent.py workspace.success.json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running verifier..."
python scripts/verify.py workspace.success.json
exit $LASTEXITCODE