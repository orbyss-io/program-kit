from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import yaml


ROOT = Path(__file__).resolve().parents[1]


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def validate_hooks() -> None:
    manifest = yaml.safe_load(
        (ROOT / "extensions/program-kit-governance/extension.yml").read_text(encoding="utf-8")
    )
    expected = {
        "after_specify": ["speckit.clarify", "speckit.program-kit-governance.architecture-check"],
        "after_tasks": ["speckit.analyze", "speckit.program-kit-governance.architecture-check"],
    }
    for event, commands in expected.items():
        entries = manifest["hooks"][event]
        if [entry["command"] for entry in entries] != commands:
            raise AssertionError(f"{event} hook ordering is invalid")
        if [entry["priority"] for entry in entries] != [5, 10]:
            raise AssertionError(f"{event} priorities are invalid")
        for entry in entries:
            if entry.get("enabled") is not True or entry.get("optional") is not False or entry.get("condition", "missing") is not None:
                raise AssertionError(f"{event} hook is not unconditionally mandatory: {entry}")


def validate_lifecycle() -> None:
    lifecycle = module(
        ROOT / "extensions/program-kit-governance/scripts/lifecycle_state.py", "lifecycle_state"
    )
    with tempfile.TemporaryDirectory(prefix="program-kit-lifecycle-") as value:
        repository = Path(value)
        feature = repository / "specs/SPC-001"
        feature.mkdir(parents=True)
        for name in lifecycle.ARTIFACTS:
            (feature / name).write_text(f"# {name}\nUnicode ✓\n", encoding="utf-8")
        if lifecycle.begin(repository, feature, "clarify", False) != 0:
            raise AssertionError("clarification did not start")
        if lifecycle.begin(repository, feature, "clarify", False) != 4:
            raise AssertionError("reentrant clarification was not rejected")
        if lifecycle.begin(repository, feature, "clarify", True) != 0:
            raise AssertionError("interrupted clarification did not resume")
        if lifecycle.complete_clarify(repository, feature, "no-questions") != 0:
            raise AssertionError("no-question clarification did not complete")

        report = repository / ".program-kit/evidence/after-tasks-analysis.md"
        report.parent.mkdir(parents=True)
        report.write_text("# Analysis\nNo blocking findings.\n", encoding="utf-8")
        if lifecycle.begin(repository, feature, "analyze", False) != 0:
            raise AssertionError("analysis did not start")
        if lifecycle.complete_analysis(repository, feature, report) != 0:
            raise AssertionError("clean analysis did not complete")
        if lifecycle.verify_before_implement(repository, feature) != 0:
            raise AssertionError("current analysis did not authorize implementation")
        (feature / "tasks.md").write_text("changed\n", encoding="utf-8")
        if lifecycle.verify_before_implement(repository, feature) != 12:
            raise AssertionError("stale analysis was not rejected")

        blocked = repository / "specs/SPC-002"
        blocked.mkdir()
        for name in lifecycle.ARTIFACTS:
            (blocked / name).write_text(f"# {name}\n", encoding="utf-8")
        blocking_report = repository / ".program-kit/evidence/SPC-002-analysis.md"
        blocking_report.write_text("| Severity | Finding |\n| HIGH | ownership drift |\n", encoding="utf-8")
        lifecycle.begin(repository, blocked, "analyze", False)
        if lifecycle.complete_analysis(repository, blocked, blocking_report) != 9:
            raise AssertionError("HIGH analysis did not block readiness")
        if lifecycle.verify_before_implement(repository, blocked) != 13:
            raise AssertionError("non-ready analysis authorized implementation")


def validate_utf8() -> None:
    ensure = ROOT / "extensions/program-kit-governance/scripts/ensure_utf8.py"
    with tempfile.TemporaryDirectory(prefix="program-kit-utf8-") as value:
        repository = Path(value)
        scripts = repository / ".specify/scripts/python"
        scripts.mkdir(parents=True)
        probe = scripts / "setup_tasks.py"
        probe.write_text("print('Task template → ✓')\n", encoding="utf-8")
        subprocess.run([sys.executable, str(ensure), "--target", str(repository)], check=True)
        environment = os.environ.copy()
        environment["PYTHONUTF8"] = "0"
        environment["PYTHONIOENCODING"] = "cp1252"
        result = subprocess.run([sys.executable, str(probe)], env=environment, capture_output=True)
        if result.returncode != 0 or "Task template → ✓" not in result.stdout.decode("utf-8"):
            raise AssertionError(f"UTF-8 startup failed under cp1252: {result.stderr!r}")
        subprocess.run([sys.executable, str(ensure), "--target", str(repository), "--check"], check=True)


