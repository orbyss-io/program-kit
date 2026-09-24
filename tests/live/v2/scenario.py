from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .common import LiveContractError, atomic_write_json, canonical_sha256, file_inventory, load_object, safe_relative, sha256_file, validate


def load_scenario(root: Path, schemas: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    scenario_path = root / "scenario.json"
    scenario = load_object(scenario_path)
    validate(scenario, load_object(schemas / "scenario.schema.json"))
    expectation_path = root / safe_relative(scenario["activeExpectation"])
    expectation = load_object(expectation_path)
    validate(expectation, load_object(schemas / "candidate-expectation.schema.json"))
    if expectation['scenario'] != f"{scenario['id']}@{scenario['version']}":
        raise LiveContractError('LIVE_SCENARIO_EXPECTATION_IDENTITY_MISMATCH')
    return scenario, expectation, expectation_path


def scenario_authority(root: Path, schemas: Path) -> dict[str, str]:
    scenario, expectation, expectation_path = load_scenario(root, schemas)
    from .intake_handoff import validate_provenance
    validate_provenance(root / safe_relative(scenario['fixture']))
    return {
        "id": scenario["id"],
        "version": scenario["version"],
        "digest": canonical_sha256(
            {
                "scenarioSha256": sha256_file(root / "scenario.json"),
                "expectationSha256": sha256_file(expectation_path),
                "fixture": scenario["fixture"],
                "fixtureInventorySha256": canonical_sha256(
                    file_inventory(root / safe_relative(scenario["fixture"]))
                ),
                "selectionTemplateSha256": sha256_file(root / safe_relative(scenario["selectionTemplate"])),
            }
        ),
        "expectationId": expectation["expectationId"],
    }


def bind_selection(scenario_root: Path, project: Path, scenario: dict[str, Any]) -> tuple[Path, str]:
    """Read-only admission of the selection accepted by the native bootstrap.

Never repair or replace architecture/selection after final approval: doing so
invalidates the very approval the checkpoint is meant to preserve.
"""
    architecture_path = project / "docs/architecture/architecture-map.json"
    architecture = load_object(architecture_path)
    decisions = architecture.get("decisions")
    if not isinstance(decisions, list):
        raise LiveContractError("LIVE_SCENARIO_ARCHITECTURE_DECISIONS_REQUIRED")
    statuses = {
        item.get("id"): item.get("status")
        for item in decisions
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    missing = [decision for decision in scenario["acceptedDecisionIds"] if statuses.get(decision) != "Accepted"]
    if missing:
        raise LiveContractError(f"LIVE_SCENARIO_ACCEPTED_DECISIONS_MISSING: {missing}")
    template = load_object(scenario_root / safe_relative(scenario["selectionTemplate"]))
    selection_path = project / "docs/architecture/building-block-selection.json"
    actual = load_object(selection_path)
    if actual.get('status') != 'Accepted' or actual.get('catalog') != template['catalog']:
        raise LiveContractError('LIVE_SCENARIO_ACCEPTED_SELECTION_MISMATCH')
    for field in ('scopes', 'targets', 'instances'):
        expected = {item['id']: item for item in template[field]}
        records = actual.get(field, [])
        observed = {item['id']: item for item in records}
        if len(records) != len(observed) or set(expected) != set(observed):
            raise LiveContractError('LIVE_SCENARIO_SELECTION_SCOPE_MISMATCH: ' + field)
        for identity, record in expected.items():
            if any(observed[identity].get(key) != value for key, value in record.items() if key != 'placement'):
                raise LiveContractError('LIVE_SCENARIO_SELECTION_CHOICE_MISMATCH: ' + identity)
    if not set(scenario['acceptedDecisionIds']) <= set(actual.get('authority', {}).get('decisionIds', [])):
        raise LiveContractError('LIVE_SCENARIO_SELECTION_AUTHORITY_MISMATCH')
    selection_sha = sha256_file(selection_path)
    documentation = architecture.get("documentation", [])
    if not isinstance(documentation, list):
        raise LiveContractError("LIVE_SCENARIO_ARCHITECTURE_DOCUMENTATION_INVALID")
    if not any(item.get('path') == 'docs/architecture/building-block-selection.json' and item.get('sha256') == selection_sha for item in documentation):
        raise LiveContractError('LIVE_SCENARIO_SELECTION_NOT_BOUND_BY_ARCHITECTURE')
    return selection_path, selection_sha


def copied_fixture(scenario_root: Path, scenario: dict[str, Any]) -> Path:
    fixture = scenario_root / safe_relative(scenario["fixture"])
    if not fixture.is_dir():
        raise LiveContractError(f"LIVE_SCENARIO_FIXTURE_MISSING: {fixture}")
    return fixture


def validate_candidate_catalog(scenario_root: Path, release_root: Path, schemas: Path):
    """Reject incompatible fixture pins before issuing or consuming a paid manifest."""
    import importlib.util
    import sys
    source = release_root / 'extensions/program-kit-building-blocks/scripts/building_blocks.py'
    spec = importlib.util.spec_from_file_location('live_scenario_catalog_check', source)
    if spec is None or spec.loader is None:
        raise LiveContractError('LIVE_SCENARIO_CATALOG_PROVIDER_MISSING')
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(spec.name)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        catalog = load_object(release_root / 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.json')
        scenario, expectation, _ = load_scenario(scenario_root, schemas)
        selection = load_object(scenario_root / safe_relative(scenario['selectionTemplate']))
        expected = module.catalog_resolution_sha256(catalog)
        if expectation['catalogSha256'] != expected or selection['catalog']['resolutionSha256'] != expected:
            raise LiveContractError('LIVE_SCENARIO_CATALOG_STALE: select a separately versioned fixture for this release; no paid authorization may be consumed')
    finally:
        if previous is None:
            sys.modules.pop(spec.name, None)
        else:
            sys.modules[spec.name] = previous
