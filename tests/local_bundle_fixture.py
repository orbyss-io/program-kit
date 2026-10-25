"""Native bundle ownership with explicitly local component transports for fixtures."""
from pathlib import Path
import sys
import importlib.util
import os
import uuid


def install_local_bundle(project, release, bridge, run, component_sources=None, integration='codex'):
    """run(label, argv) executes a real CLI child in the owned project and checks it.

    component_sources optionally maps (plural kind, component id) to an extracted
    component directory. Core retains planning, pin checks and record ownership.
    """
    from specify_cli._assets import get_speckit_version
    from specify_cli.bundles.adapters import DefaultPrimitiveInstaller
    from specify_cli.bundles.installer import install_bundle
    from specify_cli.bundles.manifest import BundleManifest
    from specify_cli.bundles.resolver import resolve_install_plan
    from owned_fixture import native_path

    project, release = Path(project), Path(release)
    manifest = BundleManifest.from_file(release / 'bundle.yml')
    plan = resolve_install_plan(manifest, speckit_version=get_speckit_version(), active_integration=integration)

    class LocalInstaller(DefaultPrimitiveInstaller):
        def install(self, root, component):
            assert Path(root).resolve() == project.resolve(), 'Native installer changed its fixture target'
            source = (component_sources or {}).get((component.kind, component.id),
                release / component.kind / component.id)
            if component.kind == 'extensions':
                # Release consumers receive copied native outputs. --dev means
                # linked registration on POSIX and tests a different mechanism.
                adapter = release / 'scripts/install_local_extension.py'
                if not adapter.is_file():
                    adapter = Path(bridge[1]).with_name('install_local_extension.py')
                command = [sys.executable, adapter, '--target', project, '--source', source,
                           '--extension', component.id]
                if '--site-packages' in bridge:
                    command += ['--site-packages', bridge[bridge.index('--site-packages') + 1]]
                run('install-' + component.id, command)
                return
            arguments = {
                'presets': ['preset', 'add', '--dev', native_path(source)],
                'workflows': ['workflow', 'add', native_path(source), '--dev'],
            }[component.kind]
            run('install-' + component.id, [*bridge, *arguments])

    return install_bundle(project, plan, LocalInstaller(allow_network=False), manifest=manifest)


def verify_release_copies(project, release):
    """Actual copied registrations still reject consumer edits and native aliases."""
    sys.path.insert(0, str(release / 'scripts'))
    spec = importlib.util.spec_from_file_location('preview_copy_ownership', release / 'scripts/upgrade_program_kit.py')
    ownership = importlib.util.module_from_spec(spec); spec.loader.exec_module(ownership)
    plan = ownership.preflight(project, release, release)
    assert plan['fromVersion'] == plan['toVersion']
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location('preview_copy_profiles', release / 'extensions/program-kit-governance/scripts/render_profile.py')
    profiles = module_from_spec(spec); spec.loader.exec_module(profiles)
    records, _ = profiles.history(project)
    relative = next(name for row in records for name in row['outputs']
                    if 'program-kit-governance' in name and name.endswith('SKILL.md'))
    output = project / relative
    original = output.read_bytes()
    customized = original + b'\nConsumer native-output customization must survive refusal.\n'
    output.write_bytes(customized)
    try:
        try:
            ownership.preflight(project, release, release)
        except ownership.UpgradeError as error:
            assert 'customized' in str(error)
        else:
            raise AssertionError('Native copied-output customization was admitted')
        assert output.read_bytes() == customized
    finally:
        output.write_bytes(original)
