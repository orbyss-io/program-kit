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
    return scenario, expectation, expectation_path


def scenario_authority(root: Path, schemas: Path) -> dict[str, str]:
    scenario, expectation, expectation_path = load_scenario(root, schemas)
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
    atomic_write_json(selection_path, template)
    selection_sha = sha256_file(selection_path)
    documentation = architecture.setdefault("documentation", [])
    if not isinstance(documentation, list):
        raise LiveContractError("LIVE_SCENARIO_ARCHITECTURE_DOCUMENTATION_INVALID")
    documentation[:] = [
        item
        for item in documentation
        if not isinstance(item, dict) or item.get("id") != "building-block-selection"
    ]
    documentation.append(
        {
            "id": "building-block-selection",
            "path": "docs/architecture/building-block-selection.json",
            "sha256": selection_sha,
            "scope": "Accepted building-block selection",
        }
    )
    atomic_write_json(architecture_path, architecture)
    return selection_path, selection_sha


def copied_fixture(scenario_root: Path, scenario: dict[str, Any]) -> Path:
    fixture = scenario_root / safe_relative(scenario["fixture"])
    if not fixture.is_dir():
        raise LiveContractError(f"LIVE_SCENARIO_FIXTURE_MISSING: {fixture}")
    return fixture
