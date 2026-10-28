from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml
from owned_fixture import FixtureDirectory


EXPECTED_HOOKS = {
    "before_specify",
    "after_specify",
    "after_plan",
    "before_plan",
    "before_tasks",
    "after_tasks",
    "before_implement",
    "after_implement",
}

RETIRED_COMMANDS = {
    'assessment', 'research', 'roadmap', 'tooling', 'bootstrap-closure',
    'bootstrap-recovery', 'proxy-bootstrap', 'bootstrap',
    'constitution-begin', 'constitution-review', 'constitution-ratify',
}


def install_archives(project: Path, release: Path, archives: dict, *, version: str):
    """Keep native planning, pin checks and ownership; supply local release ZIPs."""
    from specify_cli._assets import get_speckit_version
    from specify_cli.bundles.adapters import DefaultPrimitiveInstaller
    from specify_cli.bundles.installer import install_bundle
    from specify_cli.bundles.manifest import BundleManifest
    from specify_cli.bundles.resolver import resolve_install_plan
    from specify_cli.events import refresh_integration_events
    from specify_cli.extensions import ExtensionManager
    from specify_cli.presets import PresetManager
    sys.path.insert(0, str(release / 'extensions/program-kit-governance/scripts'))
    import render_profile

    def install(kind, identity, force=False):
        archive = archives[(kind, identity)]
        operation = 'extension' if kind == 'extensions' else 'preset'
        with render_profile.capture(project, [operation, 'add', str(archive)]):
            manager = ExtensionManager(project) if kind == 'extensions' else PresetManager(project)
            installed = manager.install_from_zip(archive, get_speckit_version(), force=force,
                expected_id=identity, expected_version=version)
            if kind == 'extensions':
                refresh_integration_events(project)
                _, _, failed = manager.scaffold_config(installed.id)
                if failed:
                    raise AssertionError('Native archive configuration scaffolding failed: ' + ', '.join(failed))

    class ArchiveInstaller(DefaultPrimitiveInstaller):
        def install(self, target, component):
            assert Path(target).resolve() == project.resolve()
            assert component.version == version
            install(component.kind, component.id)

    manifest = BundleManifest.from_file(release / 'bundle.yml')
    plan = resolve_install_plan(manifest, speckit_version=get_speckit_version(), active_integration='codex')
    result = install_bundle(project, plan, ArchiveInstaller(allow_network=False), manifest=manifest)
    assert len(result.installed) == 4 and not result.skipped
    return install


def installed_check(project, script, *arguments, expected=0):
    result = subprocess.run([sys.executable, '-B', str(script), *arguments], cwd=project,
        capture_output=True, text=True, encoding='utf-8', timeout=90)
    if result.returncode != expected:
        raise AssertionError(f'Installed command returned {result.returncode}, expected {expected}: '
                             + result.stdout + result.stderr)
    return result


