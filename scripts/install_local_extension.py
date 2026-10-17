"""Install a release extension through native copy registration, without dev links."""
from pathlib import Path
import argparse
import sys

EXTENSIONS = ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet')


def install(target, source, identity, force=False):
    target, source = Path(target).absolute(), Path(source).absolute()
    if identity not in EXTENSIONS or not (target / '.specify/integration.json').is_file():
        raise ValueError('Local extension copy requires an initialized consumer and a registered Program Kit extension')
    for path in (target, source, target / '.specify/integration.json', target / '.specify/extensions'):
        for item in (path, *path.parents):
            if item.is_symlink() or getattr(item, 'is_junction', lambda: False)():
                raise ValueError('Aliased local extension copy source/target requires explicit reconciliation')
    target, source = target.resolve(strict=True), source.resolve(strict=True)
    if source.is_relative_to(target) or not source.is_dir() or not (source / 'extension.yml').is_file():
        raise ValueError('Local release extension must be an ordinary source directory outside the consumer')
    # Reject linked inputs before native copytree can dereference them.
    if any(path.is_symlink() or getattr(path, 'is_junction', lambda: False)() for path in source.rglob('*')):
        raise ValueError('Aliased local release extension input requires explicit reconciliation')
    from specify_cli._assets import get_speckit_version
    from specify_cli.events import refresh_integration_events
    from specify_cli.extensions import ExtensionManager, ExtensionManifest
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'extensions/program-kit-governance/scripts'))
    import render_profile
    manifest = ExtensionManifest(source / 'extension.yml')
    if manifest.id != identity:
        raise ValueError('Local extension copy source differs from the selected Program Kit identity')
    manager = ExtensionManager(target)
    with render_profile.capture(target, ['extension', 'add', str(source)]):
        installed = manager.install_from_directory(source, get_speckit_version(), link_commands=False, force=force)
        # Preserve extension add's native event/config effects as well as its
        # registrations, hooks, compatibility checks and retained configuration.
        refresh_integration_events(target)
        _, _, failed = manager.scaffold_config(installed.id)
        if failed:
            raise ValueError('Local release extension configuration did not scaffold: ' + ', '.join(failed))
    print('Native extension installed with copied outputs: ' + installed.id + ' ' + installed.version)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--extension', choices=EXTENSIONS, required=True)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--site-packages', type=Path)
    args = parser.parse_args()
    if args.site_packages:
        site = args.site_packages.resolve(strict=True)
        if not args.site_packages.is_absolute() or not (site / 'specify_cli/__init__.py').is_file():
            raise ValueError('Local extension copy requires the exact installed Spec Kit package directory')
        sys.path.insert(0, str(site))
    install(args.target, args.source, args.extension, args.force)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
