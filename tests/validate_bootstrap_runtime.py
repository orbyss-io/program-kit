"""Real published host compatibility. No coding agent or consumer mutation."""
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from repository_sync import audit_toolchain, provider, write

IMAGE = 'ghcr.io/orbyss-io/foundation-host@sha256:622353f8c3888ae173819abad493ecde786307e72f661cdfa3bf3afa84cf6cde'


def main():
    # The runtime recipe intentionally uses --pull=never. Provision its exact
    # digest here instead of depending on a warm developer Docker cache.
    subprocess.run(['docker', 'pull', IMAGE], check=True, timeout=300)
    target = ROOT / 'artifacts/bootstrap-runtime' / uuid.uuid4().hex[:8]
    shutil.copytree(ROOT / 'extensions/program-kit-governance/examples/bootstrap-runtime', target)
    template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
    for name in ['global.json', 'NuGet.config']:
        shutil.copyfile(template / name, target / name)
    shutil.copyfile(ROOT / 'extensions/program-kit-governance/scripts/compatibility_process.py', target / 'bounded_process.py')
    write(target / 'runtime-inputs.json', {'hostImage': IMAGE, 'foundationRelease': '0.2.2'})
    audit_toolchain(target, {'dotnet': '10.0.202'})
    executor = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    plan = {'schemaVersion': 1, 'targets': [{'path': p, 'packages': [{'materializationKind': 'nuget-project'}]} for p in
            ['Core/Core.csproj', 'Feature/Feature.csproj', 'Boundary/Boundary.csproj']], 'registryRequirements': []}
    lock = target / '.program-kit/sync/dependencies.json'
    write(lock, plan)
    request = target / '.program-kit/evidence/building-block-restore-request.json'
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
    print('Runtime evidence: ' + str(target))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
