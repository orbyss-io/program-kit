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
    parser.add_argument('--engines',default='chromium,webkit' if os.name=='nt' else 'chromium,firefox,webkit')
    args=parser.parse_args()
    # The same readiness gate runs before locks, profile qualification or tests.
    import importlib.util
    source=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng/device_toolchain.py'
    spec=importlib.util.spec_from_file_location('maintenance_device_policy',source)
    policy=importlib.util.module_from_spec(spec); spec.loader.exec_module(policy)
    policy.contributor(ROOT)
    if not args.development and os.name=='nt':
        parser.error('Complete update validation runs in Linux CI. Use the user-owned Release terminal described in AGENTS.md on Windows.')
    if args.upgrade:
        run('upgrade',[sys.executable,'scripts/dependency_maintenance.py','upgrade'])
        policy.contributor(ROOT)  # Updated pins may require a new human device selection.
        run('profile',[sys.executable,'scripts/update_dependency_profiles.py','update','--engines='+args.engines])
    for relative in ('extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/eng/web',
                     'extensions/program-kit-governance/templates/ui-experience/acceptance'):
        directory=ROOT/relative
        run('lock-'+directory.name,['npm.cmd' if os.name=='nt' else 'npm',
            'install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--prefix',str(directory)])
    run('schema-runtime',[sys.executable,'extensions/program-kit-governance/scripts/schema_runtime.py','setup'])
    arguments=[sys.executable,'scripts/run_validation.py','--suite','Development' if args.development else 'PullRequest',
               '--workers','1' if os.name=='nt' else '4','--engines='+args.engines]
    run('deterministic-tests',arguments)


if __name__=='__main__': main()
