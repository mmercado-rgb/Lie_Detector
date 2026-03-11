# Contributing

## Scope

This repository is a small research project about truth-bound execution and independent verification. Contributions should preserve that focus.

## How to Contribute

1. Open an issue for bugs, unclear behavior, documentation gaps, or design concerns.
2. Keep changes narrow and explain the behavioral impact clearly.
3. Add or update tests when changing runtime behavior.
4. Update documentation when the public contract, workflow, or limits change.
5. Open a pull request with a concise summary and reproduction notes.

## Development Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Contribution Guidelines

- Preserve the authority boundary: the executor must not become the source of final success.
- Prefer simple changes over framework expansion.
- Do not commit generated artifacts, virtual environments, or local cache directories.
- Keep documentation plain and specific.

## Pull Request Checklist

- the change is scoped to a clear problem
- tests or reasoning cover the behavior change
- docs are updated if user-visible behavior changed
- no generated local files are included

## Questions

If you are unsure whether a change fits the project, open an issue before implementing it.
