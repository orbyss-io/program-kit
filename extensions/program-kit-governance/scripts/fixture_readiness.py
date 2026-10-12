"""Bounded read-only preparation before a fixture creates dependent effects."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def plan(root, pins, contract=None):
    targets = (contract or {}).get('dependencyTargets', [])
    tools = set(pins.get('requiredTools', []))
    if any(Path(path).suffix == '.csproj' for path in targets):
        tools.add('dotnet')
    if any(Path(path).name == 'package.json' for path in targets):
        tools.update(('node', 'npm'))
    images = sorted({pins[key] for key in ('hostImage', 'identityImage', 'image') if pins.get(key)})
    browsers = sorted(set(pins.get('requiredBrowsers', [])))
    if pins.get('identityImage'):
        browsers = sorted(set(browsers) | {'chromium'})
        tools.update(('node', 'npm', 'dotnet'))
    if pins.get('hostImage') or pins.get('profile') == 'ef-postgresql':
        tools.add('dotnet')
    if any(not isinstance(image, str) or not re.fullmatch(r'[^\s@]+@sha256:[a-f0-9]{64}', image) for image in images):
        raise ValueError('PKP604 fixture images require exact immutable digests; repair the accepted recipe')
    if set(browsers) - {'chromium', 'firefox', 'webkit'} or tools - {'dotnet', 'node', 'npm'}:
        raise ValueError('PKP600 unsupported fixture requirements; declare a bounded preparation adapter')
    return {'schemaVersion': 1, 'tools': sorted(tools), 'images': images, 'browsers': browsers,
            'deviceInstallations': 'user-terminal-only', 'effects': 'read-only prerequisites; browser launch/close only'}


def check(root, pins, contract=None, runner=None, environment=None):
    runner = runner or subprocess.run
    root = Path(root).resolve()
    requirements = plan(root, pins, contract)
    record = root / 'artifacts/program-kit/toolchain.json'
    tools = json.loads(record.read_text(encoding='utf-8')) if record.is_file() else {}
    observed = {'python': {'executable': sys.executable, 'version': '.'.join(map(str, sys.version_info[:3]))},
                'tools': {}, 'images': [], 'browsers': []}
    if sys.version_info < (3, 11):
        raise ValueError('PKP600 fixture Python >=3.11 is required; select the recorded installed runtime')
    def run(command):
        try:
            return runner(command, cwd=root, env=environment, capture_output=True, text=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError('PKP600 prerequisite command is unavailable/timed out: ' + str(command[0])) from error
    for name in requirements['tools']:
        command = tools.get('commands', {}).get(name)
        required = tools.get('required', {}).get(name)
        if not isinstance(command, list) or not command or not isinstance(command[0], str) or not Path(command[0]).is_absolute() or not Path(command[0]).is_file() or not required:
            raise ValueError('PKP600 missing/stale recorded ' + name + ' executable; repair device selection and rerun supported toolchain readiness in the user terminal')
        result = run([*command, '--version'])
        actual = (result.stdout or '').strip().removeprefix('v')
        if result.returncode or actual != required:
            raise ValueError('PKP600 current ' + name + ' version differs from the exact recipe toolchain; repair selection and rerun readiness before this fixture')
        observed['tools'][name] = {'command': command, 'version': actual}
    # Start/close only the required empty browser before Docker can create anything.
    # Public Playwright launch checks the actual headless executable and support
    # libraries, rather than mistaking the full-browser executablePath for readiness.
    for browser in requirements['browsers']:
        command = tools.get('commands', {}).get('node')
        if not command:
            raise ValueError('PKP600 browser preparation needs the exact recorded Node command')
        probe = "(async()=>{const b=await require('playwright')." + browser + ".launch({headless:true});await b.close();process.stdout.write('ready')})().catch(()=>{process.exitCode=1})"
        result = run([*command, '-e', probe])
        if result.returncode or result.stdout.strip() != 'ready':
            raise ValueError('PKP605 required ' + browser + ' browser/headless binaries or support libraries are unavailable before container creation. In the user terminal run the exact-runtime npm exec -- playwright install ' + browser + ', then rerun this readiness check. This does not complete a product browser journey.')
        observed['browsers'].append(browser)
    if requirements['images']:
        docker = shutil.which('docker')
        if not docker or not Path(docker).is_file():
            raise ValueError('PKP601 Docker client is missing; complete device installation in the user terminal and rerun readiness')
        engine = run([docker, 'info', '--format', '{{json .}}'])
        if engine.returncode:
            detail = (engine.stderr or '').lower()
            if any(text in detail for text in ('permission denied', 'access is denied', 'access denied')):
                raise ValueError('PKP602 Docker engine/socket access denied; repair user access or authorize the exact fixture process boundary')
            raise ValueError('PKP601 Docker engine is unavailable; start the selected Linux engine in the user terminal')
        try:
            info = json.loads(engine.stdout)
        except (TypeError, ValueError) as error:
            raise ValueError('PKP601 Docker engine returned invalid readiness metadata') from error
        if info.get('OSType') != 'linux':
            raise ValueError('PKP601 fixture requires a Docker Linux engine; select it in the user terminal')
        observed['docker'] = {'executable': docker, 'version': info.get('ServerVersion'), 'os': 'linux'}
        for image in requirements['images']:
            inspection = run([docker, 'image', 'inspect', image, '--format', '{{json .}}'])
            if inspection.returncode:
                tag = image.split('@')[0]
                tagged = run([docker, 'image', 'inspect', tag, '--format', '{{json .}}'])
                if tagged.returncode == 0:
                    raise ValueError('PKP604 local image tag has a different digest; acquire the exact accepted reference: ' + image)
                raise ValueError('PKP603 exact fixture image is absent; provision before behavior with docker pull ' + image)
            value = json.loads(inspection.stdout)
            expected = image.split('@', 1)[1]
            if value.get('Os') != 'linux' or not any(reference.endswith('@' + expected) for reference in value.get('RepoDigests', [])):
                raise ValueError('PKP604 inspected image does not establish the exact accepted Linux digest: ' + image)
            observed['images'].append({'reference': image, 'id': value.get('Id')})
    return {'requirements': requirements, 'observed': observed, 'ready': True}
