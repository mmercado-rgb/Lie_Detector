from __future__ import annotations

from pathlib import Path


DEFAULT_RESERVED_WORDS = [
    "PASS",
    "FAIL",
    "passed",
    "verified",
    "complete",
    "ready",
    "successful",
]


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(content, encoding="utf-8")


def write_contract(
    root: Path,
    *,
    success_conditions: list[dict[str, str]],
    output_dir: str = ".artifacts",
    freshness_path: str = ".truth/latest_run_id.txt",
    require_black_box_verification: bool = True,
    reserved_outcome_words: list[str] | None = None,
) -> Path:
    reserved_words = reserved_outcome_words or DEFAULT_RESERVED_WORDS
    lines = [
        "version: 2",
        'task_id: "test-001"',
        'goal: "Exercise contract flow"',
        "inputs:",
        '  repo_root: "."',
        "  allowed_paths:",
        '    - "src/**"',
        '    - "tests/**"',
        '    - "scripts/**"',
        "success_conditions:",
    ]

    for condition in success_conditions:
        lines.append(f"  - id: {yaml_quote(condition['id'])}")
        lines.append(f"    type: {yaml_quote(condition['type'])}")
        if "command" in condition:
            lines.append(f"    command: {yaml_quote(condition['command'])}")
        if "path" in condition:
            lines.append(f"    path: {yaml_quote(condition['path'])}")
        if "contains" in condition:
            lines.append(f"    contains: {yaml_quote(condition['contains'])}")

    lines.extend(
        [
            "evidence:",
            f"  output_dir: {yaml_quote(output_dir)}",
            "  save_stdout: true",
            "  save_stderr: true",
            "  save_exit_codes: true",
            '  hash_algorithm: "sha256"',
            f"  freshness_path: {yaml_quote(freshness_path)}",
            "policy:",
            "  fail_closed: true",
            "  executor_cannot_claim_success: true",
            "  verifier_is_final_authority: true",
            f"  require_black_box_verification: {'true' if require_black_box_verification else 'false'}",
            "  reserved_outcome_words:",
        ]
    )
    for word in reserved_words:
        lines.append(f"    - {yaml_quote(word)}")

    contract_path = root / "workspace.success.yaml"
    write_file(contract_path, "\n".join(lines) + "\n")
    return contract_path


def build_sample_workspace(root: Path) -> None:
    write_file(root / "src/app.py", "def marker() -> str:\n    return 'ok'\n")