def run(*args: str, cwd: Path) -> None:
    command = args
    specify_site_packages = os.environ.get("PROGRAM_KIT_SPECIFY_SITE_PACKAGES")
    if args and args[0] == "specify" and specify_site_packages:
        command = (
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "scripts/invoke_specify.py"),
            "--site-packages",
            specify_site_packages,
            "--",
            *args[1:],
        )
    subprocess.run(command, cwd=cwd, check=True)


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description='Qualify actual locally packaged component installation.')
    parser.add_argument('--assets-dir', default='artifacts', help='Repository-relative packaged candidate directory.')
    args = parser.parse_args()
    assets = (root / args.assets_dir).resolve()
    if not assets.is_relative_to(root):
        raise ValueError('Packaged candidate assets must remain inside the repository')
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    extension_zip = assets / f"program-kit-governance-{version}.zip"
    building_blocks_zip = assets / f"program-kit-building-blocks-{version}.zip"
    dotnet_zip = assets / f"program-kit-dotnet-{version}.zip"
    preset_zip = assets / f"program-kit-governance-preset-{version}.zip"
    bundle_zip = assets / f"program-kit-{version}.zip"
    tooling_zip = assets / f"program-kit-tooling-{version}.zip"
    initializers = {
        suffix: assets / f"Initialize-ProgramKit-{version}.{suffix}"
        for suffix in ("cmd", "sh")
    }
    if not all(
        path.is_file()
        for path in (
            extension_zip,
            building_blocks_zip,
            dotnet_zip,
            preset_zip,
            bundle_zip,
            tooling_zip,
            *initializers.values(),
        )
    ):
        raise FileNotFoundError("Build release assets before running the install test")
    for suffix, initializer in initializers.items():
        expected_bytes = (root / f"Initialize-ProgramKit.{suffix}").read_bytes()
        if suffix == "cmd":
            expected_bytes = expected_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if initializer.read_bytes() != expected_bytes:
            raise AssertionError(
                f"Versioned {suffix} consumer initializer differs from the root template"
            )

    for release_zip in (extension_zip, building_blocks_zip, dotnet_zip, preset_zip, bundle_zip, tooling_zip):
        with zipfile.ZipFile(release_zip, "r") as archive:
            forbidden_entries = []
            for name in archive.namelist():
                parts = Path(name).parts
                if (
                    name.endswith(".rules")
                    or name.endswith(".pyc")
                    or "__pycache__" in parts
                    or "bin" in parts
                    or "obj" in parts
                    or name.endswith(".nupkg")
                ):
                    forbidden_entries.append(name)
            if forbidden_entries:
                raise AssertionError(
                    f"{release_zip.name} contains generated output or approval rules: "
                    f"{forbidden_entries}"
                )

    with zipfile.ZipFile(bundle_zip, "r") as archive:
        names = archive.namelist()
        if len(names) > 512:
            raise AssertionError(
                f"Program Kit bundle exceeds Spec Kit's 512-entry safety limit: {len(names)}"
            )
        forbidden_prefixes = (".github/", "docs/", "src/", "test/", "tests/")
        leaked = [name for name in names if name.startswith(forbidden_prefixes)]
        if leaked:
            raise AssertionError(
                f"Program Kit install bundle contains repository-only source: {leaked[:10]}"
            )
        if set(names) != {"LICENSE", "README.md", "THIRD-PARTY-NOTICES.md", "VERSION", "bundle.yml"}:
            raise AssertionError("Composition archive must contain only native manifest and metadata")
    with zipfile.ZipFile(tooling_zip, "r") as archive:
        names = archive.namelist()
        required_runtime = {
            "scripts/record_local_bundle.py",
            "scripts/product_version.py",
            "scripts/initialize_device.py",
            "scripts/install_local_extension.py",
            "bundle.yml",
            "VERSION",
            "scripts/upgrade_program_kit.py",
            "scripts/invoke_specify.py",
        }
        missing_runtime = required_runtime.difference(names)
        if missing_runtime:
            raise AssertionError(
                f"Program Kit install bundle is missing runtime assets: {sorted(missing_runtime)}"
            )

    with FixtureDirectory(prefix="program-kit-release-test-") as directory:
        owned = Path(directory)
        project = owned / 'consumer'
        project.mkdir()
        release = owned / 'release'
        with zipfile.ZipFile(tooling_zip) as archive:
            archive.extractall(release)
        with zipfile.ZipFile(bundle_zip) as archive:
            archive.extractall(release)
        extracted_extension = owned / "release-extension"
        extracted_building_blocks = owned / "release-building-block-extension"
        extracted_dotnet = owned / "release-dotnet-extension"
        extracted_preset = owned / "release-governance-preset"
        with zipfile.ZipFile(extension_zip, "r") as archive:
            archive.extractall(extracted_extension)
        with zipfile.ZipFile(building_blocks_zip, "r") as archive:
            archive.extractall(extracted_building_blocks)
        if not (extracted_extension / "extension.yml").is_file():
            raise AssertionError("Extension release ZIP must contain extension.yml at its root")
        if not (extracted_extension / "scripts/governance_state.py").is_file():
            raise AssertionError("Extension release ZIP must contain the governance-state validator")
        for path in (
            "extension.yml",
            "scripts/building_blocks.py",
            "scripts/public_availability.py",
            "references/building-block-selection.schema.json",
            "references/building-blocks-lock.schema.json",
            "references/orbyss-building-blocks.json",
        ):
            if not (extracted_building_blocks / path).is_file():
                raise AssertionError(f"Building-block extension release ZIP is missing {path}")
        for path in (
            "scripts/product_intake.py",
            "commands/speckit.program-kit-governance.upgrade.md",
            "references/consumer-upgrade.md",
            "scripts/specification_intake.py",
            "scripts/architecture_map.py",
            "scripts/c4_view.py",
            "commands/speckit.program-kit-governance.product-intake.md",
            "references/product-founding.md",
            "commands/speckit.program-kit-governance.grilling.md",
            "commands/speckit.program-kit-governance.specification-intake.md",
            "references/specification-intake.md",
            "commands/speckit.program-kit-governance.view-c4.md",
            "references/architecture-map.schema.json",
            "references/architecture-map-v2.schema.json",
            "references/architecture-map-minimal.json",
            "references/intake-method.md",
            "references/intake-artifacts.md",
            "references/capability-index.json",
            "references/bootstrap-decisions.schema.json",
            "references/codex-desktop-windows.md",
            "references/c4-viewing.md",
            "references/c4-viewer-tool.json",
        ):
            if not (extracted_extension / path).is_file():
                raise AssertionError(f"Extension release ZIP is missing {path}")
        manifest = yaml.safe_load((extracted_extension / 'extension.yml').read_text(encoding='utf-8'))
        for command in manifest['provides']['commands']:
            if not (extracted_extension / command['file']).is_file():
                raise AssertionError('Advertised command missing from archive: ' + command['name'])
        for name in RETIRED_COMMANDS:
            if (extracted_extension / f'commands/speckit.program-kit-governance.{name}.md').exists():
                raise AssertionError('Archive still delivers retired command: ' + name)
        for retired in ('task_draft', 'conformance_repair', 'operation_readiness',
                        'historical_phase_evidence', 'feature_plan_decisions', 'review_material',
                        'lifecycle_state', 'artifact_ownership', 'api_proof', 'architecture_proof',
                        'capability_adoption'):
            if (extracted_extension / f'scripts/{retired}.py').exists():
                raise AssertionError('Archive still delivers retired authoring/lifecycle engine: ' + retired)
        packaged_rule_files = list(extracted_extension.rglob("*.rules"))
        if packaged_rule_files:
            raise AssertionError(
                f"Extension release ZIP must not contain approval rules: {packaged_rule_files}"
            )
        packaged_guidance = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                extracted_extension
                / "commands/speckit.program-kit-governance.product-intake.md",
                extracted_extension / "references/codex-desktop-windows.md",
            )
        )
        for phrase in (
            "Always allow",
            "first four argument tokens",
            "program-kit-bootstrap.rules",
            "approve only this exact prefix",
        ):
            if phrase in packaged_guidance:
                raise AssertionError(
                    f"Extension release ZIP reintroduced escalation guidance: {phrase}"
                )
        if 'normal user-owned PowerShell or WSL' not in ' '.join(packaged_guidance.split()):
            raise AssertionError('Packaged Windows guidance lost the human-terminal installation boundary')
        for reference in ("vertical-slicing.md", "modularity-and-contracts.md", "default-adoption.md"):
            if not (extracted_extension / "references" / reference).is_file():
                raise AssertionError(f"Extension release ZIP is missing {reference}")
        with zipfile.ZipFile(dotnet_zip, "r") as archive:
            archive.extractall(extracted_dotnet)
        if not (extracted_dotnet / "extension.yml").is_file():
            raise AssertionError(".NET extension release ZIP must contain extension.yml at its root")
        for path in (
            "scripts/dotnet_sync.py",
            "references/dotnet-engineering.md",
            "templates/dotnet/files/.editorconfig",
        ):
            if not (extracted_dotnet / path).is_file():
                raise AssertionError(f".NET extension release ZIP is missing {path}")
        with zipfile.ZipFile(preset_zip, "r") as archive:
            archive.extractall(extracted_preset)
        if not (extracted_preset / "preset.yml").is_file():
            raise AssertionError("Governance preset release ZIP must contain preset.yml at its root")
        for path in (
            "templates/constitution-governance.md",
            "templates/spec-governance.md",
            "templates/plan-governance.md",
            "templates/tasks-governance.md",
            "commands/speckit.tasks.md",
            "commands/speckit.implement.md",
        ):
            if not (extracted_preset / path).is_file():
                raise AssertionError(f"Governance preset release ZIP is missing {path}")

        print(f"Initializing packaged-release disposable consumer: {project}")
        run(
            "specify",
            "init",
            ".",
            "--force",
            "--non-interactive",
            "--integration",
            "codex",
            "--script",
            "py",
            "--ignore-agent-tools",
            cwd=project,
        )
        reinstall = install_archives(project, release, {
            ('extensions', 'program-kit-governance'): extension_zip,
            ('extensions', 'program-kit-building-blocks'): building_blocks_zip,
            ('extensions', 'program-kit-dotnet'): dotnet_zip,
            ('presets', 'program-kit-governance-preset'): preset_zip,
        }, version=version)
        if not (project / ".agents/skills/speckit-constitution/SKILL.md").is_file():
            raise AssertionError(
                "Spec Kit did not install the core speckit.constitution command"
            )
        python_resolver = project / ".specify/scripts/python/resolve_template.py"
        if not python_resolver.is_file():
            raise AssertionError("Python-flavor consumer is missing resolve_template.py")
        constitution_skill_text = (
            project / ".agents/skills/speckit-constitution/SKILL.md"
        ).read_text(encoding="utf-8")
        if ".specify/scripts/python/resolve_template.py" not in constitution_skill_text:
            raise AssertionError("Constitution skill does not reference the Python resolver")
        preexisting_config_path = project / ".specify/extensions.yml"
        preexisting_config = yaml.safe_load(preexisting_config_path.read_text(encoding="utf-8"))
        preexisting_config.setdefault("hooks", {}).setdefault("after_specify", []).append(
            {
                "extension": "consumer-extension",
                "command": "speckit.consumer.audit",
                "enabled": True,
                "optional": True,
                "priority": 50,
                "condition": None,
            }
        )
        preexisting_config_path.write_text(
            yaml.safe_dump(preexisting_config, sort_keys=False), encoding="utf-8"
        )
        reinstall('extensions', 'program-kit-governance', force=True)
        reinstall('extensions', 'program-kit-governance', force=True)
        for kind, identity, payload in (
            ('extensions', 'program-kit-governance', extension_zip),
            ('extensions', 'program-kit-building-blocks', building_blocks_zip),
            ('extensions', 'program-kit-dotnet', dotnet_zip),
            ('presets', 'program-kit-governance-preset', preset_zip),
        ):
            destination = project / '.specify' / kind / identity
            if destination.is_symlink() or (destination / '.specify-dev').exists():
                raise AssertionError('Release archive produced linked development registration: ' + identity)
            with zipfile.ZipFile(payload) as archive:
                for name in archive.namelist():
                    if not name.endswith('/') and (destination / name).read_bytes() != archive.read(name):
                        raise AssertionError('Installed payload differs from independent archive: ' + identity + '/' + name)
        product_skill = (
            project
            / ".agents/skills/speckit-program-kit-governance-product-intake/SKILL.md"
        )
        if not product_skill.is_file():
            raise AssertionError("Program Kit product-intake skill was not installed")
        for command in manifest['provides']['commands']:
            skill = project / '.agents/skills' / command['name'].replace('.', '-') / 'SKILL.md'
            installed_source = project / '.specify/extensions/program-kit-governance' / command['file']
            if not skill.is_file() or installed_source.read_bytes() != (extracted_extension / command['file']).read_bytes():
                raise AssertionError('Native command registration differs from archive: ' + command['name'])
        for name in RETIRED_COMMANDS:
            if (project / f'.agents/skills/speckit-program-kit-governance-{name}').exists():
                raise AssertionError('Retired command was registered as a native skill: ' + name)
        c4_view_skill = project / ".agents/skills/speckit-program-kit-governance-view-c4/SKILL.md"
        if not c4_view_skill.is_file():
            raise AssertionError("C4 projection viewing skill was not installed")
        grilling_skill = project / ".agents/skills/speckit-program-kit-governance-grilling/SKILL.md"
        if not grilling_skill.is_file():
            raise AssertionError("Decision grilling skill was not installed")
        feature_intake_skill = project / ".agents/skills/speckit-program-kit-governance-specification-intake/SKILL.md"
        if not feature_intake_skill.is_file():
            raise AssertionError("Mandatory feature intake skill was not installed")
        grilling_reference = (
            ".specify/extensions/program-kit-governance/commands/"
            "speckit.program-kit-governance.grilling.md"
        )
        if "shipped grilling skill" not in product_skill.read_text(encoding="utf-8"):
            raise AssertionError("Installed intake lost its Program Kit grilling dependency")
        if "shipped grilling skill" not in feature_intake_skill.read_text(encoding="utf-8"):
            raise AssertionError("Installed feature intake lost its Program Kit grilling dependency")
        shipped_grilling = project / grilling_reference
        expected_grilling = extracted_extension / "commands/speckit.program-kit-governance.grilling.md"
        if shipped_grilling.read_bytes() != expected_grilling.read_bytes():
            raise AssertionError("Installed intake resolves a different grilling contract")
        method_body = shipped_grilling.read_text(encoding="utf-8").split("---", 2)[2].strip()
        if method_body not in grilling_skill.read_text(encoding="utf-8"):
            raise AssertionError("Standalone grilling and intake do not share the shipped method")
        c4_view_skill_text = c4_view_skill.read_text(encoding="utf-8")
        if 'generated, read-only review projection' not in c4_view_skill_text:
            raise AssertionError("Installed C4 viewer skill lost its read-only projection boundary")
        installed_skill_text = product_skill.read_text(encoding="utf-8")
        if 'product_intake.py' not in installed_skill_text:
            raise AssertionError('Installed product-intake skill lost its mechanical entrypoint')
        if 'references/functional-discovery.md' not in installed_skill_text:
            raise AssertionError('Installed intake does not route functional discovery before convergence')
        functional = project/'.specify/extensions/program-kit-governance/references/functional-discovery.md'
        if functional.read_bytes() != (extracted_extension/'references/functional-discovery.md').read_bytes():
            raise AssertionError('Installed functional discovery differs from the packaged contract')
        specification = (project/'.agents/skills/speckit-program-kit-governance-specification-intake/SKILL.md').read_text(encoding='utf-8')
        if 'product intent' not in specification or 'relevant ADRs' not in specification:
            raise AssertionError('Installed specification intake cannot carry authored product knowledge forward')

        installed_scripts = project / '.specify/extensions/program-kit-governance/scripts'
        installed_check(project, installed_scripts / 'governance_state.py', 'validate-installation')
        registry_path = project / '.specify/presets/.registry'
        original_registry = registry_path.read_bytes()
        registry = json.loads(original_registry)
        registry['presets']['program-kit-governance-preset']['version'] = '0.0.0'
        registry_path.write_text(json.dumps(registry) + '\n', encoding='utf-8')
        before_mismatch = snapshot(project)
        try:
            refusal = installed_check(project, installed_scripts / 'governance_state.py',
                                      'validate-installation', expected=1)
            if 'version' not in (refusal.stdout + refusal.stderr).lower():
                raise AssertionError('Coherence failure did not identify the version mismatch')
            if snapshot(project) != before_mismatch:
                raise AssertionError('Coherence refusal changed the consumer')
        finally:
            registry_path.write_bytes(original_registry)
        # Verify the actual copied native outputs, including refusal to overwrite
        # consumer customization. The existing owner replays registered sources.
        from local_bundle_fixture import verify_release_copies
        verify_release_copies(project, release)

        # Reuse only the exact prepared project-local schema dependency. This
        # fixture never acquires or changes a device interpreter/toolchain.
        sys.path.insert(0, str(extracted_extension / 'scripts'))
        import schema_runtime
        runtime = schema_runtime.runtime_path(root)
        if not (runtime / '.ready').is_file():
            raise RuntimeError('SCHEMA_RUNTIME_MISSING: prepare the exact project dependency before this fixture')
        shutil.copytree(runtime, schema_runtime.runtime_path(project))
        installed_check(project, installed_scripts / 'schema_runtime.py', 'record-copy')
        installed_check(project, installed_scripts / 'product_intake.py', '--help')
        before_intake = snapshot(project)
        status = installed_check(project, installed_scripts / 'product_intake.py', 'status')
        payload = json.loads(status.stdout)
        if payload.get('status') != 'NO RECORDED CONTEXT' or not payload.get('next_action') or 'eligible' in payload:
            raise AssertionError('Clean installed inspection did not report its actual non-authorizing context')
        if snapshot(project) != before_intake:
            raise AssertionError('Installed product-intake status changed the consumer')

        consumer_architecture = project / 'docs/architecture'
        consumer_architecture.mkdir(parents=True)
        (consumer_architecture / 'project-intent.md').write_text(
            '# Request service\nA requester records and follows a request.\n'
            'Product confirmation remains pending human review.\n', encoding='utf-8')
        shutil.copyfile(extracted_extension / 'references/architecture-map-minimal.json',
                        consumer_architecture / 'architecture-map.json')
        installed_check(project, installed_scripts / 'architecture_map.py', 'export',
            '--map', 'docs/architecture/architecture-map.json', '--output', 'docs/architecture/workspace.dsl')
        before_map_review = snapshot(project)
        result = installed_check(project, installed_scripts / 'c4_view.py', 'inspect',
            '--project-root', '.', '--json')
        viewed = json.loads(result.stdout)
        if (viewed.get('review_mode') != 'authored-map-review'
                or viewed.get('intake_status') != 'not-required'
                or viewed.get('repository_writes') is not False
                or viewed.get('confirmation_performed') is not False
                or viewed.get('architecture_acceptance_performed') is not False):
            raise AssertionError('Installed C4 inspection manufactured authoring authority: ' + str(viewed))
        installed_check(project, installed_scripts / 'product_intake.py', 'inspect')
        if snapshot(project) != before_map_review:
            raise AssertionError('Installed read-only context/map review changed authored input')

        extension_config = yaml.safe_load(
            (project / ".specify/extensions.yml").read_text(encoding="utf-8")
            )
        if not (
            project
            / ".specify/extensions/program-kit-governance/references/intake-artifacts.md"
        ).is_file():
            raise AssertionError("Installed product-intake skill is missing its compact authoring contract")
        deployed_config = (
            project
            / ".specify/extensions/program-kit-governance/program-kit-governance-config.yml"
        )
        if not deployed_config.is_file():
            raise AssertionError("Program Kit configuration template was not scaffolded")
        hooks = set(extension_config.get("hooks", {}))
        if hooks != EXPECTED_HOOKS:
            raise AssertionError(f"Registered hooks {sorted(hooks)} != {sorted(EXPECTED_HOOKS)}")
        if extension_config.get("settings", {}).get("auto_execute_hooks") is not True:
            raise AssertionError("Program Kit requires auto_execute_hooks=true")
        expected_order = {
            "before_specify": ["speckit.program-kit-governance.architecture-check", "speckit.program-kit-governance.specification-intake"],
            "after_specify": ["speckit.clarify", "speckit.program-kit-governance.architecture-check"],
            "before_plan": ["speckit.program-kit-governance.phase-context"],
            "after_plan": ["speckit.program-kit-governance.architecture-check"],
            "before_tasks": ["speckit.program-kit-governance.phase-context"],
            "after_tasks": ["speckit.program-kit-governance.architecture-check", "speckit.analyze"],
            "before_implement": ["speckit.program-kit-governance.implementation-check"],
            "after_implement": ["speckit.program-kit-governance.architecture-check"],
        }
        for event, commands in expected_order.items():
            program_kit_hooks = [
                hook for hook in extension_config["hooks"][event]
                if hook.get("extension") == "program-kit-governance"
            ]
            if [hook.get("command") for hook in program_kit_hooks] != commands:
                raise AssertionError(f"{event} hooks are not ordered deterministically: {program_kit_hooks}")
            if any(
                hook.get("enabled") is not True
                or hook.get("optional") is not False
                or hook.get("condition") is not None
                for hook in program_kit_hooks
            ):
                raise AssertionError(f"{event} hooks are not mandatory and unconditional")
        consumer_hooks = [
            hook for hook in extension_config["hooks"]["after_specify"]
            if hook.get("extension") == "consumer-extension"
        ]
        if len(consumer_hooks) != 1:
            raise AssertionError("repeated Program Kit installation lost or duplicated unrelated hooks")
        # Exercise the installed core resolver, not just the upstream overlay files.
        expected_templates = {
            'constitution-template': ('## Core Principles', '### Verification selected by risk',
                                      'without AI, toolkit extensions or governance history'),
            'spec-template': ('## User Scenarios & Testing', '**Independent Test**',
                              '**Given**', '**When**', '**Then**',
                              'Retain applicable tests required by the'),
            'tasks-template': ('## Phase', '- [ ]', '## Program Kit vertical delivery notes',
                               'agreed review pauses', 'Do not infer acceptance'),
        }
        for template, markers in expected_templates.items():
            resolved = subprocess.run([sys.executable, '-X', 'utf8', str(python_resolver), template, '--json'],
                                      cwd=project, capture_output=True, text=True, encoding='utf-8')
            if resolved.returncode:
                raise AssertionError(f'Installed {template} resolution failed: {resolved.stderr}')
            content = json.loads(resolved.stdout)['TEMPLATE_CONTENT']
            if any(marker not in content for marker in markers):
                raise AssertionError(f'Installed {template} lost core structure or engineering guidance')
        preset_manifest = yaml.safe_load((extracted_preset / 'preset.yml').read_text(encoding='utf-8'))
        if any(item.get('strategy') != 'append' for item in preset_manifest['provides']['templates']):
            raise AssertionError('Preset replaced native commands or templates')
        for name, marker in (('tasks', '## Program Kit task guidance'),
                             ('implement', '## Program Kit implementation guidance'),
                             ('analyze', '## Program Kit operation review')):
            installed = (project / f'.agents/skills/speckit-{name}/SKILL.md').read_text(encoding='utf-8')
            if installed.count(marker) != 1 or 'task_draft.py' in installed:
                raise AssertionError('Installed native phase lost appended guidance or retained task-state engine: ' + name)
            for hook in (f'hooks.before_{name}', f'hooks.after_{name}'):
                if hook not in installed:
                    raise AssertionError('Native phase lost configured hook dispatch: ' + hook)
        implementation = (project / '.agents/skills/speckit-implement/SKILL.md').read_text(encoding='utf-8')
        if 'Pause dependent product work until actual acceptance' not in implementation:
            raise AssertionError('Installed implementation lost agreed human review boundary')
        if "program-kit-dotnet" not in extension_config.get("installed", []):
            raise AssertionError("Program Kit .NET extension was not registered")
        if "program-kit-building-blocks" not in extension_config.get("installed", []):
            raise AssertionError("Program Kit building-block extension was not registered")
        if not (
            project / ".agents/skills/speckit-program-kit-governance-sync/SKILL.md"
        ).is_file():
            raise AssertionError("Governance sync command was not installed as a namespaced skill")
        if not (
            project / ".agents/skills/speckit-program-kit-building-blocks-sync/SKILL.md"
        ).is_file():
            raise AssertionError("Building-block sync command was not installed as a namespaced skill")

        if (project / '.specify/workflows/program-kit-bootstrap').exists():
            raise AssertionError('Retired workflow was installed')
        assert (project / '.agents/skills/speckit-program-kit-governance-product-intake/SKILL.md').is_file()

        # The native bundle record was created from these exact four archives;
        # catalog transport is covered separately by the candidate install check.
        with zipfile.ZipFile(bundle_zip, "r") as archive:
            packaged_bundle = yaml.safe_load(archive.read("bundle.yml"))
        with zipfile.ZipFile(tooling_zip, "r") as archive:
            if "scripts/upgrade_program_kit.py" not in archive.namelist():
                raise AssertionError("Full Program Kit release is missing the offline/local updater")
            if "scripts/invoke_specify.py" not in archive.namelist():
                raise AssertionError("Full Program Kit release is missing the sandbox-compatible Specify bridge")
        component_graph = {
            (kind, entry["id"])
            for kind, entries in packaged_bundle["provides"].items()
            for entry in entries
        }
        if component_graph != {
            ("extensions", "program-kit-governance"),
            ("extensions", "program-kit-building-blocks"),
            ("extensions", "program-kit-dotnet"),
            ("presets", "program-kit-governance-preset"),
        }:
            raise AssertionError(f"Unexpected packaged bundle component graph: {component_graph}")
        for kind, entries in packaged_bundle['provides'].items():
            if any(entry.get('version') != version for entry in entries):
                raise AssertionError('Bundle component pins differ from the release version: ' + kind)

    print("Packaged component and bundle install test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
