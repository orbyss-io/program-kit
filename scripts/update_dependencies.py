"""Validate an automatic repository update; never starts a coding agent or publishes."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def run(name,arguments):
    output=ROOT/'artifacts/dependency-update-tests'; output.mkdir(parents=True,exist_ok=True)
    path=output/(name+'.log')
    with path.open('w',encoding='utf-8') as log:
        result=subprocess.run(arguments,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=False)
    if result.returncode:
        print(path.read_text(encoding='utf-8', errors='replace')[-12000:], flush=True)
        raise RuntimeError(name+' failed; '+str(path))
    print(name+' passed',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--development',action='store_true')
    parser.add_argument('--upgrade',action='store_true')
    parser.add_argument('--changed-from', help='Optional committed maintenance base; working changes are always included')
    parser.add_argument('--refresh-locks',action='store_true', help='Explicit lock maintenance, separate from validation')
    parser.add_argument('--engines',default='chromium,webkit' if os.name=='nt' else 'chromium,firefox,webkit')
    args=parser.parse_args()
    # Discovery/upgrades/profile qualification are deliberate maintenance. Merely
    # checking an update does not mutate lockfiles or demand unrelated SDKs.
    if args.upgrade or args.refresh_locks:
        import importlib.util
        source=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/scripts/device_toolchain.py'
        spec=importlib.util.spec_from_file_location('maintenance_device_policy',source)
        policy=importlib.util.module_from_spec(spec); spec.loader.exec_module(policy)
        policy.contributor(ROOT)
        if args.upgrade:
            run('upgrade',[sys.executable,'scripts/dependency_maintenance.py','upgrade'])
            policy.contributor(ROOT)
            run('profile',[sys.executable,'scripts/update_dependency_profiles.py','update','--engines='+args.engines])
        npm=policy.executable('npm.cmd' if os.name=='nt' else 'npm',ROOT)
        if npm is None: raise ValueError('PKT030 active shared npm selection changed; refresh and rerun readiness.')
        for label, relative in (
            ('web-acceptance', 'extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/eng/web'),
            ('hosted-pages', 'extensions/program-kit-dotnet/templates/dotnet/hosted-pages/web'),
            ('ui-acceptance', 'extensions/program-kit-governance/templates/ui-experience/acceptance')):
            run('lock-'+label,[str(npm), 'install','--package-lock-only','--ignore-scripts',
                '--no-audit','--no-fund','--prefix',str(ROOT/relative)])
    arguments=[sys.executable,'scripts/run_validation.py','--suite','Integrity' if args.development else 'Affected',
               '--engines='+args.engines]
    if args.changed_from and not args.development:
        arguments.extend(['--changed-from',args.changed_from])
    run('deterministic-tests',arguments)


if __name__=='__main__': main()
