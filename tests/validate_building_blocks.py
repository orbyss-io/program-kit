from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "extensions/program-kit-building-blocks"
CATALOG = EXTENSION / "references/orbyss-building-blocks.json"
RESOLVER = EXTENSION / "scripts/building_blocks.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("program_kit_building_blocks", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def expect_error(module, code: str, action) -> None:
    try:
        action()
    except module.ResolverError as error:
        if error.code != code:
            raise AssertionError(f"Expected {code}, found {error}") from error
        return
    raise AssertionError(f"Expected {code}")


def refresh_registration(selection_path: Path, architecture_path: Path) -> None:
    architecture = json.loads(architecture_path.read_text(encoding="utf-8"))
    architecture["documentation"][0]["sha256"] = hashlib.sha256(selection_path.read_bytes()).hexdigest()
    write_json(architecture_path, architecture)


def accepted_fixture(module, root: Path, catalog: dict, composition: str = "domain_events") -> tuple[Path, Path]:
    selection_path = root / "docs/architecture/building-block-selection.json"
    architecture_path = root / "docs/architecture/architecture-map.json"
    selection = {
        "$schema": ".specify/extensions/program-kit-building-blocks/references/building-block-selection.schema.json",
        "schemaVersion": "1.0",
        "selectionId": "test-building-blocks",
        "revision": 1,
        "status": "Accepted",
        "catalog": {
            "id": catalog["catalogId"],
            "schemaVersion": catalog["schemaVersion"],
            "resolutionRevision": catalog["resolutionRevision"],
            "resolutionSha256": module.catalog_resolution_sha256(catalog),
            "familyReleases": {
                name: family["releaseVersion"] for name, family in sorted(catalog["families"].items())
            },
        },
        "authority": {
            "architectureMap": "docs/architecture/architecture-map.json",
            "decisionIds": ["use-building-blocks"],
            "rationale": "Exercise deterministic accepted selection resolution.",
        },
        "scopes": [{"id": "application", "kind": "application", "environment": "production"}],
        "targets": [
            {
                "id": "feature",
                "kind": "dotnet-project",
                "path": "src/Test.Feature/Test.Feature.csproj",
                "role": "implementation",
                "scope": "application",
            },
            {
                "id": "shell",
                "kind": "cshell-shell",
                "path": "shells.json",
                "role": "composition",
                "scope": "application",
                "shell": "default",
            },
        ],
        "instances": [
            {
                "id": "domain-events",
                "composition": composition,
                "scope": "application",
                "targetBindings": {
                    **({"dotnet": "feature"} if "dotnet" in catalog["compositions"][composition]["targetSlots"] else {}),
                    **({"shell": "shell"} if "shell" in catalog["compositions"][composition]["targetSlots"] else {}),
                },
                "options": {},
            }
        ],
    }
    write_json(selection_path, selection)
    project = root / "src/Test.Feature/Test.Feature.csproj"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        '  <PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup>\n'
        '  <ItemGroup><PackageReference Include="Consumer.Owned" /></ItemGroup>\n'
        '</Project>\n',
        encoding="utf-8",
        newline="\n",
    )
    digest = hashlib.sha256(selection_path.read_bytes()).hexdigest()
    write_json(
        architecture_path,
        {
            "documentation": [
                {
                    "id": "building-block-selection",
                    "path": "docs/architecture/building-block-selection.json",
                    "sha256": digest,
                    "scope": "Accepted building-block selection",
                }
            ],
            "decisions": [{"id": "use-building-blocks", "status": "Accepted"}],
        },
    )
    return selection_path, architecture_path


