"""Native bundle ownership with explicitly local component transports for fixtures."""
from pathlib import Path


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
            arguments = {
                'extensions': ['extension', 'add', native_path(source), '--dev'],
                'presets': ['preset', 'add', '--dev', native_path(source)],
                'workflows': ['workflow', 'add', native_path(source), '--dev'],
            }[component.kind]
            run('install-' + component.id, [*bridge, *arguments])

    return install_bundle(project, plan, LocalInstaller(allow_network=False), manifest=manifest)
