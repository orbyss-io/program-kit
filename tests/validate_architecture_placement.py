"""Offline greenfield placement and recovery regressions; starts no agents."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import validate_building_blocks as bt
import validate_bootstrap_context as ct
import validate_bootstrap_semantics as semantic

ROOT = Path(__file__).resolve().parents[1]


def context_error(module, fragment, action):
    try:
        action()
    except module.ContextError as error:
        assert fragment in str(error), str(error)
    else:
        raise AssertionError(f"Expected context diagnostic: {fragment}")


def workflow_checks(root, context, run_id):
    """Real workflow engine/CLI, mocked agent dispatch; no coding agent can start."""
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
    from specify_cli.workflows.steps.command import CommandStep
    import yaml

    shutil.copytree(ROOT / "extensions/program-kit-governance", root / ".specify/extensions/program-kit-governance", dirs_exist_ok=True)
    shipped = yaml.safe_load((ROOT / "workflows/program-kit-bootstrap/workflow.yml").read_text())
    steps = [copy.deepcopy(step) for step in shipped["steps"]
             if step["id"] in {"architecture-dispatch", "validate-architecture-output"}]
    steps[0]["integration"] = "codex"
    steps[0]["input"] = {"args": "offline fixture; dispatch is mocked"}
    # Use the test interpreter explicitly; the shipped command otherwise runs unchanged.
    steps[1]["run"] = steps[1]["run"].replace("python ", f'"{sys.executable}" ', 1)
    definition = WorkflowDefinition({"workflow": {"id": "program-kit-bootstrap", "name": "Architecture fixture"}, "steps": steps})

    def blocked_dispatch(*args, **kwargs):
        context.record_architecture_blocked(root, run_id, "Renderer compatibility unresolved", "architecture", "Compare supported renderer options")
        return {"exit_code": 0, "stdout": "BLOCKED", "stderr": ""}

    engine = WorkflowEngine(root)
    # Preserve the seeded typed inputs in the reduced workflow fixture.
    definition.inputs = {}
    with patch.object(CommandStep, "_try_dispatch", side_effect=blocked_dispatch) as dispatch:
        state = engine.execute(definition, run_id=run_id)
        assert dispatch.call_count == 1
        assert state.status.value == "failed"
        assert state.current_step_id == "validate-architecture-output"
        gate = state.step_results["validate-architecture-output"]
        assert "Renderer compatibility unresolved" in gate["output"]["stderr"]
        assert "Required architecture output is missing" not in gate["output"]["stderr"]
        assert state.step_results["architecture-dispatch"]["status"] == "completed"
        # The real supported resume command retries the failed gate, never the dispatch.
        again = engine.resume(run_id)
        assert again.status.value == "failed" and dispatch.call_count == 1


def main():
    blocks = bt.load_module(bt.RESOLVER)
    context = ct.load_module(ROOT)
    catalog = blocks.load_json(bt.CATALOG)
    write, write_json = ct.write, ct.write_json
    with tempfile.TemporaryDirectory(prefix="program-kit-placement-") as temporary:
        root = Path(temporary)
        intake = {"routing": {"capabilities": ["authenticated-browser-bff", "forms", "localization"]}}
        installed = root / ".specify/extensions/program-kit-building-blocks"
        shutil.copytree(ROOT / "extensions/program-kit-building-blocks", installed)
        contract = context.building_block_stage_contract(root, intake)
        assert len(contract["target_inventory"]["candidates"]) == 1
        assert contract["target_inventory"]["candidates"][0]["origin"] == "convention"
        assert contract["placement_planning"]["missing_observed_kinds"] == ["cshell-shell", "dotnet-project", "npm-package"]
        context_error(context, "before dispatch", lambda: context.validate_placement_handoff(
            contract["target_inventory"], contract["composition_contracts"], {}))
        selection_path = root / "docs/architecture/building-block-selection.json"
        blocks.draft_selection(root, selection_path, catalog, contract["capabilities"])
        selection = blocks.load_json(selection_path)
        selection["authority"] = {"architectureMap": "docs/architecture/architecture-map.json",
                                  "decisionIds": ["placement"], "rationale": "Owned application boundary."}
        selection["scopes"] = [
            {"id": "app", "kind": "application", "environment": "test"},
            {"id": "browser", "kind": "browser-boundary", "parent": "app", "environment": "test"},
        ]
        selection["targets"] = [
            {"id": "dotnet", "kind": "dotnet-project", "path": "src/Pricing/Pricing.csproj", "role": "implementation", "scope": "browser"},
            {"id": "frontend", "kind": "npm-package", "path": "web/pricing/package.json", "role": "frontend-runtime", "scope": "browser"},
            {"id": "shell", "kind": "cshell-shell", "path": "shells.json", "role": "composition", "scope": "browser", "shell": "pricing"},
        ]
        for target in selection["targets"]:
            target["placement"] = {"state": "planned", "owner": "pricing", "decisionIds": ["placement"],
                                   "rationale": "Pricing capability and browser boundary; synthetic fixture only."}
        selection["instances"] = [
            {"id": key, "composition": key, "scope": "browser", "targetBindings": {slot: slot for slot in value["target_slots"]},
             "options": {"renderer": ["react"]} if key == "forms_runtime" else {}}
            for key, value in contract["composition_contracts"].items()
        ]
        adr = root / "docs/architecture/decisions/placement.md"
        write(adr, "# Placement\n\nStatus: Proposed\n\nPricing owns API, frontend and shell placements.\n")
        architecture_path = root / selection["authority"]["architectureMap"]
        architecture = {"elements": [{"id": "pricing", "ownership": "Pricing team", "decision_refs": ["placement"]}],
                        "decisions": [{"id": "placement", "path": adr.relative_to(root).as_posix(),
                                       "sha256": blocks.raw_sha256(adr), "status": "Proposed"}], "documentation": []}
        write_json(architecture_path, architecture)

        def resolve(value=selection):
            write_json(selection_path, value)
            lock = blocks.resolve(root, selection_path, bt.CATALOG, "0.10.0", require_accepted=False)
            blocks.validate_placements(root, value, require_all=True)
            return lock

        before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        lock = resolve()
        assert lock["managedOutputs"]
        assert not any((root / target["path"]).exists() for target in selection["targets"])
        assert all((root / path).read_bytes() == data for path, data in before.items() if path != selection_path.relative_to(root))
        cli = subprocess.run([sys.executable, str(installed / "scripts/building_blocks.py"), "validate-draft",
                              "--target", str(root), "--require-placement-provenance"], capture_output=True, text=True)
        assert cli.returncode == 0, cli.stderr

        def invalid(change, code):
            value = copy.deepcopy(selection)
            change(value)
            bt.expect_error(blocks, code, lambda: resolve(value))

        invalid(lambda s: s["targets"][0].pop("placement"), "PKB306")
        invalid(lambda s: s["targets"][0]["placement"].update(owner="absent"), "PKB306")
        invalid(lambda s: s["targets"][0]["placement"].update(decisionIds=["absent"]), "PKB306")
        invalid(lambda s: s["targets"][0]["placement"].update(state="observed"), "PKB306")
        invalid(lambda s: s["targets"][0].update(role="frontend-runtime"), "PKB303")
        invalid(lambda s: s["targets"][0].update(kind="npm-package"), "PKB303")
        invalid(lambda s: s["targets"][0].update(scope="absent"), "PKB300")
        invalid(lambda s: s["targets"][0].update(scope="app"), "PKB303")
        invalid(lambda s: s["targets"][2].pop("shell"), "PKB102")
        invalid(lambda s: s["instances"].clear(), "PKB306")
        invalid(lambda s: s["instances"][0]["targetBindings"].pop("dotnet"), "PKB302")
        invalid(lambda s: next(i for i in s["instances"] if i["composition"] == "forms_runtime")["options"].update(renderer=["blazor"]), "PKB203")
        for path in ("../outside.csproj", "C:/outside.csproj", "src/NUL.csproj", "src/bad./bad.csproj", ".specify/fake.csproj"):
            invalid(lambda s, path=path: s["targets"][0].update(path=path), "PKB300")
        invalid(lambda s: s["targets"].append({**copy.deepcopy(s["targets"][0]), "id": "collision", "path": "SRC/PRICING/PRICING.CSPROJ"}), "PKB301")
        original_adr = adr.read_bytes()
        write(adr, "Changed decision without refreshing provenance\n")
        bt.expect_error(blocks, "PKB306", resolve)
        adr.write_bytes(original_adr)

        # Approval remains separate; even an approved plan cannot apply missing manifests.
        resolve()
        bt.expect_error(blocks, "PKB110", lambda: blocks.resolve(root, selection_path, bt.CATALOG, "0.10.0"))
        architecture["decisions"][0]["status"] = "Accepted"
        write(adr, adr.read_text().replace("Status: Proposed", "Status: Accepted"))
        architecture["decisions"][0]["sha256"] = blocks.raw_sha256(adr)
        write_json(architecture_path, architecture)
        accepted_lock = blocks.accept_selection(root, selection_path, bt.CATALOG,
            selection["authority"]["architectureMap"], ["placement"], "Reviewed synthetic placement", "0.10.0")
        assert blocks.load_json(selection_path)["status"] == "Accepted"
        bt.expect_error(blocks, "PKB404", lambda: blocks.apply_materialization(root, root / ".program-kit/building-blocks.lock.json", accepted_lock, catalog))
        assert not any((root / target["path"]).exists() for target in selection["targets"])
        for output in accepted_lock["managedOutputs"]:
            if output["kind"] in {"nuget-project", "npm-package"}:
                bt.expect_error(blocks, "PKB404", lambda output=output: blocks.reconcile_output(root, None, output))

        # A mixed repository preserves observed casing and owner declarations.
        project = root / selection["targets"][0]["path"]
        write(project, '<Project Sdk="Microsoft.NET.Sdk" />\n')
        mixed = copy.deepcopy(selection)
        mixed["targets"][0]["placement"]["state"] = "observed"
        resolve(mixed)
        assert project.read_text() == '<Project Sdk="Microsoft.NET.Sdk" />\n'
        assert next(t for t in context.building_block_target_inventory(root)["candidates"] if t["path"] == selection["targets"][0]["path"])["origin"] == "observed"
        invalid(lambda s: s["targets"][0].update(path="src/pricing/Pricing.csproj"), "PKB301")

    with tempfile.TemporaryDirectory(prefix="program-kit-recovery-") as temporary:
        root = Path(temporary)
        run_id = "bd6be6ca"
        ct.seed_project(root, context, semantic, run_id)
        (root / ".specify/governance/bootstrap-approval.json").unlink(missing_ok=True)
        for relative in ("Directory.Build.props", "src/Price.Api/Price.Api.csproj", "web/package.json"):
            (root / relative).unlink()
        run = context.safe_run_directory(root, run_id)
        state = {"run_id": run_id, "workflow_id": "program-kit-bootstrap", "status": "failed",
                 "current_step_id": "validate-architecture-output", "current_step_index": 20}
        write_json(run / "state.json", state)
        write(run / "workflow.yml", "# Preserved snapshot; recovery must not rewrite it.\n")
        for stage in ("architecture", "research"):
            _, brief = context.build_context(root, run_id, stage)
            assert "<workflow-run-id>" not in json.dumps(brief)
            assert run_id in brief["stage_plan"]["terminal_condition"]["command"]
            assert brief["stage_plan"]["building_blocks"]["composition_contracts"]["forms_runtime"]["option_groups"][0]["options"] == ["angular", "react", "vue"]
        original_inputs = (run / "inputs.json").read_bytes()
        workflow_checks(root, context, run_id)
        # The reduced workflow has no inputs; restore this test fixture's confirmed intake
        # binding before testing recovery. Production recovery never edits it.
        (run / "inputs.json").write_bytes(original_inputs)
        (root / "docs/architecture/README.md").unlink(missing_ok=True)
        context_error(context, "Renderer compatibility unresolved", lambda: context.validate_stage_output(root, "architecture"))
        context_error(context, "Renderer compatibility unresolved", lambda: context.validate_stage_batch(root, run_id, "architecture"))
        protected = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()
                     and (path.name in {"state.json", "inputs.json", "workflow.yml", "bootstrap-intake.json", "bootstrap-decisions.json"}
                          or "approval" in path.name or "constitution" in path.name)}
        result = context.prepare_architecture_recovery(root, run_id)
        assert result["resume_after_validation"] == "specify workflow resume bd6be6ca"
        assert all(path.read_bytes() == data for path, data in protected.items())
        assert list((run / "program-kit-context").glob("architecture.blocked-*.json"))
        assert not (root / context.ARCHITECTURE_BLOCKED).exists()
        for record in result["preserved"]:
            assert context.sha256_file(root / record["preserved_path"]) == record["sha256"]
        assert not any(root.rglob("*.csproj"))
        state["status"] = "completed"
        write_json(run / "state.json", state)
        context_error(context, "failed bootstrap", lambda: context.prepare_architecture_recovery(root, run_id))
    print("Greenfield/mixed placement, provenance, managed options, blocked diagnostics and recovery preservation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
