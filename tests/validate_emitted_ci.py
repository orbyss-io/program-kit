"""Execute the actual emitted CI commands after checking existing native prerequisites.

No device tool installation, service provisioning, coding agent or application
acceptance. CI itself provisions its runtimes; this local fixture verifies the
already installed selections and executes the emitted frontend and full CI gate.
"""
import hashlib
import importlib
import json
import os
from pathlib import Path
import shlex
import sys
import uuid
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture


def main():
    directory = ROOT / 'artifacts/tests/emitted-ci' / uuid.uuid4().hex[:8]; directory.mkdir(parents=True)
    result = {'status': 'running', 'scope': __doc__, 'deviceInstallationPerformed': False, 'applicationAcceptance': False}
    try:
        observed = foundation_fixture.captured([sys.executable, str(ROOT / 'tests/validate_composition_start.py'), '--foundation-only'],
            ROOT, directory / 'scaffold', timeout=600)
        if observed['exitCode'] or not observed['cleanupComplete'] or not observed['logsDrained']:
            raise ValueError('Current emitted CI scaffold failed; inspect ' + str(directory))
        actual = json.loads((directory / 'scaffold/stdout.log').read_bytes())
        root = (ROOT / actual['consumer']).resolve()
        if not root.is_relative_to(ROOT / 'artifacts/t') or actual['status'] != 'scaffolded':
            raise ValueError('CI proof requires its new owned consumer')
        workflow = root / '.github/workflows/application-ci.yml'; payload = workflow.read_bytes()
        steps = yaml.safe_load(payload)['jobs']['build']['steps']
        def step(name):
            matches = [row for row in steps if row['name'] == name]
            if len(matches) != 1: raise ValueError('Emitted CI step missing or ambiguous: ' + name)
            return matches[0]
        for name, pin in [('Set up .NET', 'global-json-file'), ('Set up managed Python', 'python-version-file'),
                          ('Set up managed Node', 'node-version-file')]:
            selected = step(name)['with'][pin]
            if not (root / selected).is_file(): raise ValueError('CI runtime pin is missing: ' + selected)
        step('Select managed npm')
        preparation = shlex.split(step('Prepare selected typed frontends')['run'])
        verification = shlex.split(step('Run repository verification gate')['run'])
        if preparation != ['python', 'eng/prepare_hosted_pages.py', '--repository', '.', '--restore']:
            raise ValueError('Unknown emitted frontend preparation command')
        if verification != ['./eng/Invoke-RepositoryVerification.ps1', '-Mode', 'CI']:
            raise ValueError('Unknown emitted CI verification command')
        device_python = os.environ.get('PROGRAMKIT_DEVICE_PYTHON') or sys.executable
        commands = [([device_python, *preparation[1:]], 'frontend'),
                    (['pwsh', '-NoProfile', '-File', *verification], 'verification')]
        for command, name in commands:
            observed = foundation_fixture.captured(command, root, directory / name, timeout=1200)
            if observed['exitCode'] or not observed['cleanupComplete'] or not observed['logsDrained']:
                raise ValueError('Actual emitted CI command failed at ' + name + '; inspect ' + str(directory))
        inventories = list((root / 'artifacts/packages').rglob('program-kit-pack.json'))
        if not inventories or not (root / 'artifacts/tests/architecture.xml').is_file():
            raise ValueError('Actual CI gate did not produce native pack/architecture evidence')
        result.update(status='passed', consumer=root.relative_to(ROOT).as_posix(),
            workflowSha256=hashlib.sha256(payload).hexdigest(), commands=[command for command, _ in commands],
            packInventories=[p.relative_to(root).as_posix() for p in inventories],
            prerequisiteProvisioning='CI-owned setup remains CI execution; local run uses actual existing selected runtimes')
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error)); raise
    finally:
        (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print('Actual emitted CI command proof: ' + str(directory / 'results.json'))


if __name__ == '__main__': main()
