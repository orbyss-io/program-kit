"""Seal a locally refreshed kit through Spec Kit's native bundle installer API."""
import argparse
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-root',type=Path,required=True)
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--integration',required=True)
    parser.add_argument('--site-packages',type=Path)
    args=parser.parse_args()
    if args.site_packages: sys.path.insert(0,str(args.site_packages.resolve(strict=True)))
    from specify_cli._assets import get_speckit_version
    from specify_cli.bundles import BundlerError
    from specify_cli.bundles.adapters import DefaultPrimitiveInstaller
    from specify_cli.bundles.installer import install_bundle
    from specify_cli.bundles.manifest import BundleManifest
    from specify_cli.bundles.project import active_integration
    from specify_cli.bundles.resolver import resolve_install_plan
    from specify_cli.bundles.versioning import same_version

    class RefreshedLocalInstaller(DefaultPrimitiveInstaller):
        # All component installation has already used the public native CLI.
        # Core still owns pin checks, conflicts, ownership and record atomicity.
        def install(self,root,component):
            raise BundlerError('Local component is missing before bundle sealing: '+component.id)

        def refresh(self,root,component):
            actual=self.installed_version(root,component)
            if not actual or not component.version or not same_version(actual,component.version):
                raise BundlerError('Local component does not match its bundle pin: '+component.id)

    root=args.target.resolve(strict=True)
    manifest=BundleManifest.from_file(args.release_root.resolve(strict=True)/'bundle.yml')
    detected=active_integration(root)
    plan=resolve_install_plan(manifest,speckit_version=get_speckit_version(),
        active_integration=detected or args.integration,integration_explicit=detected is None)
    expected={('extensions','program-kit-governance'),('extensions','program-kit-building-blocks'),
              ('extensions','program-kit-dotnet'),('presets','program-kit-governance-preset'),
              ('workflows','program-kit-bootstrap')}
    if plan.bundle_id!='program-kit' or {(item.kind,item.id) for item in plan.components}!=expected:
        raise BundlerError('Local sealing accepts only the exact Program Kit component set')
    result=install_bundle(root,plan,RefreshedLocalInstaller(allow_network=False),manifest=manifest,refresh=True)
    print('Native bundle ownership/pins sealed after local component refresh: '+result.bundle_id)


if __name__=='__main__': main()