def main() -> int:
    module = load_module(RESOLVER)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    module.validate_catalog(catalog)
    if catalog["schemaVersion"] != "1.0" or catalog["resolutionRevision"] != 1:
        raise AssertionError("Executable catalog must begin at schema 1.0 and resolution revision 1")
    ecosystems = [package["ecosystem"] for package in catalog["packages"].values()]
    if ecosystems.count("nuget") != 50 or ecosystems.count("npm") != 12 or ecosystems.count("oci") != 1:
        raise AssertionError("Catalog must contain 50 NuGet, 12 npm, and one Foundation host artifact")
    if len(catalog["compositions"]) != 16:
        raise AssertionError("Catalog must preserve all 16 current compositions")
    if any(not package.get("version") for package in catalog["packages"].values()):
        raise AssertionError("Every artifact must have an explicit exact version")
    configuration = [
        item
        for composition in catalog["compositions"].values()
        for item in composition["configuration"]
    ] + [
        item
        for package in catalog["packages"].values()
        for item in package["configuration"]
    ]
    if not any(item["required"] for item in configuration):
        raise AssertionError("Catalog lost required configuration knowledge")
    if not any(not item["required"] and "default" in item for item in configuration):
        raise AssertionError("Catalog lost optional configuration keys and defaults")
    resolution_hash = module.catalog_resolution_sha256(catalog)
    if resolution_hash != module.catalog_resolution_sha256(copy.deepcopy(catalog)):
        raise AssertionError("Catalog resolution hashing is not deterministic")
    prose_change = copy.deepcopy(catalog)
    prose_change["policy"]["compatibility"] += " Prose-only clarification."
    prose_change["packages"]["nuget:Orbyss.Foundation.Tasks"]["role"] += " Prose-only clarification."
    if module.catalog_resolution_sha256(prose_change) != resolution_hash:
        raise AssertionError("Prose-only catalog changes altered the executable resolution hash")
    version_change = copy.deepcopy(catalog)
    version_change["packages"]["nuget:Orbyss.Foundation.Tasks"]["version"] = "0.1.1"
    if module.catalog_resolution_sha256(version_change) == resolution_hash:
        raise AssertionError("Package version changes did not alter the executable resolution hash")

    with tempfile.TemporaryDirectory(prefix="program-kit-building-blocks-") as value:
        repository = Path(value)
        selection_path, _ = accepted_fixture(module, repository, catalog)
        first = module.resolve(repository, selection_path, CATALOG, "0.10.0")
        second = module.resolve(repository, selection_path, CATALOG, "0.10.0")
        if first != second or module.pretty_json(first) != module.pretty_json(second):
            raise AssertionError("Identical accepted inputs did not produce a byte-stable lock")
        packages = {
            package["packageId"]
            for target in first["targets"]
            for package in target["packages"]
        }
        if packages != {"Orbyss.Foundation.DomainEvents", "Orbyss.Foundation.DomainEvents.Abstractions"}:
            raise AssertionError(f"Domain-events closure is incorrect: {sorted(packages)}")
        if [item["featureIdentity"] for item in first["activations"]] != ["Orbyss.Foundation.DomainEvents"]:
            raise AssertionError("Domain-events activation was not derived")
        output_kinds = {item["kind"] for item in first["managedOutputs"]}
        if output_kinds != {"nuget-central-pins", "nuget-project", "cshell-activations"}:
            raise AssertionError(f"Domain-events materialization plan is incomplete: {sorted(output_kinds)}")
        original_selection = json.loads(selection_path.read_text(encoding="utf-8"))
        multi_shell = copy.deepcopy(original_selection)
        multi_shell["targets"].append(
            {
                "id": "secondary-shell",
                "kind": "cshell-shell",
                "path": "apps/secondary/shells.json",
                "role": "composition",
                "scope": "application",
                "shell": "default",
            }
        )
        multi_shell["instances"][0]["targetBindings"]["shell"] = ["shell", "secondary-shell"]
        write_json(selection_path, multi_shell)
        refresh_registration(selection_path, repository / "docs/architecture/architecture-map.json")
        multi_plan = module.resolve(repository, selection_path, CATALOG, "0.10.0")
        activation_paths = {
            output["path"]
            for output in multi_plan["managedOutputs"]
            if output["kind"] == "cshell-activations"
        }
        if activation_paths != {
            ".program-kit/building-blocks.shells.json",
            "apps/secondary/.program-kit/building-blocks.shells.json",
        }:
            raise AssertionError(f"Shell activations were not materialized beside exact shell targets: {activation_paths}")
        write_json(selection_path, original_selection)
        refresh_registration(selection_path, repository / "docs/architecture/architecture-map.json")
        first = module.resolve(repository, selection_path, CATALOG, "0.10.0")
        lock_path = repository / ".program-kit/building-blocks.lock.json"
        module.apply_materialization(repository, lock_path, first, catalog)
        module.check_materialization(repository, first)
        project_text = (repository / "src/Test.Feature/Test.Feature.csproj").read_text(encoding="utf-8")
        if "Consumer.Owned" not in project_text or project_text.count("ProgramKit.BuildingBlocks") != 1:
            raise AssertionError("Entry-level NuGet reconciliation did not preserve consumer-owned state")
        first_bytes = {
            output["path"]: (repository / output["path"]).read_bytes()
            for output in first["managedOutputs"]
        }
        module.apply_materialization(repository, lock_path, first, catalog)
        if first_bytes != {
            output["path"]: (repository / output["path"]).read_bytes()
            for output in first["managedOutputs"]
        }:
            raise AssertionError("Repeated materialization was not byte-stable")
        os.environ["PROGRAMKIT_TEST_BUILDING_BLOCK_FAIL_AFTER_ACTION"] = "1"
        try:
            try:
                module.apply_materialization(repository, lock_path, first, catalog)
            except OSError:
                pass
            else:
                raise AssertionError("Injected materialization failure did not interrupt the transaction")
        finally:
            os.environ.pop("PROGRAMKIT_TEST_BUILDING_BLOCK_FAIL_AFTER_ACTION", None)
        module.check_materialization(repository, first)
        if module.recover_materialization(repository):
            raise AssertionError("Failed transaction did not roll back and clean its journal")
        project_path = repository / "src/Test.Feature/Test.Feature.csproj"
        project_path.write_text(project_text.replace("Orbyss.Foundation.DomainEvents\"", "Orbyss.Foundation.Tasks\""), encoding="utf-8")
        expect_error(module, "PKB403", lambda: module.check_materialization(repository, first))
        project_path.write_text(project_text, encoding="utf-8", newline="\n")

        stale = json.loads(selection_path.read_text(encoding="utf-8"))
        stale["authority"]["rationale"] += " Changed after acceptance."
        write_json(selection_path, stale)
        expect_error(module, "PKB112", lambda: module.resolve(repository, selection_path, CATALOG, "0.10.0"))

        selection_path, _ = accepted_fixture(module, repository, catalog, "forms_runtime")
        expect_error(module, "PKB204", lambda: module.resolve(repository, selection_path, CATALOG, "0.10.0"))

        npm_repository = repository / "npm-consumer"
        selection_path, architecture_path = accepted_fixture(module, npm_repository, catalog, "forms_runtime")
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        selection["targets"].append(
            {
                "id": "frontend",
                "kind": "npm-package",
                "path": "web/package.json",
                "role": "frontend-runtime",
                "scope": "application",
            }
        )
        selection["instances"][0]["targetBindings"]["frontend"] = "frontend"
        selection["instances"][0]["options"] = {"renderer": ["react"], "extensions": []}
        write_json(selection_path, selection)
        refresh_registration(selection_path, architecture_path)
        write_json(
            npm_repository / "web/package.json",
            {"name": "consumer-web", "private": True, "dependencies": {"consumer-owned": "1.2.3"}},
        )
        npm_lock = module.resolve(npm_repository, selection_path, CATALOG, "0.10.0")
        npm_lock_path = npm_repository / ".program-kit/building-blocks.lock.json"
        module.apply_materialization(npm_repository, npm_lock_path, npm_lock, catalog)
        package_json = json.loads((npm_repository / "web/package.json").read_text(encoding="utf-8"))
        if package_json["dependencies"].get("consumer-owned") != "1.2.3":
            raise AssertionError("npm reconciliation overwrote a consumer-owned dependency")
        if not any(key.startswith("@orbyss-io/forms-") for key in package_json["dependencies"]):
            raise AssertionError("npm materialization omitted the exact visible Forms dependencies")
        npmrc = (npm_repository / "web/.npmrc").read_text(encoding="utf-8")
        if "${PROGRAM_KIT_NPM_TOKEN}" not in npmrc or "npm.pkg.github.com" not in npmrc:
            raise AssertionError("npm materialization did not emit environment-only GitHub registry routing")
        package_json["dependencies"]["@orbyss-io/forms-vue"] = "0.1.1"
        write_json(npm_repository / "web/package.json", package_json)
        expect_error(
            module,
            "PKB405",
            lambda: module.audit_unmanaged_dependencies(npm_repository, catalog, npm_lock),
        )

        tool_repository = repository / "tool-consumer"
        selection_path, architecture_path = accepted_fixture(module, tool_repository, catalog, "openapi_export")
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        selection["targets"].append(
            {
                "id": "tools",
                "kind": "dotnet-tool-manifest",
                "path": ".config/dotnet-tools.json",
                "role": "tooling",
                "scope": "application",
            }
        )
        selection["instances"][0]["targetBindings"]["tools"] = "tools"
        write_json(selection_path, selection)
        refresh_registration(selection_path, architecture_path)
        write_json(
            tool_repository / ".config/dotnet-tools.json",
            {"version": 1, "isRoot": True, "tools": {"consumer.tool": {"version": "2.0.0", "commands": ["consumer"]}}},
        )
        tool_lock = module.resolve(tool_repository, selection_path, CATALOG, "0.10.0")
        module.apply_materialization(tool_repository, tool_repository / ".program-kit/building-blocks.lock.json", tool_lock, catalog)
        tools = json.loads((tool_repository / ".config/dotnet-tools.json").read_text(encoding="utf-8"))["tools"]
        if "consumer.tool" not in tools or tools.get("orbyss.foundation.openapi.exporter", {}).get("commands") != [
            "orbyss-foundation-openapi-export"
        ]:
            raise AssertionError("dotnet tool materialization did not preserve consumer tools and exact commands")

        acceptance_repository = repository / "acceptance-consumer"
        selection_path, architecture_path = accepted_fixture(module, acceptance_repository, catalog)
        draft = json.loads(selection_path.read_text(encoding="utf-8"))
        draft["status"] = "Draft"
        draft["draftSuggestions"] = [
            {"capability": "domain-events", "compositions": ["domain_events"]}
        ]
        write_json(selection_path, draft)
        accepted_plan = module.accept_selection(
            acceptance_repository,
            selection_path,
            CATALOG,
            "docs/architecture/architecture-map.json",
            ["use-building-blocks"],
            "Accept the exact domain-events closure and project assignment.",
            "0.10.0",
        )
        accepted = json.loads(selection_path.read_text(encoding="utf-8"))
        registered = json.loads(architecture_path.read_text(encoding="utf-8"))["documentation"][0]
        if accepted["status"] != "Accepted" or "draftSuggestions" in accepted:
            raise AssertionError("Acceptance did not complete the Draft lifecycle")
        if registered.get("canonicalSha256") != module.canonical_sha256(accepted):
            raise AssertionError("Acceptance did not bind canonical consumer architecture content")
        if accepted_plan != module.resolve(acceptance_repository, selection_path, CATALOG, "0.10.0"):
            raise AssertionError("Accepted lifecycle output did not resolve deterministically")

        host_repository = repository / "host-consumer"
        selection_path, architecture_path = accepted_fixture(module, host_repository, catalog, "api_baseline")
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        selection["scopes"].insert(0, {"id": "repository", "kind": "repository", "environment": "production"})
        selection["scopes"][1]["parent"] = "repository"
        selection["targets"].extend(
            [
                {"id": "repository-policy", "kind": "repository", "path": "Directory.Build.props", "role": "repository", "scope": "repository"},
                {"id": "host", "kind": "host-image", "path": "Dockerfile", "role": "runtime-host", "scope": "application"},
            ]
        )
        selection["instances"][0]["targetBindings"].update({"repository": "repository-policy", "host": "host"})
        selection["instances"][0]["options"] = {"host": ["foundation-host"]}
        write_json(selection_path, selection)
        refresh_registration(selection_path, architecture_path)
        host_lock = module.resolve(host_repository, selection_path, CATALOG, "0.10.0")
        host_output = next(item for item in host_lock["managedOutputs"] if item["kind"] == "host-images")
        if host_output["entries"][0]["reference"] != "ghcr.io/orbyss-io/foundation-host:v0.1.0":
            raise AssertionError("Foundation host selection did not materialize the exact version tag")

    print("Executable catalog, authority binding, deterministic lock, and cross-ecosystem materialization passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
