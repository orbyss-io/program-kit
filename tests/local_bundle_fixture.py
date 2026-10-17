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
    spec = importlib.util.spec_from_file_location('release_copy_ownership', release / 'scripts/native_phase_ownership.py')
    ownership = importlib.util.module_from_spec(spec); spec.loader.exec_module(ownership)
    admitted = ownership.preflight(project, release)
    assert admitted['outputs'] and all(not (project / row['path']).is_symlink() for row in admitted['outputs'])
    assert not list((project / '.specify/extensions').rglob('.specify-dev'))
    output = project / next(row['path'] for row in admitted['outputs']
                            if row['extension'] == 'program-kit-governance' and row['path'].endswith('SKILL.md'))
    original = output.read_bytes()
    customized = original + b'\nConsumer native-output customization must survive refusal.\n'
    output.write_bytes(customized)
    try:
        try:
            ownership.preflight(project, release)
        except ownership.OwnershipError as error:
            assert 'consumer customization' in str(error)
        else:
            raise AssertionError('Native copied-output customization was admitted')
        assert output.read_bytes() == customized
    finally:
        output.write_bytes(original)
    if os.name != 'nt':
        # Real POSIX symlinks reproduce the mechanism Windows may silently copy.
        target = project / '.program-kit' / ('alias-probe-' + uuid.uuid4().hex)
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(original)
        output.unlink(); output.symlink_to(os.path.relpath(target, output.parent))
        try:
            try:
                ownership.preflight(project, release)
            except ownership.OwnershipError as error:
                assert 'symlinked' in str(error)
            else:
                raise AssertionError('Native aliased output was admitted')
            assert output.is_symlink() and target.read_bytes() == original
        finally:
            output.unlink(); output.write_bytes(original); target.unlink()
