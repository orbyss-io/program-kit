"""Actual released .NET component integration through the shared restore executor; no agent."""
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from repository_sync import audit_toolchain, provider, write


def main():
    destination = ROOT / 'artifacts/public-component-use' / uuid.uuid4().hex[:8]
    shutil.copytree(ROOT / 'tests/fixtures/knowledge-application/components', destination)
    template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
    shutil.copyfile(template / 'global.json', destination / 'global.json')
    # Replace the copied fixture config using the executor's exact case. Windows
    # otherwise retains the original directory-entry spelling after an overwrite.
    (destination / 'NuGet.Config').unlink()
    shutil.copyfile(template / 'NuGet.config', destination / 'NuGet.config')
    config_names = [p.name for p in destination.iterdir() if p.name.casefold() == 'nuget.config']
    if config_names != ['NuGet.config']:
        raise AssertionError(f'Restore fixture needs one exactly named NuGet.config: {config_names}')
    pins = json.loads((destination / 'global.json').read_text(encoding='utf-8'))
    audit_toolchain(destination, {'dotnet': pins['sdk']['version']})
    projects = ['ComponentProbe.csproj', 'hosted-pages/Probe.csproj', 'web-defaults/Probe.csproj']
    lock = destination / '.program-kit/sync/dependencies.json'
    plan = {'schemaVersion': 1, 'targets': [{'path': p, 'packages': [{'materializationKind': 'nuget-project'}]} for p in projects], 'registryRequirements': []}
    write(lock, plan)
    executor = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    request = destination / '.program-kit/evidence/building-block-restore-request.json'
    try:
        for mode in ('renew', 'locked'):
            write(request, executor.restore_request(destination, lock, plan, mode))
            with (destination / (mode + '.log')).open('w', encoding='utf-8') as stream:
                subprocess.run([sys.executable, str(executor.__file__), mode, '--target', str(destination), '--lock', lock.relative_to(destination).as_posix(),
                                '--request', request.relative_to(destination).as_posix(), '--approved'], cwd=destination, stdout=stream, stderr=subprocess.STDOUT,
                               check=True, timeout=600)
        executor.verify_evidence(destination, plan, json.loads((destination / '.program-kit/evidence/building-block-restore.json').read_text(encoding='utf-8')))
        for project in projects:
            name = Path(project).parent.name if '/' in project else 'forms-json'
            command = ['dotnet', 'run', '--project', project, '--no-restore']
            if project == projects[0]:
                command += ['--', 'results.xml']
            with (destination / (name + '.log')).open('w', encoding='utf-8') as stream:
                subprocess.run(command, cwd=destination, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=180)
    except subprocess.CalledProcessError:
        for log in sorted(destination.glob('*.log')):
            print(f'{log.name}:\n{log.read_text(encoding="utf-8", errors="replace")[-6000:]}', file=sys.stderr)
        print('Public component integration failed; preserved logs: ' + str(destination), file=sys.stderr)
        return 2
    print('Released Forms/JSON, real two-shell WebDefaults/JSON admission and HostedPages HTTP probes passed: ' + str(destination))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
