"""Persist deterministic traceability artifacts for experiment runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from experiment.results_schema import make_result_record
from experiment.run_metadata import normalize_run_metadata
from experiment.uncertainty_budget import normalize_uncertainty_budget


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _slugify(name: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "_" for char in name.strip())
    while "__" in slug:
        slug = slug.replace("__", "_")
    slug = slug.strip("_")
    if not slug:
        raise ValueError("summary name must contain at least one alphanumeric character")
    return slug


def write_run_dataset(
    root_dir: str | Path,
    metadata: object,
    raw_traces: object,
    normalized_traces: object,
    result: object,
    uncertainty_budget: object | None = None,
    claim_assessment: object | None = None,
) -> dict[str, object]:
    """Write all traceability artifacts for one run to a deterministic layout."""
    root = Path(root_dir)
    normalized_metadata = normalize_run_metadata(metadata)
    normalized_result = make_result_record(result)

    run_seed = {
        "metadata": normalized_metadata,
        "raw_traces": raw_traces,
    }
    run_id = hashlib.sha256(_canonical_json(run_seed).encode("ascii")).hexdigest()[:16]
    run_dir = root / "runs" / run_id

    file_map: dict[str, str] = {
        "metadata": f"runs/{run_id}/metadata.json",
        "raw_traces": f"runs/{run_id}/raw_traces.json",
        "normalized_traces": f"runs/{run_id}/normalized_traces.json",
        "ledger": f"runs/{run_id}/ledger.json",
        "result": f"runs/{run_id}/result.json",
    }

    if uncertainty_budget is not None:
        file_map["uncertainty_budget"] = f"runs/{run_id}/uncertainty_budget.json"
    if claim_assessment is not None:
        file_map["claim_assessment"] = f"runs/{run_id}/claim_assessment.json"

    manifest = {
        "run_id": run_id,
        "files": file_map,
    }

    _write_json(run_dir / "metadata.json", normalized_metadata)
    _write_json(run_dir / "raw_traces.json", raw_traces)
    _write_json(run_dir / "normalized_traces.json", normalized_traces)
    _write_json(run_dir / "ledger.json", normalized_result["ledger"])
    _write_json(run_dir / "result.json", normalized_result)
    if uncertainty_budget is not None:
        _write_json(
            run_dir / "uncertainty_budget.json",
            normalize_uncertainty_budget(uncertainty_budget),
        )
    if claim_assessment is not None:
        _write_json(run_dir / "claim_assessment.json", claim_assessment)
    _write_json(run_dir / "manifest.json", manifest)

    file_map["manifest"] = f"runs/{run_id}/manifest.json"
    return manifest


def write_summary(
    root_dir: str | Path,
    summary_name: str,
    summary: object,
    run_manifests: list[object],
) -> dict[str, str]:
    """Write a deterministic batch summary file with referenced run ids."""
    root = Path(root_dir)
    slug = _slugify(summary_name)
    path = root / "summaries" / f"{slug}.json"
    run_ids: list[str] = []
    for manifest in run_manifests:
        if not isinstance(manifest, dict) or "run_id" not in manifest:
            raise ValueError("run_manifests must contain manifest dictionaries with run_id")
        run_id = manifest["run_id"]
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_manifest run_id must be a non-empty string")
        run_ids.append(run_id)

    payload = {
        "name": slug,
        "run_ids": run_ids,
        "summary": summary,
    }
    _write_json(path, payload)
    return {"name": slug, "path": f"summaries/{slug}.json"}
