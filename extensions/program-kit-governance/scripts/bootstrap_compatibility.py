"""Scratch compatibility setup through repository sync's exact dependency executor.

No consumer product is scaffolded. A live supervisor owns credentialed restores;
workers can only submit a source-bound request for the generated scratch directory.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
import time
import uuid
import re
from contextlib import chdir
from pathlib import Path

import package_execution
from repository_sync import contained, context, audit_toolchain, provider, load, write, digest


def configuration(root: Path, *, dotnet: bool, npm: bool):
    """Derive scratch files from managed defaults or current assessment-approved pins."""
    template = package_execution.extension_root() / 'program-kit-dotnet/templates/dotnet/files'
    setup = context(root, 'bootstrap', None)
    pins = {key: value for key, value in setup['toolchainPins'].items() if key in {'node', 'npm'}} if npm else {}
    if npm and set(pins) != {'node', 'npm'}:
        raise ValueError('Compatibility requires an accepted JavaScript toolchain before npm provisioning')
    files = (['global.json', 'NuGet.config'] if dotnet else []) + (['.nvmrc', '.npm-version'] if npm else [])
    content = {name: (template / name).read_bytes() for name in files}
    decisions = load(root / 'docs/architecture/bootstrap-decisions.json', {})
    authority = decisions.get('toolchain', {})
    override = authority.get('source') == 'override'
    if override:
        governance = provider('program-kit-governance/scripts/governance_state.py')
        with chdir(root):
            governance.validate_assessment_approval()
    if dotnet:
        global_json = load(template / 'global.json')
        sdk = authority.get('pins', {}).get('dotnet-sdk') if override else global_json['sdk']['version']
        if not isinstance(sdk, str) or not re.fullmatch(r'\d+\.\d+\.\d+', sdk):
            raise ValueError('Compatibility requires an exact approved .NET SDK')
        pins['dotnet'] = sdk
        if sdk != global_json['sdk']['version']:
            global_json['sdk']['version'] = sdk
            content['global.json'] = (json.dumps(global_json, indent=2) + '\n').encode('utf-8')
    for name, key in (('.nvmrc', 'node'), ('.npm-version', 'npm')):
        if npm and content[name].decode('utf-8').strip() != pins[key]:
            content[name] = (pins[key] + '\n').encode('utf-8')
    return pins, content


def prepare(root: Path, scratch: Path, contract: dict):
    fixtures = contract.get('fixtures', {})
    if not isinstance(fixtures, dict):
        raise ValueError('Compatibility fixtures must map scratch-relative paths to repository-owned files')
    inputs = []
    for relative, source in fixtures.items():
        source_path = contained(root, source)
        destination = contained(scratch, relative)
        if not source_path.is_file() or not destination.is_relative_to(scratch):
            raise ValueError('Compatibility fixture input is missing or outside its scope')
        if destination.parts and any(part.lower() in {'.git', '.specify', '.program-kit', 'node_modules', 'bin', 'obj'} for part in Path(relative).parts):
            raise ValueError('Compatibility fixture cannot supply managed/cache content')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)
        inputs.append({'path': source, 'sha256': digest(source_path)})
    targets = contract.get('dependencyTargets', [])
    if not isinstance(targets, list) or len(targets) != len(set(targets)):
        raise ValueError('Compatibility dependencyTargets must be distinct fixture paths')
    if not targets:
        return inputs, None
    if any(relative not in fixtures for relative in targets):
        raise ValueError('Every compatibility dependency target needs a bound fixture source')
    dependencies = []
    dotnet = npm = False
    for relative in targets:
        path = contained(scratch, relative)
        if path.suffix == '.csproj':
            kind = 'nuget-project'
            dotnet = True
        elif path.name == 'package.json':
            kind = 'npm-dependency'
            npm = True
        else:
            raise ValueError('Compatibility dependency targets must be explicit csproj/package.json files')
        dependencies.append({'path': relative, 'packages': [{'materializationKind': kind}]})
    pins, content = configuration(root, dotnet=dotnet, npm=npm)
    for relative, payload in content.items():
        if relative.casefold() in {name.casefold() for name in fixtures}:
            raise ValueError('Toolchain/source overrides belong to accepted setup authority, not fixture files')
        (scratch / relative).write_bytes(payload)
    write(scratch / '.program-kit/sync/compatibility-pins.json', pins)
    plan = {'schemaVersion': 1, 'targets': dependencies, 'registryRequirements': []}
    write(scratch / '.program-kit/sync/dependencies.json', plan)
    return inputs, plan


def restore(root: Path, scratch: Path, *, timeout=600, stdout=None, stderr=None):
    tool = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    lock_path = scratch / '.program-kit/sync/dependencies.json'
    plan = load(lock_path)
    boundary = root / '.program-kit-live/worker-boundary.json'
    if boundary.is_file():
        requests = root / '.program-kit-live/bootstrap-restore'
        identity = uuid.uuid4().hex
        path = requests / (identity + '.request.json')
        request = {'schemaVersion': 1, 'scratch': scratch.relative_to(root).as_posix(),
                   'timeoutSeconds': timeout, 'lockSha256': digest(lock_path), 'inputDigest': package_execution.canonical_hash(tool.input_basis(scratch, plan))}
        write(path, request)
        response = requests / (identity + '.response.json')
        deadline = time.monotonic() + timeout + 30
        while not response.is_file():
            if time.monotonic() >= deadline:
                raise ValueError('Compatibility supervisor did not finish this exact restore request before its deadline')
            time.sleep(.25)
        receipt = load(response)
        if receipt.get('requestSha256') != digest(path) or receipt.get('status') != 'passed':
            raise ValueError('Compatibility supervisor restore failed; inspect its preserved redacted evidence')
    else:
        audit_toolchain(scratch, load(scratch / '.program-kit/sync/compatibility-pins.json'))
        # The bootstrap closure command grants this scoped restore; use the same
        # request validation, exact toolchain and lock executor as feature/upgrade.
        for mode in ('renew', 'locked'):
            request = tool.restore_request(scratch, lock_path, plan, mode)
            write(scratch / '.program-kit/evidence/building-block-restore-request.json', request)
            from compatibility_process import run
            exit_code = run([sys.executable, str(Path(tool.__file__)), mode, '--target', str(scratch),
                             '--lock', '.program-kit/sync/dependencies.json', '--request',
                             '.program-kit/evidence/building-block-restore-request.json', '--approved'],
                            scratch, stdout, stderr, timeout)
            if exit_code:
                raise ValueError('Shared compatibility restore failed: ' + mode)
    receipt = load(scratch / '.program-kit/evidence/building-block-restore.json')
    tool.verify_evidence(scratch, plan, receipt)
    return {'lockedRestore': receipt, 'toolchain': load(scratch / '.program-kit/evidence/toolchain.json')}


def serve(root, request_path):
    """Trusted supervisor entry point. Its script snapshot lives outside the worker tree."""
    request = load(request_path)
    scratch = contained(root, request['scratch'])
    relative = scratch.relative_to(root).parts
    if request.get('schemaVersion') != 1 or relative[:3] != ('.specify', 'governance', 'compatibility') or len(relative) != 6 or not relative[-1].startswith('scratch-'):
        raise ValueError('Invalid compatibility scratch boundary')
    tool = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    lock_path = scratch / '.program-kit/sync/dependencies.json'
    plan = load(lock_path)
    if digest(lock_path) != request['lockSha256'] or package_execution.canonical_hash(tool.input_basis(scratch, plan)) != request['inputDigest']:
        raise ValueError('Compatibility restore request became stale before provisioning')
    pins = load(scratch / '.program-kit/sync/compatibility-pins.json')
    dotnet = any(Path(t['path']).suffix == '.csproj' for t in plan['targets'])
    npm = any(Path(t['path']).name == 'package.json' for t in plan['targets'])
    expected, content = configuration(root, dotnet=dotnet, npm=npm)
    if pins != expected:
        raise ValueError('Compatibility toolchain differs from current approved setup authority')
    # Re-observe executables and trust in the supervisor; never execute a command
    # array supplied by a worker's toolchain record.
    for name, payload in content.items():
        if (scratch / name).read_bytes() != payload:
            raise ValueError('Compatibility managed toolchain/source configuration changed')
    audit_toolchain(scratch, pins)
    for mode in ('renew', 'locked'):
        write(scratch / '.program-kit/evidence/building-block-restore-request.json',
              tool.restore_request(scratch, lock_path, plan, mode))
        result = subprocess.run([sys.executable, str(Path(tool.__file__)), mode, '--target', str(scratch),
                                 '--lock', '.program-kit/sync/dependencies.json', '--request',
                                 '.program-kit/evidence/building-block-restore-request.json', '--approved'],
                                cwd=scratch, check=False)
        if result.returncode:
            raise ValueError('Shared compatibility restore failed: ' + mode)
    tool.verify_evidence(scratch, plan, load(scratch / '.program-kit/evidence/building-block-restore.json'))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['serve'])
    parser.add_argument('--repository', required=True)
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    try:
        serve(Path(args.repository).resolve(), Path(args.request).resolve())
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