def validate_feature_activation() -> None:
    feature = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/feature_metadata.py"
    with tempfile.TemporaryDirectory(prefix="program-kit-feature-") as value:
        shells = Path(value) / "shells.json"
        shells.write_text(
            json.dumps({"CShells": {"Shells": {"default": {"Features": {"ProgramKitTasks": {}}}}}}),
            encoding="utf-8",
        )
        command = [sys.executable, str(feature), "activate", "--shells", str(shells), "--shell", "default", "--feature", "Orders"]
        subprocess.run(command, check=True)
        duplicate = subprocess.run(command, capture_output=True, text=True)
        if duplicate.returncode == 0 or "PKF006" not in duplicate.stderr:
            raise AssertionError("duplicate feature activation was not rejected")
        result = json.loads(shells.read_text(encoding="utf-8"))
        if set(result["CShells"]["Shells"]["default"]["Features"]) != {"ProgramKitTasks", "Orders"}:
            raise AssertionError("CShells feature activation shape drifted")


def validate_bundle_feature_closure() -> None:
    bundle = module(
        ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/create_application_bundle.py",
        "create_application_bundle",
    )
    with tempfile.TemporaryDirectory(prefix="program-kit-bundle-features-") as value:
        root = Path(value)

        def package(package_id: str, identity: str | None = None, **overrides) -> Path:
            path = root / f"{package_id}.1.0.0.nupkg"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(
                    f"{package_id}.nuspec",
                    f"<package><metadata><id>{package_id}</id><version>1.0.0</version></metadata></package>",
                )
                if identity:
                    descriptor = {
                        "schemaVersion": 1,
                        "identity": identity,
                        "packageId": package_id,
                        "featureDependencies": [],
                        "runtimeDependencies": [],
                        "routes": [],
                        "dormant": False,
                        **overrides,
                    }
                    archive.writestr("program-kit/feature.json", json.dumps(descriptor))
            return path

        tasks = package("ProgramKit.Tasks")
        orders = package("Orders.Feature", "Orders", routes=["/orders"])
        identities = {("ProgramKit.Tasks", "1.0.0"): tasks, ("Orders.Feature", "1.0.0"): orders}
        shells = root / "shells.json"
        shells.write_text(
            json.dumps({"CShells": {"Shells": {"default": {"Features": {"ProgramKitTasks": {}, "Orders": {}}}}}}),
            encoding="utf-8",
        )
        descriptors = bundle.validate_feature_closure(shells, identities)
        if [item["identity"] for item in descriptors] != ["Orders"]:
            raise AssertionError("valid feature closure did not resolve exactly once")

        missing_shells = root / "missing.json"
        missing_shells.write_text(
            json.dumps({"CShells": {"Shells": {"default": {"Features": {"Missing": {}}}}}}),
            encoding="utf-8",
        )
        try:
            bundle.validate_feature_closure(missing_shells, identities)
        except ValueError as error:
            if "PKB009" not in str(error) or "default" not in str(error) or "Missing" not in str(error):
                raise
        else:
            raise AssertionError("missing activated feature did not fail actionably")

        duplicate = package("Orders.Other", "Orders")
        try:
            bundle.validate_feature_closure(shells, {**identities, ("Orders.Other", "1.0.0"): duplicate})
        except ValueError as error:
            if "PKB007" not in str(error):
                raise
        else:
            raise AssertionError("duplicate feature identity was accepted")

        dependent = package(
            "Dependent.Feature", "Dependent", runtimeDependencies=["Missing.Runtime"]
        )
        dependency_shells = root / "dependency.json"
        dependency_shells.write_text(
            json.dumps({"CShells": {"Shells": {"default": {"Features": {"Dependent": {}}}}}}),
            encoding="utf-8",
        )
        try:
            bundle.validate_feature_closure(
                dependency_shells,
                {("Dependent.Feature", "1.0.0"): dependent},
            )
        except ValueError as error:
            if "PKB010" not in str(error) or "Missing.Runtime" not in str(error):
                raise
        else:
            raise AssertionError("missing runtime dependency was accepted")

        payments = package("Payments.Feature", "Payments", routes=["/orders"])
        collision_shells = root / "collision.json"
        collision_shells.write_text(
            json.dumps({"CShells": {"Shells": {"default": {"Features": {"Orders": {}, "Payments": {}}}}}}),
            encoding="utf-8",
        )
        try:
            bundle.validate_feature_closure(
                collision_shells,
                {**identities, ("Payments.Feature", "1.0.0"): payments},
            )
        except ValueError as error:
            if "PKB012" not in str(error):
                raise
        else:
            raise AssertionError("route collision was accepted")


