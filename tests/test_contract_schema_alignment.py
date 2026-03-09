from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.contract_model import (
    SCHEMA_REQUIRED_CONDITION_FIELDS,
    SUPPORTED_TYPES,
    assert_schema_condition_alignment,
    require_mapping,
)


def load_workspace_schema() -> object:
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "workspace_success.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def extract_schema_condition_types(schema: object) -> set[str]:
    schema_map = schema if isinstance(schema, dict) else {}
    properties = schema_map.get("properties", {}) if isinstance(schema_map, dict) else {}
    success_conditions = properties.get("success_conditions", {}) if isinstance(properties, dict) else {}
    items = success_conditions.get("items", {}) if isinstance(success_conditions, dict) else {}
    variants = items.get("oneOf", []) if isinstance(items, dict) else []
    condition_types: set[str] = set()
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        variant_properties = variant.get("properties", {})
        if not isinstance(variant_properties, dict):
            continue
        type_schema = variant_properties.get("type", {})
        if not isinstance(type_schema, dict):
            continue
        type_const = type_schema.get("const")
        if isinstance(type_const, str):
            condition_types.add(type_const)
    return condition_types


def test_schema_and_contract_model_success_condition_types_match() -> None:
    schema = load_workspace_schema()
    assert_schema_condition_alignment(schema)
    assert extract_schema_condition_types(schema) == set(SUPPORTED_TYPES)


def test_schema_alignment_fails_closed_on_variant_drift() -> None:
    schema = load_workspace_schema()
    drifted = copy.deepcopy(schema)
    drifted_map = require_mapping(drifted, "schema")
    drifted_properties = require_mapping(drifted_map.get("properties"), "schema.properties")
    drifted_success_conditions = require_mapping(
        drifted_properties.get("success_conditions"),
        "schema.properties.success_conditions",
    )
    drifted_items = require_mapping(
        drifted_success_conditions.get("items"),
        "schema.properties.success_conditions.items",
    )
    variants = drifted_items.get("oneOf")
    assert isinstance(variants, list)
    variants.append(
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "type"],
            "properties": {
                "id": {"type": "string"},
                "type": {"const": "command_exit_zero"},
            },
        }
    )

    with pytest.raises(ValueError, match="schema has duplicate success condition type"):
        assert_schema_condition_alignment(drifted)


def test_schema_required_condition_fields_match_contract_model() -> None:
    schema = load_workspace_schema()
    assert_schema_condition_alignment(schema)

    schema_required: dict[str, frozenset[str]] = {}
    schema_map = require_mapping(schema, "schema")
    properties = require_mapping(schema_map.get("properties"), "schema.properties")
    success_conditions = require_mapping(
        properties.get("success_conditions"),
        "schema.properties.success_conditions",
    )
    items = require_mapping(
        success_conditions.get("items"),
        "schema.properties.success_conditions.items",
    )
    variants = items.get("oneOf")
    assert isinstance(variants, list)
    for variant in variants:
        variant_map = require_mapping(variant, "schema success condition variant")
        variant_properties = require_mapping(
            variant_map.get("properties"),
            "schema success condition variant.properties",
        )
        type_schema = require_mapping(
            variant_properties.get("type"),
            "schema success condition variant.properties.type",
        )
        condition_type = type_schema.get("const")
        raw_required = variant_map.get("required")
        assert isinstance(condition_type, str)
        assert isinstance(raw_required, list)
        required = {field for field in raw_required if isinstance(field, str) and field not in {"id", "type"}}
        schema_required[condition_type] = frozenset(required)

    assert schema_required == SCHEMA_REQUIRED_CONDITION_FIELDS
