from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
UPDATER = ROOT / "scripts/upgrade_program_kit.py"
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
from owned_scratch import owned_scratch, filesystem_path, native_path


def load_updater():
    scripts = str(ROOT / "scripts")
    sys.path.insert(0, scripts)
    try:
        specification = importlib.util.spec_from_file_location("program_kit_upgrade", UPDATER)
        if specification is None or specification.loader is None:
            raise AssertionError("could not load release-owned updater")
        module = importlib.util.module_from_spec(specification)
        sys.modules[specification.name] = module
        specification.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(scripts)


def validate_uv_launcher_bridge() -> None:
    if os.name != "nt":
        return
    updater = load_updater()
    with tempfile.TemporaryDirectory(prefix="program-kit-uv-launcher-") as value:
        root = Path(value)
        target = root / "consumer"
        target.mkdir()
        release = root / "release"
        bridge = release / "scripts/invoke_specify.py"
        bridge.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts/invoke_specify.py", bridge)

        environment = root / "external-uv-tools/specify-cli"
        interpreter = environment / "Scripts/python.exe"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_bytes(b"inaccessible uv Python launcher fixture")
        (environment / "pyvenv.cfg").write_text(
            "home = C:\\external\\uv\\python\nuv = 0.11.3\n", encoding="utf-8"
        )
        package = environment / "Lib/site-packages/specify_cli"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            "def main():\n"
            "    print('sandbox-compatible Specify fixture')\n"
            "    return 0\n",
            encoding="utf-8",
        )
        launcher = root / "external-bin/specify.exe"
        launcher.parent.mkdir()
        launcher.write_bytes(
            b"MZ-program-kit-invalid-executable-fixture\n#!"
            + str(interpreter).encode("utf-8")
            + b"\nfrom specify_cli import main\n"
        )
        before = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
        original_probe = updater.run_specify_probe

        def probe(command, arguments, repository):
            if command == [str(launcher)]:
                return subprocess.CompletedProcess(
                    command + arguments,
                    101,
                    "",
                    f'Unable to create process using "{interpreter}" "{launcher}": Access is denied.',
                )
            return original_probe(command, arguments, repository)

        with patch.object(updater, "run_specify_probe", probe):
            resolved = updater.preflight_specify([str(launcher)], target, release)
        after = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
        if before != after:
            raise AssertionError("uv launcher bridge preflight mutated the consumer repository")
        if resolved[:2] != [sys.executable, str(bridge.resolve())] or str(package.parent.resolve()) not in resolved:
            raise AssertionError(f"uv launcher did not resolve the release-owned bridge: {resolved}")
        probe = run(*resolved, "bundle", "install", "--help", cwd=target)
        require_success(probe, "sandbox-compatible uv Specify bridge")


def validate_read_only_module_loading() -> None:
    import py_compile
    updater = load_updater()
    with tempfile.TemporaryDirectory(prefix='program-kit-readonly-adapter-') as directory:
        adapter = Path(directory) / 'adapter.py'
        adapter.write_text('value = 1\n', encoding='utf-8')
        previous = sys.dont_write_bytecode
        updater.load_release_module(adapter, 'readonly_upgrade_adapter')
        if list(adapter.parent.glob('__pycache__/*')) or sys.dont_write_bytecode != previous:
            raise AssertionError('Adapter inspection created consumer bytecode or changed interpreter policy')
        cache = Path(py_compile.compile(str(adapter), doraise=True))
        cached = cache.read_bytes()
        adapter.write_text("value = 'updated adapter without cache writes'\n", encoding='utf-8')
        module = updater.load_release_module(adapter, 'readonly_upgrade_adapter')
        if module.value != 'updated adapter without cache writes' or cache.read_bytes() != cached:
            raise AssertionError('Read-only adapter loading executed stale code or rewrote consumer bytecode')
        adapter.write_text("raise RuntimeError('adapter admission failure fixture')\n", encoding='utf-8')
        try:
            updater.load_release_module(adapter, 'readonly_upgrade_adapter')
        except RuntimeError as error:
            if str(error) != 'adapter admission failure fixture':
                raise
        else:
            raise AssertionError('Adapter admission failure was hidden')
        if cache.read_bytes() != cached or sys.dont_write_bytecode != previous:
            raise AssertionError('Failed adapter inspection rewrote consumer bytecode or interpreter policy')


def run(*command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, env={**os.environ, 'SPECIFY_INIT_DIR': str(cwd)},
                            text=True, encoding='utf-8', errors='replace',
                            capture_output=True, check=False)
    if str(UPDATER) in command:
        evidence = ROOT / 'artifacts/maintenance-flow/local-upgrade-timings.json'
        evidence.parent.mkdir(parents=True, exist_ok=True)
        rows = json.loads(evidence.read_text(encoding='utf-8')) if evidence.is_file() else []
        rows.append({'elapsedSeconds':round(time.perf_counter()-started,3), 'exitCode':result.returncode,
                     'offline': '--offline' in command, 'preview':'--plan' in command,
                     'installationCoherent': '"readinessScope": "offline-setup"' in result.stdout,
                     'deliberateFailureFixture': '--specify-command-json' in command})
        evidence.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    return result


def require_offline_setup(result, label):
    if result.returncode == 3 and ('PKU113 managed setup is coherent; dependency verification remains pending' in result.stderr
                                or 'PKU132 installation is coherent; migration verification remains pending' in result.stderr):
        if '"readinessScope": "offline-setup"' not in result.stdout or '"blockers": []' not in result.stdout:
            raise AssertionError('Upgrade did not establish offline setup: ' + result.stdout)
        return
    require_success(result, label)


