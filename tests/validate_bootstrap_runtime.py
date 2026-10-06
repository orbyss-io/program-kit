"""Real published host compatibility. No coding agent or consumer mutation."""
import argparse
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from repository_sync import audit_toolchain, provider, write

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, help='Exact candidate profile; otherwise exercise the qualified default.')
    parser.add_argument('--catalog', type=Path, help='Explicit target catalog for the exact candidate profile.')
    args = parser.parse_args()
    if args.catalog is not None and args.profile is None:
        parser.error('--catalog requires an explicit --profile')
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
    import building_blocks as blocks
    from public_availability import verify_oci
    catalog = (blocks.materialize_dependency_profile(blocks.load_json(args.catalog or blocks.default_catalog(Path(blocks.__file__))),
               blocks.load_json(args.profile)) if args.profile else blocks.new_project_catalog())
    host = catalog['packages']['oci:ghcr.io/orbyss-io/foundation-host']
    image = verify_oci(host, catalog['sources'][host['source']])['reference']
    # The runtime recipe intentionally uses --pull=never. Provision its exact
    # digest here instead of depending on a warm developer Docker cache.
    subprocess.run(['docker', 'pull', image], check=True, timeout=300)
    target = ROOT / 'artifacts/bootstrap-runtime' / uuid.uuid4().hex[:8]
    shutil.copytree(ROOT / 'extensions/program-kit-governance/examples/bootstrap-runtime', target)
    template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
    for name in ['global.json', 'NuGet.config']:
        shutil.copyfile(template / name, target / name)
    shutil.copyfile(ROOT / 'extensions/program-kit-governance/scripts/compatibility_process.py', target / 'bounded_process.py')
    # Retarget only this disposable fixture. The installed historical example
    # and all consumer projects retain their original reviewed inputs.
    for project in target.rglob('*.csproj'):
        value = ET.parse(project)
        for reference in value.iter('PackageReference'):
            package = catalog['packages'].get('nuget:' + reference.get('Include', ''))
            if package:
                reference.set('Version', package['version'])
        value.write(project, encoding='utf-8', xml_declaration=True)
    inputs = {'hostImage': image, 'foundationRelease': catalog['families']['foundation']['releaseVersion'],
              'catalogResolutionSha256': blocks.catalog_resolution_sha256(catalog)}
    write(target / 'runtime-inputs.json', inputs)
    audit_toolchain(target, {'dotnet': '10.0.202'})
    executor = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    plan = {'schemaVersion': 1, 'targets': [{'path': p, 'packages': [{'materializationKind': 'nuget-project'}]} for p in
            ['Core/Core.csproj', 'Feature/Feature.csproj', 'Boundary/Boundary.csproj']], 'registryRequirements': []}
    lock = target / '.program-kit/sync/dependencies.json'
    write(lock, plan)
    request = target / 'artifacts/program-kit/building-block-restore-request.json'
    for mode in ('renew', 'locked'):
        write(request, executor.restore_request(target, lock, plan, mode))
        with (target / (mode + '.log')).open('w', encoding='utf-8') as log:
            result = subprocess.run([sys.executable, str(executor.__file__), mode, '--target', str(target), '--lock', lock.relative_to(target).as_posix(),
                '--request', request.relative_to(target).as_posix(), '--approved'], cwd=target, stdout=log, stderr=subprocess.STDOUT, timeout=300)
        if result.returncode:
            raise RuntimeError('Restore failed: ' + str(target / (mode + '.log')))
    with (target / 'runtime.log').open('w', encoding='utf-8') as log:
        result = subprocess.run([sys.executable, 'runtime_probe.py'], cwd=target, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    if result.returncode:
        print((target / 'runtime.log').read_text(encoding='utf-8', errors='replace')[-12000:])
    else:
        cases = ET.parse(target / 'compatibility-results.xml').getroot()
        if cases.findall('.//failure') or cases.findall('.//error') or len(cases.findall('testcase')) != 5:
            raise ValueError('Published host fixture did not establish all five compatibility cases')
        write(target / 'qualification-result.json', {'satisfied': True, 'inputs': inputs,
            'cases': sorted(case.get('classname') + '.' + case.get('name') for case in cases.findall('testcase')),
            'resultsSha256': blocks.raw_sha256(target / 'compatibility-results.xml')})
    print('Runtime evidence: ' + str(target))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
