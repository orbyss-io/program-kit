from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


def load_module(root: Path):
    path = root / "extensions/program-kit-governance/scripts/bootstrap_context.py"
    spec = importlib.util.spec_from_file_location("bootstrap_context", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value: dict) -> None:
    write(path, json.dumps(value, indent=2) + "\n")


def seed_project(project: Path, module, run_id: str) -> None:
    run = project / ".specify/workflows/runs" / run_id
    write(project / "INITIAL_DESIGN.md", "# Tiny application\n\nA visitor sees a greeting.\n")
    write_json(run / "inputs.json", {"inputs": {"initial_design": "./INITIAL_DESIGN.md"}})
    write_json(
        project / module.BRIEF_PATH,
        {
            "schema_version": "1.0",
            "source": {
                "path": "INITIAL_DESIGN.md",
                "sha256": module.sha256_file(project / "INITIAL_DESIGN.md"),
            },
            "project": {"name": "Tiny application", "summary": "A visitor sees a greeting."},
            "facts": [
                {"id": "greeting", "statement": "The application shows a greeting.", "evidence": "INITIAL_DESIGN.md:3"}
            ],
            "explicit_boundaries": [],
            "actors": [
                {"id": "visitor", "statement": "A visitor uses the application.", "evidence": "INITIAL_DESIGN.md:3"}
            ],
            "journeys": [
                {"id": "see-greeting", "statement": "A visitor sees a greeting.", "evidence": "INITIAL_DESIGN.md:3"}
            ],
            "quality_requirements": [],
            "ambiguities": [],
            "routing": {
                "languages": [],
                "frameworks": [],
                "interfaces": [],
                "included_surfaces": ["greeting"],
                "excluded_surfaces": [],
            },
        },
    )
    markdown = {
        ".specify/memory/constitution.md": "# Constitution\n\n**Status**: Ratified\n",
        "docs/architecture/bootstrap-assessment.md": "# Assessment\n\n## Actors\n\n- **Visitor** sees a greeting.\n",
        "docs/architecture/decision-backlog.md": "# Backlog\n\n## ADR-001\n\n**Status**: Deferred\n",
        "docs/architecture/tooling-evaluation.md": "# Tooling\n\n## Quality\n\n- **Decision**: built-in checks.\n",
        "docs/architecture/architecture.md": "# Architecture\n\n## Candidate slices\n\n- **SPC-001** greeting.\n",
        "docs/architecture/quality-attributes.md": "# Quality attributes\n\n## QA-001\n\n**Status**: Ready\n",
        "docs/architecture/quality-system.md": "# Quality system\n\n## Bootstrap gates\n",
        "docs/architecture/technology-radar.md": "# Technology radar\n\n## Accepted\n",
        "docs/architecture/traceability.md": "# Traceability\n\n| Design | SPC-001 |\n| --- | --- |\n",
        "docs/architecture/specification-roadmap.md": "# Roadmap\n\n### SPC-001: Greeting\n\n**Status**: Ready\n",
        "docs/architecture/decisions/bootstrap-baseline.md": "# Bootstrap baseline\n\n**Status**: Accepted\n",
        "docs/architecture/decisions/ADR-001.md": "# ADR-001: Boundary\n\n**Status**: Proposed\n",
    }
    for relative, text in markdown.items():
        write(project / relative, text)
    json_files = {
        "docs/architecture/bootstrap-decisions.json": {
            "schema_version": "1.0",
            "choices": [{"id": "greeting", "decision": "Static greeting"}],
        },
        ".specify/governance/bootstrap-assessment-approval.json": {"status": "Approved"},
        ".specify/memory/constitution-ratification.json": {"status": "Ratified"},
        ".specify/governance/bootstrap-approval.json": {"status": "Approved"},
    }
    for relative, value in json_files.items():
        write_json(project / relative, value)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    module = load_module(root)
    with tempfile.TemporaryDirectory(prefix="program-kit-context-test-") as directory:
        project = Path(directory)
        run_id = "context-test-1"
        seed_project(project, module, run_id)
        module.validate_brief(project, run_id)

        for stage in module.STAGE_ARTIFACTS:
            path, payload = module.build_context(project, run_id, stage)
            if not path.is_file() or payload["stage"] != stage:
                raise AssertionError(f"{stage} context was not written")
            if payload["initial_design"]["path"] != "INITIAL_DESIGN.md":
                raise AssertionError("Initial-design provenance is not project-relative")
            if payload["reading_policy"]["mode"] != "deny-by-default":
                raise AssertionError(f"{stage} context does not enforce deny-by-default reading")
            if "artifacts" in payload:
                raise AssertionError(f"{stage} stage brief embeds the evidence index")
            output_contract = payload["output_contract"]
            for artifact, budget in output_contract["artifact_byte_budgets"].items():
                if artifact not in output_contract["write_paths"] or budget <= 0:
                    raise AssertionError(
                        f"{stage} output contract contains an invalid artifact budget"
                    )
            evidence_path = project / payload["evidence_index"]["path"]
            if not evidence_path.is_file():
                raise AssertionError(f"{stage} evidence index was not written")
            module.validate_context(project, run_id, stage)

        roadmap_path = (
            project
            / ".specify/workflows/runs"
            / run_id
            / "program-kit-context/roadmap.json"
        )
        roadmap = json.loads(roadmap_path.read_text(encoding="utf-8"))
        if roadmap["authorities"]["assessment_approval"]["status"] != "Approved":
            raise AssertionError("Approved authority was not included in context")
        adr = next(item for item in roadmap["decisions"] if item["path"].endswith("ADR-001.md"))
        if adr["status"] != "Proposed":
            raise AssertionError("ADR status was not indexed")
        if roadmap_path.stat().st_size >= (
            project / roadmap["evidence_index"]["path"]
        ).stat().st_size:
            raise AssertionError("Compact stage brief is not smaller than its evidence index")
        roadmap_budget = roadmap["output_contract"]["artifact_byte_budgets"].get(
            "docs/architecture/architecture.md"
        )
        if roadmap_budget != 12 * 1024:
            raise AssertionError("Roadmap did not inherit the final architecture byte budget")

        original = roadmap_path.read_bytes()
        write(
            project / "docs/architecture/quality-system.md",
            "# Quality system\n\n## Changed after context generation\n",
        )
        try:
            module.validate_context(project, run_id, "roadmap")
        except module.ContextError as exc:
            if "stale or invalid" not in str(exc):
                raise
        else:
            raise AssertionError("Context validation accepted a changed source")
        if roadmap_path.read_bytes() != original:
            raise AssertionError("Read-only context validation rewrote the stored context")

        local_config = (
            project
            / ".specify/extensions/program-kit-governance/program-kit-governance-config.local.yml"
        )
        write(
            local_config,
            """architecture:
  decisions: "governance/decisions"
  specification_roadmap: "governance/roadmap.md"
constitution:
  document: "governance/constitution.md"
  ratification: "governance/ratification.json"
""",
        )
        for source, destination in (
            ("docs/architecture/specification-roadmap.md", "governance/roadmap.md"),
            (".specify/memory/constitution.md", "governance/constitution.md"),
            (".specify/memory/constitution-ratification.json", "governance/ratification.json"),
            ("docs/architecture/decisions/bootstrap-baseline.md", "governance/decisions/bootstrap-baseline.md"),
            ("docs/architecture/decisions/ADR-001.md", "governance/decisions/ADR-001.md"),
        ):
            write(project / destination, (project / source).read_text(encoding="utf-8"))
        _, configured = module.build_context(project, run_id, "readiness")
        if configured["governance"]["paths"]["decisions"] != "governance/decisions":
            raise AssertionError("Compact context ignored the configured decisions path")
        if configured["reading_policy"]["required_full_reads"] != ["governance/constitution.md"]:
            raise AssertionError("Compact context ignored the configured constitution path")
        configured_evidence = json.loads(
            (project / configured["evidence_index"]["path"]).read_text(encoding="utf-8")
        )
        configured_paths = {item["path"] for item in configured_evidence["artifacts"]}
        if not {
            "governance/roadmap.md",
            "governance/constitution.md",
            "governance/ratification.json",
            "governance/decisions/bootstrap-baseline.md",
        }.issubset(configured_paths):
            raise AssertionError(f"Configured governance evidence is incomplete: {configured_paths}")
        module.validate_context(project, run_id, "readiness")

        try:
            module.safe_run_directory(project, "../escape")
        except module.ContextError:
            pass
        else:
            raise AssertionError("Unsafe workflow run ID was accepted")

    print("Bootstrap context generation and staleness checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