def require_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        raise AssertionError(f"{label} failed:\n{result.stdout}{result.stderr}")


def version(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  version:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    raise AssertionError(f"No version in {path}")


def set_manifest_version(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    marker = f'  version: "{old}"'
    if marker not in text:
        raise AssertionError(f"Could not seed old version in {path}")
    path.write_text(text.replace(marker, f'  version: "{new}"', 1), encoding="utf-8")


def authenticate_fictional_native_sources(project: Path, fixture_root: Path) -> Path:
    """Give synthetic version-zero fixtures real native integrity and isolated evidence.

    This is deliberately fictional source history. The actual 0.12.7 regression
    separately installs immutable historical components. No production catalog,
    ownership guard or real consumer is altered to authorize the synthetic test.
    """
    from specify_cli.extensions import ExtensionManager, ExtensionManifest
    from specify_cli.presets import PresetManifest, PresetRegistry
    sys.path.insert(0, str(ROOT / 'scripts'))
    try:
        import native_phase_ownership
    finally:
        sys.path.remove(str(ROOT / 'scripts'))
    staged = fixture_root / 'candidate-release'
    for directory in ('scripts', 'extensions', 'presets', 'workflows', 'releases'):
        shutil.copytree(ROOT / directory, staged / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'bin', 'obj', 'node_modules'))
    for name in ('VERSION', 'bundle.yml', 'README.md', 'LICENSE', 'THIRD-PARTY-NOTICES.md'):
        if (ROOT / name).is_file():
            shutil.copyfile(ROOT / name, staged / name)
    witness = fixture_root / 'fictional-original-source'
    witness.mkdir()
    rows = []
    manager = ExtensionManager(project)
    presets = PresetRegistry(project / '.specify/presets')
    for kind, identity, filename, registry, manifest_type in (
            ('extensions', 'program-kit-governance', 'extension.yml', manager.registry, ExtensionManifest),
            ('extensions', 'program-kit-building-blocks', 'extension.yml', manager.registry, ExtensionManifest),
            ('extensions', 'program-kit-dotnet', 'extension.yml', manager.registry, ExtensionManifest),
            ('presets', 'program-kit-governance-preset', 'preset.yml', presets, PresetManifest)):
        installed = project / '.specify' / kind / identity
        manifest = manifest_type(installed / filename)
        registry.update(identity, {'version': manifest.version, 'manifest_hash': manifest.get_hash()})
        files = {}
        for relative in sorted(native_phase_ownership.installed_source_files(installed)):
            source = installed / relative
            original = witness / kind / identity / relative
            original.parent.mkdir(parents=True, exist_ok=True); original.write_bytes(source.read_bytes())
            files[relative] = sha256(original)
        rows.append({'kind': kind, 'id': identity, 'version': manifest.version,
                     'manifestSha256': manifest.get_hash().removeprefix('sha256:'), 'files': files})
    require_success(run('git', 'init', '--object-format=sha1', '-q', cwd=witness), 'fictional source evidence initialization')
    # Ordinary add can apply the user's text attributes. Record the already
    # captured fixture bytes with native Git plumbing, without transformations.
    index = bytearray()
    for row in rows:
        for relative in row['files']:
            name = row['kind'] + '/' + row['id'] + '/' + relative
            hashed = subprocess.run(['git', 'hash-object', '-w', '--no-filters', '--stdin'],
                                    cwd=witness, input=(witness / name).read_bytes(), capture_output=True, check=True)
            blob = hashed.stdout.decode('ascii').strip()
            index.extend(('100644 ' + blob + '\t' + name + '\0').encode())
    subprocess.run(['git', 'update-index', '-z', '--index-info'], cwd=witness,
                   input=bytes(index), capture_output=True, check=True)
    require_success(run('git', '-c', 'user.name=Program Kit fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'Immutable fictional version-zero native source fixture', cwd=witness), 'fictional source evidence commit')
    commit = run('git', 'rev-parse', 'HEAD', cwd=witness).stdout.strip()
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise AssertionError('Fictional source witness has no actual immutable commit')
    # Archive checkout can apply global EOL attributes. Verify immutable raw Git
    # objects instead, which is the exact byte authority of this fictional fixture.
    requests = [(row['kind'] + '/' + row['id'] + '/' + relative, expected_hash)
                for row in rows for relative, expected_hash in row['files'].items()]
    objects = subprocess.run(['git', 'cat-file', '--batch'], cwd=witness,
                             input=''.join(commit + ':' + path + '\n' for path, _ in requests).encode(),
                             capture_output=True, check=True).stdout
    position = 0
    for relative, expected_hash in requests:
        end = objects.index(b'\n', position)
        header = objects[position:end].decode('ascii').split()
        if len(header) != 3 or header[1] != 'blob':
            raise AssertionError('Missing immutable fictional source object: ' + relative)
        size = int(header[2]); position = end + 1
        recorded = objects[position:position + size]; position += size + 1
        if hashlib.sha256(recorded).hexdigest() != expected_hash:
            raise AssertionError('Fictional source witness must bind exact immutable bytes: ' + relative)
    for row in rows:
        row.update(sourceCommit=commit, sourceScope='fictional disposable source fixture')
    catalog = staged / 'extensions/program-kit-governance/references/native-phase-source-baselines.json'
    value = json.loads(catalog.read_text(encoding='utf-8'))
    value['components'].extend(rows)
    catalog.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return staged


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lifecycle_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    canonical = re.sub(r"(?m)^(\s*-\s+\[)[ xX](\]\s+)", r"\1 \2", text)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def seed_confirmed_feature_intake(project: Path, spec: Path) -> None:
    """Provide the real intake prerequisite for this disposable upgrade fixture."""
    import validate_governance_state as governance_fixture

    scripts = project / ".specify/extensions/program-kit-governance/scripts"
    missing = run(
        sys.executable, str(scripts / "implementation_preflight.py"),
        "--repository", str(project), "--feature-dir", str(spec.parent), cwd=project,
    )
    if missing.returncode != 2 or 'old progress grants no authority' not in missing.stdout:
        raise AssertionError('An old partial feature must require fresh story adoption: ' + missing.stdout + missing.stderr)

    original_directory = Path.cwd()
    sys.path.insert(0, str(scripts))
    try:
        import specification_intake as intake

        os.chdir(project)
        governance = intake.governance
        governance.configure_paths()
        constitution = project / governance.CONSTITUTION
        constitution.parent.mkdir(parents=True, exist_ok=True)
        constitution.write_text(
            governance_fixture.constitution(pending=False).replace("**Status**: Draft", "**Status**: Ratified"),
            encoding="utf-8",
        )
        version, ratified, amended = governance.constitution_metadata(constitution)
        intake.atomic_write(project / governance.RATIFICATION, {
            "status": "Ratified", "gate_verdict": "ratify", "approval_mode": "interactive",
            "constitution": {"path": governance.CONSTITUTION.as_posix(), "version": version,
                             "sha256": sha256(constitution), "ratified": ratified, "last_amended": amended},
        })
        (project / governance.ARCHITECTURE).write_text(
            "# Accepted upgrade fixture architecture\nCatalog.Api owns the OpenAPI contract.\n", encoding="utf-8",
        )
        roadmap = project / governance.ROADMAP
        roadmap.parent.mkdir(parents=True, exist_ok=True)
        roadmap.write_text(governance_fixture.roadmap().replace("SPEC-001", "SPC-001"), encoding="utf-8")
        brief_path = intake.begin(project, "SPC-001", "Upgrade the Catalog.Api OpenAPI producer pin")
        brief = intake.read(brief_path)
        brief.update({field: "Catalog.Api upgrade fixture: " + field for field in intake.FIELDS})
        brief["decisions"] = [{
            "id": "Q1", "question": "Which contract is in scope?", "answer": "Catalog.Api OpenAPI",
            "provenance": "Deterministic upgrade fixture", "rationale": "Exercise producer-pin renewal",
            "dependsOn": [], "disposition": "answered", "blocking": True,
        }]
        intake.atomic_write(brief_path, brief)
        reviewed = intake.review(project, "SPC-001")
        intake.confirm(project, "SPC-001", reviewed["reviewHash"],
                       "Deterministic fixture confirmation", "The fixture confirms this exact review")
        confirmed = intake.check(project, "SPC-001")
        spec.write_text(
            spec.read_text(encoding="utf-8")
            + f"- **Confirmed intake brief**: {confirmed['brief']}\n"
            + f"- **Confirmed intake SHA256**: {confirmed['briefHash']}\n",
            encoding="utf-8",
        )
        intake.check_spec(project, spec)
    finally:
        os.chdir(original_directory)
        sys.path.remove(str(scripts))


def seed_openapi_lifecycle(project: Path, old_runtime: str) -> Path:
    feature = project / "specs/001-openapi-upgrade"
    feature.mkdir(parents=True)
    spec = feature / "spec.md"
    plan = feature / "plan.md"
    tasks = feature / "tasks.md"
    research = feature / "research.md"
    spec.write_text(
        "# spec\n## Governance Traceability\n"
        "- **Specification roadmap entry**: SPC-001\n"
        "- **Architecture constraints**: accepted baseline\n"
        "- **Owned contracts and data**: Catalog.Api OpenAPI\n",
        encoding="utf-8",
    )
    seed_confirmed_feature_intake(project, spec)
    plan.write_text(
        "# plan\n## Architecture Realization\n"
        "- **Roadmap entry and status transition**: SPC-001\n"
        "- **Vertical-slice path**: Catalog.Api OpenAPI to generated client\n"
        "- **Artifact ownership manifest**: artifact-ownership.json\n"
        f"Use Orbyss.Foundation.OpenApi.Exporter {old_runtime} for Catalog.Api OpenAPI.\n",
        encoding="utf-8",
    )
    tasks.write_text(
        "# tasks\n## Governance Completion Evidence\n"
        "- **Roadmap transition**: Delivered after evidence\n"
        "- **Path and ownership protection**: validated\n"
        f"- [ ] T001 Verify Catalog.Api OpenAPI exporter {old_runtime} with "
        "`contracts/openapi/catalog.contract.json`.\n",
        encoding="utf-8",
    )
    research.write_text(
        f"# Research\nUse Orbyss.Foundation.OpenApi.Exporter {old_runtime}.\n",
        encoding="utf-8",
    )
    canonical = {
        "artifacts/program-kit/runtime-closure.json",
        "artifacts/program-kit/host-image.json",
        "artifacts/program-kit/after-tasks-analysis.md",
        "docs/security/security-ledger.md",
        "tests/fixtures/program-kit/local-contract.json",
        "contracts/openapi/catalog.contract.json",
    }
    (feature / "artifact-ownership.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "feature": feature.name,
                "profiles": ["program-kit", "dotnet", "typescript-vite"],
                "artifacts": [
                    {
                        "path": path,
                        "ownership": "consumer-owned" if path.endswith(".contract.json") else "evidence",
                        "classification": "internal",
                        "lifecycle": "source" if path.endswith(".contract.json") else "retained",
                    }
                    for path in sorted(canonical)
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    contract = project / "contracts/openapi/catalog.contract.json"
    contract.parent.mkdir(parents=True)
    contract.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "identity": "catalog-v1",
                "documentName": "v1",
                "shell": "default",
                "producer": {"kind": "Orbyss.Foundation.OpenApi.Exporter", "version": old_runtime},
                "features": ["Catalog.Api"],
                "packageClosure": "artifacts/release-bundle/packages",
                "rawDocument": "artifacts/openapi/catalog.raw.json",
                "artifact": "contracts/openapi/catalog.json",
                "baseline": "contracts/openapi/catalog.baseline.json",
                "compatibility": {
                    "oasdiffVersion": (ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.oasdiff-version').read_text(encoding='utf-8').strip().removeprefix('v'),
                    "approval": "contracts/openapi/catalog.breaking-change.json",
                },
                "generator": {
                    "directory": "tools/openapi/catalog",
                    "packageJson": "tools/openapi/catalog/package.json",
                    "lockFile": "tools/openapi/catalog/package-lock.json",
                    "script": "generate",
                    "generatedTypes": "tools/openapi/catalog/generated/types.ts",
                },
                "application": {
                    "directory": "src/web",
                    "packageJson": "src/web/package.json",
                    "lockFile": "src/web/package-lock.json",
                    "script": "typecheck",
                    "tsconfig": "src/web/tsconfig.json",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "eng/openapi-contracts.json").write_text(
        json.dumps({"schemaVersion": 1, "contracts": ["contracts/openapi/catalog.contract.json"]}) + "\n",
        encoding="utf-8",
    )
    candidate = feature / "npm-candidate.package.json"
    candidate.write_text('{"devDependencies":{"openapi-typescript":"7.13.0"}}\n', encoding="utf-8")
    npm_evidence = project / "artifacts/program-kit/npm-graph.json"
    npm_evidence.parent.mkdir(parents=True, exist_ok=True)
    npm_evidence.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "packageJson": candidate.relative_to(project).as_posix(),
                "packageJsonSha256": sha256(candidate),
                "satisfied": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report = project / "artifacts/program-kit/after-tasks-analysis.md"
    report.write_text(
        "# Specification Analysis Report\n\n"
        "| ID | Category | Severity | Location(s) | Summary | Recommendation |\n"
        "|----|----------|----------|-------------|---------|----------------|\n"
        "| â€” | â€” | â€” | â€” | No findings | Proceed |\n",
        encoding="utf-8",
    )
    lifecycle = project / ".program-kit/lifecycle" / f"{feature.name}.json"
    lifecycle.parent.mkdir(parents=True, exist_ok=True)
    lifecycle.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "feature": feature.name,
                "phases": {
                    "afterTasksAnalysis": {
                        "completedAtUtc": "2026-01-01T00:00:00Z",
                        "artifactHashes": {
                            "spec.md": sha256(spec),
                            "plan.md": sha256(plan),
                            "tasks.md": lifecycle_sha256(tasks),
                        },
                        "report": report.relative_to(project).as_posix(),
                        "reportSha256": sha256(report),
                        "severities": [],
                        "readyForImplementation": True,
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return feature


def main() -> int:
    timings = ROOT / 'artifacts/maintenance-flow/local-upgrade-timings.json'
    timings.unlink(missing_ok=True)
    validate_read_only_module_loading()
    validate_uv_launcher_bridge()
    expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    with owned_scratch(ROOT, 'validation-fixture') as directory, owned_scratch(ROOT, 'validation-fixture') as witness:
        # Preserve every historical profile while using extended paths for Python
        # filesystem I/O. These exact owned roots cannot escape into consumer data.
        project = Path(filesystem_path(directory))
        fixture_directory = filesystem_path(witness)
        initialized = run(
            "specify", "init", ".", "--force", "--non-interactive",
            "--integration", "codex", "--script", "py", "--ignore-agent-tools",
            cwd=project,
        )
        require_success(initialized, "Spec Kit initialization")
        primitive_commands = (
            ("specify", "workflow", "add", str(ROOT / "workflows/program-kit-bootstrap"), "--dev"),
            ("specify", "extension", "add", str(ROOT / "extensions/program-kit-governance"), "--dev", "--force"),
            ("specify", "extension", "add", str(ROOT / "extensions/program-kit-building-blocks"), "--dev", "--force"),
            ("specify", "extension", "add", str(ROOT / "extensions/program-kit-dotnet"), "--dev", "--force"),
            ("specify", "preset", "add", "--dev", str(ROOT / "presets/program-kit-governance-preset")),
        )
        for primitive in primitive_commands:
            require_success(run(*primitive, cwd=project), f"seed {' '.join(primitive[1:3])}")
        # Offline upgrade consumes an explicitly prepared target runtime, not network installs.
        source_scripts = ROOT / 'extensions/program-kit-governance/scripts'
        runtime_spec = importlib.util.spec_from_file_location('upgrade_test_runtime', source_scripts / 'schema_runtime.py')
        runtime = importlib.util.module_from_spec(runtime_spec)
        runtime_spec.loader.exec_module(runtime)
        destination = runtime.runtime_path(project)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(runtime.runtime_path(), destination)
        runtime.record_copy(project)
        old = "0.0.0"
        manifests = (
            project / ".specify/extensions/program-kit-governance/extension.yml",
            project / ".specify/extensions/program-kit-building-blocks/extension.yml",
            project / ".specify/extensions/program-kit-dotnet/extension.yml",
            project / ".specify/presets/program-kit-governance-preset/preset.yml",
            project / ".specify/workflows/program-kit-bootstrap/workflow.yml",
        )
        for manifest in manifests:
            set_manifest_version(manifest, expected, old)
        workflow_registry_path = project / ".specify/workflows/workflow-registry.json"
        workflow_registry = json.loads(workflow_registry_path.read_text(encoding="utf-8"))
        workflow_registry["workflows"]["program-kit-bootstrap"]["version"] = old
        workflow_registry_path.write_text(json.dumps(workflow_registry), encoding="utf-8")
        preset_registry_path = project / ".specify/presets/.registry"
        preset_registry = json.loads(preset_registry_path.read_text(encoding="utf-8"))
        preset_registry["presets"]["program-kit-governance-preset"]["version"] = old
        preset_registry_path.write_text(json.dumps(preset_registry), encoding="utf-8")
        bundle_records = {
            "schema_version": "1.0",
            "bundles": [{
                "bundle_id": "program-kit",
                "version": old,
                "contributed_components": [
                    {"kind": "extensions", "id": "program-kit-governance", "version": old},
                    {"kind": "extensions", "id": "program-kit-building-blocks", "version": old},
                    {"kind": "extensions", "id": "program-kit-dotnet", "version": old},
                    {"kind": "presets", "id": "program-kit-governance-preset", "version": old},
                ],
            }],
        }
        (project / ".specify/bundle-records.json").write_text(
            json.dumps(bundle_records), encoding="utf-8"
        )
        release = authenticate_fictional_native_sources(project, Path(fixture_directory).resolve())
        from upgrade_selection_cases import validate_selection_upgrades
        validate_selection_upgrades(project, sys.modules[__name__], release=release)
        managed = project / ".program-kit/managed.json"
        managed.parent.mkdir(parents=True, exist_ok=True)
        managed.write_text(
            json.dumps({
                "schemaVersion": 1,
                "programKitVersion": old,
                "dotnetSdk": "10.0.202",
                "dotnetSdkSource": "program-kit-default",
                "webProfile": "none",
                "persistenceProfile": "none",
                "files": {},
            }),
            encoding="utf-8",
        )
        bootstrap_decisions = project / "docs/architecture/bootstrap-decisions.json"
        bootstrap_decisions.parent.mkdir(parents=True)
        bootstrap_decisions.write_text(
            json.dumps({
                "schema_version": "1.0",
                "default_profile": {"id": "program-kit-standard", "version": old},
                "selected_profiles": [],
                "dotnet": {
                    "host_runtime": "Custom.Host",
                    "host_source": "override",
                    "program_kit_host_opt_out": True,
                    "opt_out_reason": "Isolate the OpenAPI upgrade contract from host composition.",
                },
                "choices": [{
                    "id": "first-slice",
                    "decision": "Keep the accepted first slice",
                    "source": "explicit-intake",
                    "rationale": "It is the approved consumer outcome",
                    "override": "Use a later accepted decision",
                }],
                "overrides": [],
                "acknowledgements": [],
                "unresolved": [],
                "deferred": [],
                "persistence": [
                    {"owner": owner, "storage": "server-relational", "profile": "ef-postgresql", "status": "proposed"}
                    for owner in ("policy-portfolio", "owner-access")
                ],
            }),
            encoding="utf-8",
        )
        from upgrade_probe_fixtures import render_registered_probes
        render_registered_probes(project)
        probe_inputs = [project / 'docs/architecture/bootstrap-proof-plan.json',
                        *(project / 'docs/architecture/compatibility').glob('*')]
        immutable_probes = {path: path.read_bytes() for path in probe_inputs if path.is_file()}
        immutable_decisions = bootstrap_decisions.read_bytes()
        command = (
            sys.executable, str(UPDATER), "--release-root", str(release),
            "--target", str(project), "--integration", "codex", "--offline",
        )
        installed_tool = project / '.specify/extensions/program-kit-governance/scripts/json_schema.py'
        original_tool = installed_tool.read_bytes()
        edited_tool = original_tool + b'\n# consumer-owned edit\n'
        installed_tool.write_bytes(edited_tool)
        rejected_edit = run(*command, cwd=project)
        if (rejected_edit.returncode != 2 or not ('SCHEMA_TOOLS_LOCALLY_EDITED' in rejected_edit.stderr
                or 'PKU135' in rejected_edit.stderr and 'json_schema.py' in rejected_edit.stderr)
                or 'Resolve bundle composition record' in rejected_edit.stdout
                or installed_tool.read_bytes() != edited_tool):
            raise AssertionError(f'Upgrade did not protect consumer tool edits: {rejected_edit.stdout}{rejected_edit.stderr}')
        installed_tool.write_bytes(original_tool)
        blocked_cli = project / "blocked_specify.py"
        blocked_cli.write_text(
            "import sys\nprint('sandbox denied the installed Specify interpreter', file=sys.stderr)\n"
            "raise SystemExit(101)\n",
            encoding="utf-8",
        )
        before_preflight = {
            path.relative_to(project).as_posix(): sha256(path)
            for path in project.rglob("*")
            if path.is_file()
        }
        blocked = run(
            *command,
            "--specify-command-json",
            json.dumps([sys.executable, str(blocked_cli)]),
            cwd=project,
        )
        after_preflight = {
            path.relative_to(project).as_posix(): sha256(path)
            for path in project.rglob("*")
            if path.is_file()
        }
        if blocked.returncode != 2 or "PKU112" not in blocked.stderr:
            raise AssertionError(f"inaccessible Specify launcher was not rejected:\n{blocked.stdout}{blocked.stderr}")
        if before_preflight != after_preflight or (project / ".specify/program-kit-upgrade.lock").exists():
            raise AssertionError("Specify executable preflight mutated the consumer repository")

        protected_skill = (
            project
            / ".agents/skills/speckit-program-kit-governance-bootstrap/SKILL.md"
        )
        original_mode = stat.S_IMODE(protected_skill.stat().st_mode)
        protected_skill.chmod(stat.S_IREAD)
        before_destination_preflight = {
            path.relative_to(project).as_posix(): sha256(path)
            for path in project.rglob("*")
            if path.is_file()
        }
        try:
            destination_blocked = run(*command, cwd=project)
        finally:
            protected_skill.chmod(original_mode | stat.S_IWRITE)
        after_destination_preflight = {
            path.relative_to(project).as_posix(): sha256(path)
            for path in project.rglob("*")
            if path.is_file()
        }
        if destination_blocked.returncode != 2 or "PKU115" not in destination_blocked.stderr:
            raise AssertionError(
                "protected integration destination was not rejected before mutation:\n"
                f"{destination_blocked.stdout}{destination_blocked.stderr}"
            )
        if "Resolve bundle composition record" in destination_blocked.stdout:
            raise AssertionError("destination permission preflight began component mutation")
        if before_destination_preflight != after_destination_preflight:
            changed = sorted(name for name in before_destination_preflight.keys() | after_destination_preflight.keys()
                             if before_destination_preflight.get(name) != after_destination_preflight.get(name))
            raise AssertionError("destination permission preflight changed consumer file content: " + ', '.join(changed))
        if "outside this sandbox" not in destination_blocked.stderr or "SKILL.md" not in destination_blocked.stderr:
            raise AssertionError("PKU115 omitted the blocked destination or copyable recovery route")

        partial_cli = project / "partial_specify.py"
        partial_cli.write_text(
            "import subprocess, sys\n"
            "args = sys.argv[1:]\n"
            "if args[:2] == ['extension', 'add'] and "
            "any(value.replace('\\\\', '/').endswith('/extensions/program-kit-governance') for value in args):\n"
            "    print('deliberate third-step failure', file=sys.stderr)\n"
            "    raise SystemExit(97)\n"
            "raise SystemExit(subprocess.run(['specify', *args], check=False).returncode)\n",
            encoding="utf-8",
        )
        partial = run(
            *command,
            "--specify-command-json",
            json.dumps([sys.executable, str(partial_cli)]),
            cwd=project,
        )
        if partial.returncode != 2 or "PKU105 Install governance extension" not in partial.stderr:
            raise AssertionError(f"partial sequential upgrade fixture did not fail at step three:\n{partial.stdout}{partial.stderr}")
        if "Resolve bundle composition record" in partial.stdout or "Install bootstrap workflow" not in partial.stdout:
            raise AssertionError("partial sequential upgrade advanced bundle authority before component refresh completed")
        partial_records = json.loads(
            (project / ".specify/bundle-records.json").read_text(encoding="utf-8")
        )["bundles"][0]
        if partial_records.get("version") != old or version(manifests[0]) != old:
            raise AssertionError("partial upgrade fixture did not leave the expected mixed component state")

        post_install_cli = project / 'post_install_specify.py'
        post_install_cli.write_text(
            "import subprocess, sys\nfrom pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "result = subprocess.run(['specify', *args], check=False)\n"
            "if result.returncode == 0 and args[:2] == ['preset', 'add']:\n"
            "    path = Path('.specify/extensions/program-kit-governance/scripts/repository_sync.py')\n"
            "    with path.open('a', encoding='utf-8') as stream:\n"
            "        stream.write('\\ndef readiness(*args, **kwargs):\\n    return {\\\"ready\\\": False, \\\"blockers\\\": [\\\"deliberate post-install convergence failure\\\"]}\\n')\n"
            "raise SystemExit(result.returncode)\n", encoding='utf-8')
        post_install = run(*command, '--specify-command-json', json.dumps([sys.executable, str(post_install_cli)]), cwd=project)
        if post_install.returncode != 2 or 'deliberate post-install convergence failure' not in post_install.stderr:
            raise AssertionError('Post-install convergence fixture did not fail honestly: ' + post_install.stdout + post_install.stderr)
        if {version(path) for path in manifests} != {expected}:
            raise AssertionError('Post-install fixture did not first install all target components')
        if (project / '.specify/governance/program-kit-upgrades.json').exists():
            raise AssertionError('Failed convergence fabricated accepted upgrade authority')
        attempts = list((project / 'artifacts/program-kit/runs').glob('*/upgrade-attempt.json'))
        failures = [json.loads(path.read_text()) for path in attempts]
        if not any(value.get('diagnostic', '').startswith('PKU116') and value['previousInstalledVersion'] == old for value in failures):
            raise AssertionError('Post-install failure lost its root diagnostic or original version')

        # The injected source defect is deliberately local fixture code. The
        # ownership admission now correctly refuses to erase an arbitrary source
        # edit during retry, so repair this exact owned injection first.
        injected_source = project / '.specify/extensions/program-kit-governance/scripts/repository_sync.py'
        publisher_source = (release / 'extensions/program-kit-governance/scripts/repository_sync.py').read_bytes()
        injection = '\ndef readiness(*args, **kwargs):\n    return {"ready": False, "blockers": ["deliberate post-install convergence failure"]}\n'
        if injected_source.read_bytes() not in {publisher_source + injection.encode(), publisher_source + injection.replace('\n', '\r\n').encode()}:
            raise AssertionError('Injected source changed independently; preserve it instead of replacing unknown edits')
        injected_source.write_bytes(publisher_source)

        # Exercise the documented plain-Python entry point as well as the CLI-owned guards.
        plain_python = shutil.which('python') or sys.executable
        installed = run(plain_python, *command[1:], cwd=project)
        require_offline_setup(installed, "local release upgrade")
        if 'deferredPersistenceAdmissions' not in installed.stdout or 'policy-portfolio' not in installed.stdout:
            raise AssertionError('Initialized consumer lost its explicit future admission obligations')
        order = (
            "Install bootstrap workflow",
            "Install governance extension",
            "Install building-block extension",
            "Install .NET extension",
            "Remove prior governance preset",
            "Install governance preset",
            "Resolve bundle composition record",
            "Synchronize existing repository setup",
            "Verify offline repository convergence",
            "Validate cross-component version coherence",
        )
        offsets = [installed.stdout.find(label) for label in order]
        if any(offset < 0 for offset in offsets) or offsets != sorted(offsets):
            raise AssertionError(f"Component mutations were not visibly sequential: {installed.stdout}")

        if {version(path) for path in manifests} != {expected}:
            raise AssertionError("Local release installation left mixed component manifests")
        state = json.loads(managed.read_text(encoding="utf-8"))
        if state.get("programKitVersion") != expected:
            raise AssertionError(f"Managed baseline did not advance to {expected}: {state}")
        final_records = json.loads(
            (project / ".specify/bundle-records.json").read_text(encoding="utf-8")
        )["bundles"][0]
        final_versions = {final_records["version"]} | {
            component["version"] for component in final_records["contributed_components"]
        }
        if final_versions != {expected}:
            raise AssertionError(f"Bundle record did not converge: {final_records}")
        if "Synchronize existing repository setup" not in installed.stdout:
            raise AssertionError("Updater did not report managed baseline synchronization")
        if bootstrap_decisions.read_bytes() != immutable_decisions:
            raise AssertionError("Updater rewrote immutable bootstrap decisions")
        if any(path.read_bytes() != data for path, data in immutable_probes.items()):
            raise AssertionError('Updater changed registered bootstrap probe recipes/contracts/sources')
        if (project / '.specify/governance/program-kit-upgrades.json').exists():
            raise AssertionError('Routine upgrade wrote a duplicate bootstrap acceptance record')
        installation = json.loads((project / '.program-kit/installation/migration.json').read_text())
        if installation['fromVersion'] != old or installation['toVersion'] != expected:
            raise AssertionError('Installation metadata lost original migration scope')

        old_runtime = "0.0.0-preview.1"
        building_blocks = json.loads(
            (ROOT / 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.json').read_text(encoding='utf-8')
        )
        target_runtime = building_blocks["families"]["foundation"]["releaseVersion"]
        target_exporter = json.loads((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/.config/dotnet-tools.json').read_text(encoding='utf-8'))['tools']['orbyss.foundation.openapi.exporter']['version']
        feature = seed_openapi_lifecycle(project, old_runtime)
        (project / "Program.slnx").write_text("<Solution />\n", encoding="utf-8")
        # This fixture's stale conventional lock is active, not an unexplained
        # orphan. Its native project owner remains present through migration.
        (project / 'Fixture.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
        (project / "packages.lock.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "dependencies": {
                        "net10.0": {
                            "Orbyss.Foundation.Authentication": {
                                "type": "Direct",
                                "requested": f"[{old_runtime}, )",
                                "resolved": old_runtime,
                            }
                        }
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        contract_path = project / "contracts/openapi/catalog.contract.json"
        contract_before = contract_path.read_bytes()
        history_before = {path:path.read_bytes() for path in feature.glob('*.md')}
        lifecycle_path = project / '.program-kit/lifecycle/001-openapi-upgrade.json'
        lifecycle_before = lifecycle_path.read_bytes()
        accepted_command = (*command, '--accept-openapi-producer-pin-reconciliation')
        reconciled = run(*accepted_command, cwd=project)
        if reconciled.returncode != 3 or 'PKU113' not in reconciled.stderr:
            raise AssertionError('Offline upgrade did not report actual lock verification pending: ' + reconciled.stdout + reconciled.stderr)
        contract_value = json.loads(contract_path.read_text(encoding="utf-8"))
        if contract_value["producer"]["version"] != target_exporter:
            raise AssertionError("registered OpenAPI producer pin did not advance atomically")
        if any(path.read_bytes() != payload for path,payload in history_before.items()):
            raise AssertionError('Mechanical producer upgrade rewrote feature authoring documents')
        if lifecycle_path.read_bytes() != lifecycle_before:
            raise AssertionError('Mechanical producer upgrade rewrote historical results')
        lock_renewal = json.loads(
            (project / "artifacts/program-kit/dotnet-lock-renewal.json").read_text(encoding="utf-8")
        )
        expected_commands = [
            "python .specify/extensions/program-kit-governance/scripts/repository_sync.py request-renew --phase upgrade",
            "python .specify/extensions/program-kit-building-blocks/scripts/restore_dependencies.py renew --approved --lock .program-kit/sync/dependencies.json --request artifacts/program-kit/building-block-restore-request.json",
            "python .specify/extensions/program-kit-governance/scripts/repository_sync.py request-locked --phase upgrade",
            "python .specify/extensions/program-kit-building-blocks/scripts/restore_dependencies.py locked --approved --lock .program-kit/sync/dependencies.json --request artifacts/program-kit/building-block-restore-request.json",
        ]
        if (
            lock_renewal.get("targetPackageVersions", {}).get("Orbyss.Foundation.Authentication") != building_blocks["families"]["foundation"]["releaseVersion"]
            or lock_renewal.get("affectedLocks") != ["packages.lock.json"]
            or lock_renewal.get("renewalCommands") != expected_commands
            or lock_renewal.get("satisfied") is not False
        ):
            raise AssertionError(f"NuGet lock renewal evidence is incomplete: {lock_renewal}")

        sync = project / ".specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py"
        require_success(
            run(
                sys.executable,
                str(sync),
                "--target",
                str(project),
                "--profile-selected",
                "--persistence-profile",
                "none",
                "--web-profile",
                "none",
                "--check",
                "--upgrade-existing",
                cwd=project,
            ),
            "post-reconciliation managed sync check",
        )
        ownership = project / ".specify/extensions/program-kit-governance/scripts/artifact_ownership.py"
        require_success(
            run(
                sys.executable,
                str(ownership),
                "--manifest",
                str(feature / "artifact-ownership.json"),
                "--plan",
                str(feature / "plan.md"),
                "--tasks",
                str(feature / "tasks.md"),
                cwd=project,
            ),
            "post-reconciliation artifact ownership",
        )
        preflight = project / ".specify/extensions/program-kit-governance/scripts/implementation_preflight.py"
        for implementation_command in ([sys.executable, str(preflight), '--repository', str(project), '--feature-dir', str(feature)],
                                       [sys.executable, str(preflight.with_name('phase_obligations.py')), 'check', '--repository', str(project), '--feature-dir', str(feature), '--phase', 'implementation']):
            blocked = run(*implementation_command, cwd=project)
            if blocked.returncode != 2 or 'old progress grants no authority' not in blocked.stdout:
                raise AssertionError('Old partial upgrade fixture continued without fresh adoption: ' + blocked.stdout + blocked.stderr)
        if lifecycle_path.read_bytes() != lifecycle_before:
            raise AssertionError('Normal implementation guidance rewrote historical lifecycle results')
        lock_value = json.loads((project / "packages.lock.json").read_text(encoding="utf-8"))
        dependency = lock_value["dependencies"]["net10.0"]["Orbyss.Foundation.Authentication"]
        dependency["requested"] = f"[{target_runtime}, )"
        dependency["resolved"] = target_runtime
        (project / "packages.lock.json").write_text(
            json.dumps(lock_value, indent=2) + "\n",
            encoding="utf-8",
        )
        renewed_metadata = run(*command, cwd=project)
        if renewed_metadata.returncode != 3 or 'dependency verification remains pending' not in renewed_metadata.stderr:
            raise AssertionError('Changing package lock metadata falsely satisfied shared dependency verification: '
                                 + renewed_metadata.stdout + renewed_metadata.stderr)
        satisfied_renewal = json.loads(
            (project / "artifacts/program-kit/dotnet-lock-renewal.json").read_text(encoding="utf-8")
        )
        if (
            satisfied_renewal.get("targetPackageVersions", {}).get("Orbyss.Foundation.Authentication") != building_blocks["families"]["foundation"]["releaseVersion"]
            or satisfied_renewal.get("reason") != "shared-dependency-verification-pending"
            or satisfied_renewal.get("satisfied") is not False
        ):
            raise AssertionError(f"NuGet lock renewal did not converge: {satisfied_renewal}")

        migration = json.loads((project / '.program-kit/installation/migration.json').read_text())
        if migration['status'] != 'pending' or migration['migrationCompletionEstablished']:
            raise AssertionError('Pending consumer verification was reported as a completed migration')
        before_plan = {path.relative_to(project).as_posix(): sha256(path) for path in project.rglob('*') if path.is_file()}
        preview = run(*command, '--plan', cwd=project)
        require_success(preview, 'unfinished migration read-only plan')
        preview_plan = json.loads(preview.stdout)
        offer = preview_plan['optionalSoftwareReview']
        if (offer['optional'] is not True or offer['networkLookupPerformed'] is not False
                or offer['choices'] != ['Keep current versions', 'Review qualified dependency profiles', 'Review all repository software']):
            raise AssertionError('Upgrade preview did not offer an optional software review without lookups')
        if preview_plan['fromVersion'] != old or preview_plan['toVersion'] != expected or not preview_plan['migrations']:
            raise AssertionError('Installed files caused the unfinished migration origin to disappear')
        if before_plan != {path.relative_to(project).as_posix(): sha256(path) for path in project.rglob('*') if path.is_file()}:
            raise AssertionError('Migration preview mutated consumer authority or evidence')

        lock = project / ".specify/program-kit-upgrade.lock"
        lock.write_text("test lock\n", encoding="utf-8")
        locked = run(*command, cwd=project)
        if locked.returncode != 2 or "PKU106" not in locked.stderr:
            raise AssertionError("Concurrent component mutation lock was not rejected")
        if not lock.is_file():
            raise AssertionError("Updater removed a lock it did not own")

    print("Sequential offline/local Program Kit upgrade and coherence validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