def validate_preflight_seams() -> None:
    preflight = ROOT / "extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/eng/program-kit/preflight.py"
    with tempfile.TemporaryDirectory(prefix="program-kit-preflight-") as value:
        tools = Path(value)
        if os.name == "nt":
            stopped = tools / "docker-stopped.cmd"
            stopped.write_text("@echo off\r\nexit /b 1\r\n", encoding="utf-8")
            slow = tools / "docker-slow.cmd"
            slow.write_text("@echo off\r\nping -n 3 127.0.0.1 >nul\r\necho \"10.0.0\"\r\n", encoding="utf-8")
            ready = tools / "docker-ready.cmd"
            ready.write_text("@echo off\r\necho \"10.0.0\"\r\n", encoding="utf-8")
        else:
            stopped = tools / "docker-stopped"
            stopped.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            slow = tools / "docker-slow"
            slow.write_text("#!/bin/sh\nsleep 2\nprintf '\"10.0.0\"\\n'\n", encoding="utf-8")
            ready = tools / "docker-ready"
            ready.write_text("#!/bin/sh\nprintf '\"10.0.0\"\\n'\n", encoding="utf-8")
            for path in (stopped, slow, ready):
                path.chmod(0o755)

        def run(command: str, timeout: str = "5") -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(preflight), "--docker-command", command, "--timeout-seconds", timeout],
                capture_output=True,
                text=True,
            )

        cases = [
            (run("program-kit-missing-docker"), 2, "PKP002"),
            (run(str(stopped)), 4, "PKP004"),
            (run(str(slow), "0.1"), 3, "PKP003"),
            (run(str(ready), "0"), 1, "PKP001"),
        ]
        for result, code, marker in cases:
            if result.returncode != code or marker not in result.stderr:
                raise AssertionError(f"preflight seam {marker} failed: {result.stdout}{result.stderr}")
        if run(str(ready)).returncode != 0:
            raise AssertionError("ready Docker seam did not pass")


def validate_toolchain_workflow() -> None:
    toolchain = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/toolchain.py"
    with tempfile.TemporaryDirectory(prefix="program-kit-toolchain-") as value:
        repository = Path(value)
        tools = repository / "tools"
        tools.mkdir()
        (repository / "global.json").write_text('{"sdk":{"version":"10.0.202"}}\n', encoding="utf-8")
        (repository / ".nvmrc").write_text("24.20.0\n", encoding="utf-8")
        marker = repository / "dotnet-installed"
        if os.name == "nt":
            dotnet = tools / "dotnet.cmd"
            dotnet.write_text(
                f"@echo off\r\nif exist \"{marker}\" (echo 10.0.202) else (echo 9.0.100)\r\n",
                encoding="utf-8",
            )
            node = tools / "node.cmd"
            node.write_text("@echo off\r\necho v24.20.0\r\n", encoding="utf-8")
            installer = repository / "dotnet-install.cmd"
            installer.write_text(f"@echo off\r\ntype nul > \"{marker}\"\r\n", encoding="utf-8")
            offline = repository / "offline.cmd"
            offline.write_text("@echo off\r\nexit /b 1\r\n", encoding="utf-8")
        else:
            dotnet = tools / "dotnet"
            dotnet.write_text(f"#!/bin/sh\n[ -f '{marker}' ] && echo 10.0.202 || echo 9.0.100\n", encoding="utf-8")
            node = tools / "node"
            node.write_text("#!/bin/sh\necho v24.20.0\n", encoding="utf-8")
            installer = repository / "dotnet-install.sh"
            installer.write_text(f"#!/bin/sh\ntouch '{marker}'\n", encoding="utf-8")
            offline = repository / "offline.sh"
            offline.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            for path in (dotnet, node, installer, offline):
                path.chmod(0o755)
        environment = os.environ.copy()
        environment["PATH"] = str(tools) + os.pathsep + environment.get("PATH", "")

        def run(*arguments: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [
                    sys.executable,
                    str(toolchain),
                    "--repository",
                    str(repository),
                    "--dotnet-command",
                    str(dotnet),
                    "--node-command",
                    str(node),
                    *arguments,
                ],
                # Exact command paths are test seams; production defaults remain dotnet/node from PATH.
                env=environment,
                capture_output=True,
                text=True,
            )

        declined = run("--remediate", "--decline")
        if declined.returncode != 3 or "PKT003" not in declined.stderr:
            raise AssertionError("declined toolchain remediation changed state or returned the wrong code")
        unavailable = run("--remediate", "--approve")
        if unavailable.returncode != 4 or "PKT004" not in unavailable.stderr:
            raise AssertionError(f"unavailable installer path was not actionable: {unavailable.stdout}{unavailable.stderr}")
        offline_result = run("--remediate", "--approve", "--dotnet-installer", str(offline))
        if offline_result.returncode != 4 or "PKT006" not in offline_result.stderr:
            raise AssertionError("offline/failed installer path was not distinguished")
        approved = run("--remediate", "--approve", "--dotnet-installer", str(installer))
        if approved.returncode != 0 or "PKT010" not in approved.stdout:
            raise AssertionError(f"approved remediation did not re-verify: {approved.stdout}{approved.stderr}")
        satisfied = run()
        if satisfied.returncode != 0 or "PKT000" not in satisfied.stdout:
            raise AssertionError("already-satisfied toolchain did not avoid installation")


def validate_managed_sources() -> None:
    template = ROOT / "extensions/program-kit-dotnet/templates/dotnet"
    manifest = json.loads((template / "managed-files.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        source = template / entry.get("sourceRoot", "files") / entry.get("source", entry["path"])
        if not source.is_file():
            raise AssertionError(f"managed source is missing: {source}")
        if source.suffix in {".props", ".targets"}:
            ElementTree.parse(source)

    targets = (template / "files/eng/program-kit/ProgramKit.Build.targets").read_text(encoding="utf-8")
    for phrase in ("ProgramKitApiContracts", "1.29.1", "ProgramKitFeatureMetadata", "PKF101", "openapi_contracts.py", "feature_metadata.py"):
        if phrase not in targets:
            raise AssertionError(f"managed build target is missing {phrase}")
    bundle_schema = json.loads(
        (template / "files/.program-kit/application-bundle.schema.json").read_text(encoding="utf-8")
    )
    feature_schema = bundle_schema["properties"].get("features", {}).get("items", {})
    if feature_schema.get("additionalProperties") is not False:
        raise AssertionError("application-bundle feature metadata is not closed by the JSON Schema")
    for field in ("identity", "packageId", "featureDependencies", "runtimeDependencies", "routes", "dormant"):
        if field not in feature_schema.get("required", []):
            raise AssertionError(f"application-bundle feature schema does not require {field}")
    persistence = ROOT / "extensions/program-kit-dotnet/references/persistence-profiles.md"
    text = persistence.read_text(encoding="utf-8")
    for phrase in ("ef-postgresql", "ef-sqlserver", "ef-sqlite", "IEntityTypeConfiguration", "Testcontainers", "generic repository", "lazy-loading"):
        if phrase not in text:
            raise AssertionError(f"persistence guidance is missing {phrase}")


def validate_openapi_contracts() -> None:
    script = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/openapi_contracts.py"
    contracts = module(script, "openapi_contracts")
    with tempfile.TemporaryDirectory(prefix="program-kit-openapi-") as value:
        root = Path(value)
        generated = root / "obj/api.json"
        generated.parent.mkdir()
        artifact = root / "contracts/openapi.json"
        baseline = root / "contracts/baseline.json"
        document = {
            "openapi": "3.1.0",
            "info": {"title": "Consumer API", "version": "1.0.0"},
            "paths": {"/orders": {"get": {"operationId": "ListOrders", "responses": {"200": {"description": "OK"}}}}},
        }
        generated.write_text(json.dumps(document), encoding="utf-8")
        first = subprocess.run(
            [
                sys.executable,
                str(script),
                "--generated",
                str(generated),
                "--artifact",
                str(artifact),
                "--baseline",
                str(baseline),
                "--oasdiff-version",
                "1.29.1",
                "--write-generated",
                "--initialize-baseline",
            ],
            capture_output=True,
            text=True,
        )
        if first.returncode != 0 or artifact.read_bytes() != baseline.read_bytes():
            raise AssertionError(f"first OpenAPI baseline was not deterministic: {first.stdout}{first.stderr}")
        document["paths"]["/orders/{id}"] = {
            "get": {"operationId": "GetOrder", "responses": {"200": {"description": "OK"}}}
        }
        generated.write_text(json.dumps(document), encoding="utf-8")
        stale = subprocess.run(
            [
                sys.executable,
                str(script),
                "--generated",
                str(generated),
                "--artifact",
                str(artifact),
                "--baseline",
                str(baseline),
                "--oasdiff-version",
                "1.29.1",
            ],
            capture_output=True,
            text=True,
        )
        if stale.returncode == 0 or "PKO008" not in stale.stderr:
            raise AssertionError("stale generated OpenAPI output was accepted")
        document["paths"]["/orders/{id}"]["get"]["operationId"] = "ListOrders"
        try:
            contracts.validate_operation_identity(document)
        except ValueError as error:
            if "PKO005" not in str(error):
                raise
        else:
            raise AssertionError("duplicate OpenAPI operation identity was accepted")


def validate_sync_preservation() -> None:
    sync = ROOT / "extensions/program-kit-dotnet/scripts/dotnet_sync.py"
    with tempfile.TemporaryDirectory(prefix="program-kit-sync-") as value:
        repository = Path(value)
        command = [
            sys.executable,
            str(sync),
            "--target",
            str(repository),
            "--profile-selected",
            "--host-runtime-accepted",
            "--preview-sources-approved",
            "--persistence-profile",
            "ef-postgresql",
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        root_targets = repository / "Directory.Build.targets"
        original = root_targets.read_text(encoding="utf-8")
        consumer_value = original + "<!-- consumer extension survives -->\n"
        root_targets.write_text(consumer_value, encoding="utf-8")
        unrelated = repository / "consumer-owned.txt"
        unrelated.write_text("keep\n", encoding="utf-8")
        repeated = subprocess.run(command, capture_output=True, text=True)
        if repeated.returncode != 2 or root_targets.read_text(encoding="utf-8") != consumer_value:
            raise AssertionError("scaffold-once consumer MSBuild extension was overwritten or not reported")
        if unrelated.read_text(encoding="utf-8") != "keep\n":
            raise AssertionError("unrelated consumer file changed during synchronization")
        state = json.loads((repository / ".program-kit/managed.json").read_text(encoding="utf-8"))
        if state.get("persistenceProfile") != "ef-postgresql":
            raise AssertionError("selected persistence profile was not recorded")
        root_targets.write_bytes(original.encode("utf-8"))
        converged = subprocess.run(command, capture_output=True, text=True)
        if converged.returncode != 0 or "conflicts: 0" not in converged.stdout:
            raise AssertionError(f"repeated synchronization did not converge: {converged.stdout}{converged.stderr}")


def validate_artifact_ownership() -> None:
    ownership = module(
        ROOT / "extensions/program-kit-governance/scripts/artifact_ownership.py", "artifact_ownership"
    )
    with tempfile.TemporaryDirectory(prefix="program-kit-ownership-") as value:
        root = Path(value)
        artifacts = [
            {"path": path, "ownership": "evidence", "classification": "internal", "lifecycle": "retained"}
            for path in sorted(ownership.CANONICAL)
        ]
        artifacts.append(
            {"path": "eng/program-kit/Build.ps1", "ownership": "managed", "classification": "internal", "lifecycle": "source"}
        )
        manifest = {"schemaVersion": 1, "feature": "SPC-001", "profiles": ["program-kit"], "artifacts": artifacts}
        path = root / "artifact-ownership.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        loaded = ownership.load_manifest(path)
        tasks = root / "tasks.md"
        tasks.write_text("- [ ] Update `eng/program-kit/Build.ps1`\n", encoding="utf-8")
        try:
            ownership.validate_tasks(tasks, loaded, None)
        except ValueError as error:
            if "PKA008" not in str(error) or "consumer-owned" not in str(error):
                raise
        else:
            raise AssertionError("managed path edit was not rejected")


def main() -> int:
    validate_hooks()
    validate_lifecycle()
    validate_utf8()
    validate_feature_activation()
    validate_bundle_feature_closure()
    validate_preflight_seams()
    validate_toolchain_workflow()
    validate_managed_sources()
    validate_openapi_contracts()
    validate_sync_preservation()
    validate_artifact_ownership()
    print("Lifecycle, activation, profile, ownership, and UTF-8 contracts passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
