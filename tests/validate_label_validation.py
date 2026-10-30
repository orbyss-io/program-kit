"""Closed label-metadata contract; optional actual Core, generated JS, HTTP and browser parity.

--unit is the bounded Development contract test. --execute additionally runs the
compiled disposable Core/exporter and native browser matrix, never a coding agent.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
TOOL = TEMPLATE / 'files/scripts/label_validation.py'
spec = importlib.util.spec_from_file_location('label_validation', TOOL)
labels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(labels)
EVIDENCE = None
COMMAND = 0


def run(command, cwd=ROOT, input=None, expected=0, timeout=180):
    global COMMAND
    result = subprocess.run([str(item) for item in command], cwd=cwd, input=input,
        capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    if EVIDENCE:
        COMMAND += 1
        (EVIDENCE / f'command-{COMMAND}.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        (EVIDENCE / f'command-{COMMAND}.json').write_text(json.dumps({'command': [str(item) for item in command],
            'exitCode': result.returncode, 'expectedExitCode': expected}, indent=2), encoding='utf-8')
    if result.returncode != expected:
        raise AssertionError('Command failed: ' + str(command) + '\n' + result.stdout + result.stderr)
    return result.stdout


def unit_checks():
    value = {'schemaVersion': 1, 'owner': 'SyntheticOwner', 'contractId': 'SyntheticOwner.Creation', 'contractVersion': 1,
        'rules': {'displayLabel': {'ruleId': 'SyntheticOwner.Label', 'ruleVersion': 1, 'normalizationOrder': labels.ORDER,
            'trimCodeUnits': labels.TRIM_CODE_UNITS, 'rejectedRawCodeUnitRanges': labels.RAW_CONTROL_RANGES,
            'lengthUnit': 'utf16', 'minimumLength': 1, 'maximumLength': 120}}}
    labels.validate_descriptor(value)
    mutations = [lambda item: item.update(schemaVersion=2), lambda item: item.update(owner='../other'),
        lambda item: item.update(contractVersion=True), lambda item: item.update(extra=True),
        lambda item: item['rules']['displayLabel'].update(ruleId=''),
        lambda item: item['rules']['displayLabel'].update(ruleVersion=0),
        lambda item: item['rules']['displayLabel'].update(normalizationOrder=['trim', 'rejectRawControls', 'validateUtf16Length']),
        lambda item: item['rules']['displayLabel'].update(trimCodeUnits=[32]),
        lambda item: item['rules']['displayLabel'].update(trimCodeUnits=[True, *labels.TRIM_CODE_UNITS[1:]]),
        lambda item: item['rules']['displayLabel'].update(rejectedRawCodeUnitRanges=[[0, 31]]),
        lambda item: item['rules']['displayLabel'].update(lengthUnit='unicode-code-points'),
        lambda item: item['rules']['displayLabel'].update(minimumLength=121),
        lambda item: item['rules']['displayLabel'].update(maximumLength=0),
        lambda item: item['rules']['displayLabel'].update(maximumLength=True),
        lambda item: item['rules']['displayLabel'].update(transportMaxLength=120),
        lambda item: item['rules'].update(other=copy.deepcopy(item['rules']['displayLabel']))]
    for mutate in mutations:
        altered = copy.deepcopy(value)
        mutate(altered)
        try:
            labels.validate_descriptor(altered)
        except ValueError:
            pass
        else:
            raise AssertionError('Unsupported descriptor was accepted')
    generated = labels.generate_typescript(value)
    assert b'rawControls.test(raw)' in generated and b'raw.trim()' not in generated
    assert b'validationDescriptorSha256' in generated and b'Object.freeze(labelValidationMetadata)' in generated
    identity_fixture = copy.deepcopy(value)
    identity_fixture.update(owner='TRIM_UNITS', contractId='DIGEST.METADATA.TRIM_UNITS')
    identity_rule = identity_fixture['rules'].pop('displayLabel')
    identity_rule['ruleId'] = 'METADATA.TRIM_UNITS.DIGEST'
    identity_fixture['rules']['TRIM_UNITS'] = identity_rule
    assert json.dumps(identity_fixture, ensure_ascii=True, indent=2, sort_keys=True).encode() in labels.generate_typescript(identity_fixture)
    own_constructor = copy.deepcopy(value)
    own_constructor['rules'] = {'constructor': own_constructor['rules']['displayLabel']}
    labels.validate_descriptor(own_constructor)
    output = EVIDENCE / 'unit/labels.ts'
    labels.preserve_output(output, generated, False)
    labels.preserve_output(output, generated, True)
    output.write_bytes(generated + b'// stale\n')
    try:
        labels.preserve_output(output, generated, True)
    except ValueError:
        pass
    else:
        raise AssertionError('Stale generated validator accepted')
    duplicate_artifacts = [labels.canonical_bytes(value).decode().replace('"schemaVersion": 1', '"schemaVersion": 1, "schemaVersion": 1'),
        labels.canonical_bytes(value).decode().replace('"maximumLength": 120', '"maximumLength": 120, "maximumLength": 120')]
    for malformed in duplicate_artifacts:
        descriptor = EVIDENCE / 'unit/duplicate-descriptor.json'
        descriptor.write_text(malformed, encoding='utf-8')
        try:
            labels.read_descriptor(descriptor)
        except ValueError as error:
            assert 'duplicate JSON property' in str(error)
        else:
            raise AssertionError('Duplicate artifact property accepted')
    schema = json.loads((TEMPLATE / 'files/scripts/label-validation.schema.json').read_text())
    assert schema['$defs']['rule']['properties']['trimCodeUnits']['const'] == labels.TRIM_CODE_UNITS
    assert schema['$defs']['rule']['properties']['normalizationOrder']['const'] == labels.ORDER
    manifest = json.loads((TEMPLATE / 'managed-files.json').read_text())
    assert {'scripts/label_validation.py', 'scripts/label-validation.schema.json'} <= {row['path'] for row in manifest['files']}
    return {'invalidDescriptorCases': len(mutations), 'duplicateArtifactCases': len(duplicate_artifacts),
        'generatedStalenessRejected': True, 'ownedIdentityPreservation': True, 'ownConstructorSupported': True,
        'managedMaterialization': True}


def toolchain(workspace: Path, prepared: Path | None, engines: list[str]) -> Path:
    package = json.loads((TEMPLATE / 'web-profiles/common/tools/program-kit/web/package.json').read_text())
    pins = {name: package['devDependencies'][name] for name in ('@playwright/test', 'typescript')}
    expected_node = (TEMPLATE / 'files/.nvmrc').read_text().strip().removeprefix('v')
    assert run(['node', '--version']).strip().removeprefix('v') == expected_node, 'Node differs from the selected native pin'
    if prepared:
        modules = prepared.resolve()
    else:
        (workspace / 'package.json').write_text(json.dumps({'private': True, 'type': 'module', 'devDependencies': pins}))
        expected_npm = (TEMPLATE / 'files/.npm-version').read_text().strip().removeprefix('v')
        npm = 'npm.cmd' if os.name == 'nt' else 'npm'
        assert run([npm, '--version']).strip() == expected_npm, 'npm differs from the selected native pin'
        run([npm, 'install', '--package-lock-only', '--ignore-scripts', '--no-audit', '--no-fund'], workspace)
        run([npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], workspace)
        modules = workspace / 'node_modules'
        install = ['node', modules / 'playwright/cli.js', 'install']
        if os.name != 'nt':
            install.append('--with-deps')
        run([*install, *engines], workspace, timeout=600)
    for name, version in pins.items():
        actual = json.loads((modules / name / 'package.json').read_text())['version']
        assert actual == version, name + ' differs from the selected native pin'
    return modules


def vectors():
    return [None, '', ' ', 'x' * 119, 'x' * 120, 'x' * 121, ' ' + 'x' * 120 + ' ',
        '\tname', 'name\n', 'na\x00me', '\x85name', '\ufeffname', '\xa0name\xa0',
        '\u2003name\u3000', '\u2028name\u2029', '😀' * 60, '😀' * 61, 'e\u0301' * 60,
        'e\u0301' * 61, ' A😀é ', *[chr(unit) + 'label' for unit in range(32)],
        *['label' + chr(unit) for unit in range(127, 160)]]


def http_checks(workspace: Path, inputs):
    run(['dotnet', 'restore', 'Api/Api.csproj', '--configfile', 'NuGet.config'], workspace)
    run(['dotnet', 'build', 'Api/Api.csproj', '--no-restore', '--configuration', 'Release', '--nologo'], workspace)
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        port = port_socket.getsockname()[1]
    address = f'http://127.0.0.1:{port}'
    with (EVIDENCE / 'native-api.log').open('w', encoding='utf-8') as stream:
        process = subprocess.Popen(['dotnet', str(workspace / 'Api/bin/Release/net10.0/Api.dll'), '--urls', address],
            cwd=workspace, stdout=stream, stderr=subprocess.STDOUT)
        try:
            due = time.monotonic() + 20
            while True:
                try:
                    with urlopen(address + '/effects', timeout=1) as response:
                        assert json.load(response) == 0
                    break
                except (URLError, TimeoutError):
                    if time.monotonic() >= due or process.poll() is not None:
                        raise AssertionError('Native API did not become ready')
                    time.sleep(0.1)
            for raw in inputs:
                request = Request(address + '/labels', data=json.dumps({'label': raw}).encode(), headers={'Content-Type': 'application/json'})
                try:
                    with urlopen(request, timeout=3) as response:
                        raise AssertionError('Invalid raw API input admitted: ' + str(response.status))
                except HTTPError as error:
                    assert error.code == 400
            with urlopen(address + '/effects', timeout=3) as response:
                assert json.load(response) == 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=10)
    return {'nativeHttpInvalidCases': len(inputs), 'effects': 0, 'databaseAcceptanceClaimed': False}


def native_checks(args):
    workspace = EVIDENCE / 'consumer'
    shutil.copytree(ROOT / 'tests/fixtures/label-validation', workspace)
    shutil.copyfile(TEMPLATE / 'files/global.json', workspace / 'global.json')
    (workspace / 'package.json').write_text('{"type":"module"}')
    modules = toolchain(workspace, args.node_modules, args.engines.split(','))
    run(['dotnet', 'restore', 'Exporter/Exporter.csproj', '--configfile', 'NuGet.config'], workspace)
    descriptor = workspace / 'contracts/labels.json'
    generated = workspace / 'generated/labels.ts'
    exporter = workspace / 'Exporter/Exporter.csproj'
    export = [sys.executable, TOOL, 'export', '--repository', workspace, '--project', exporter, '--output', descriptor]
    generate = [sys.executable, TOOL, 'generate', '--descriptor', descriptor, '--output', generated]
    run(export); run(generate); run([*export, '--check']); run([*generate, '--check'])
    # Representation aliases and identity strings use actual exported Core bounds/sets;
    # these independent generator fixtures change no Core normalization semantics.
    own_constructor = labels.read_descriptor(descriptor)
    own_constructor['rules'] = {'constructor': own_constructor['rules']['displayLabel']}
    (generated.parent / 'owned-constructor.ts').write_bytes(labels.generate_typescript(own_constructor))
    identity_fixture = labels.read_descriptor(descriptor)
    identity_fixture.update(owner='TRIM_UNITS', contractId='DIGEST.METADATA.TRIM_UNITS')
    identity_rule = identity_fixture['rules'].pop('displayLabel')
    identity_rule['ruleId'] = 'METADATA.TRIM_UNITS.DIGEST'
    identity_fixture['rules']['TRIM_UNITS'] = identity_rule
    (workspace / 'identity-descriptor.json').write_bytes(labels.canonical_bytes(identity_fixture))
    (generated.parent / 'identity.ts').write_bytes(labels.generate_typescript(identity_fixture))
    run(['node', modules / 'typescript/lib/tsc.js', '--strict', '--target', 'ES2022', '--module', 'ES2022',
        '--lib', 'ES2022,DOM', '--skipLibCheck', '--outDir', generated.parent,
        generated, generated.parent / 'owned-constructor.ts', generated.parent / 'identity.ts'], workspace)
    runtime_admission = json.loads(run(['node', 'rule-names.mjs'], workspace))
    inputs = vectors()
    native = json.loads(run(['dotnet', 'run', '--no-build', '--no-restore', '--project', exporter,
        '--configuration', 'Release', '--', 'evaluate'], workspace, input=json.dumps(inputs)))
    (workspace / 'vectors.json').write_text(json.dumps(inputs, ensure_ascii=True), encoding='utf-8')
    evaluator = '''import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {normalizeLabel,labelValidationMetadata,validationDescriptorSha256} from './generated/labels.js';
const inputs=JSON.parse(await readFile('vectors.json','utf8'));
console.log(JSON.stringify(inputs.map(raw=>{const result=normalizeLabel('displayLabel',raw);const value=result.valid?result.value:null;
return {valid:result.valid,value,digest:value===null?null:createHash('sha256').update('CreatePolicy:v1\\n'+Buffer.byteLength(value,'utf8')+':'+value).digest('hex')};})));
if(!Object.isFrozen(labelValidationMetadata.rules.displayLabel))throw new Error('Mutable metadata');
'''
    (workspace / 'evaluate.mjs').write_text(evaluator)
    browser_values = json.loads(run(['node', 'evaluate.mjs'], workspace))
    assert native == browser_values, 'Actual Core/generated JS normalization or digest differs'
    assert native[4]['valid'] and not native[5]['valid'] and native[6]['value'] == 'x' * 120
    assert not native[7]['valid'] and not native[8]['valid'] and not native[10]['valid']
    assert native[11]['value'] == '\ufeffname' and native[12]['value'] == 'name'
    assert native[15]['valid'] and not native[16]['valid']
    # Change actual Core authority: a rebuilt exporter must detect stale metadata, then regenerate matching bounds.
    core = workspace / 'Core/DisplayLabels.cs'
    original = core.read_text()
    core.write_text(original.replace('MaximumLength = 120', 'MaximumLength = 119'))
    run([*export, '--check'], expected=1)
    run(export)
    run([*generate, '--check'], expected=1)
    core.write_text(original)
    run(export); run([*generate, '--check'])
    invalid = [raw for raw, result in zip(inputs, native) if not result['valid']]
    http = http_checks(workspace, invalid)
    browser = json.loads(run(['node', workspace / 'browser.mjs', workspace,
        modules / '@playwright/test/index.mjs', args.engines], workspace))
    return {'compiledCoreGeneratedJsVectors': len(inputs), 'digestParity': True, 'nativeSourceStalenessRejected': True,
        'typescriptCompiled': True, 'runtimeRuleAdmission': runtime_admission, 'nativeApi': http, 'browser': browser,
        'scope': 'Disposable synthetic consumer; actual compiled pure Core, native HTTP and browser. No real consumer or PostgreSQL acceptance.'}


def main():
    global EVIDENCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--node-modules', type=Path, help='Reuse existing exact pinned TypeScript/Playwright without package or browser installation')
    args = parser.parse_args()
    engines = args.engines.split(',')
    if not engines or len(set(engines)) != len(engines) or set(engines) - {'chromium', 'firefox', 'webkit'}:
        parser.error('Specify distinct supported browser engines')
    EVIDENCE = ROOT / 'artifacts/tests/validation-parity' / uuid.uuid4().hex[:8]
    EVIDENCE.mkdir(parents=True)
    status = {'status': 'running', 'nativeExecuted': args.execute}
    try:
        if args.unit or not args.execute:
            status['unit'] = unit_checks()
        if args.execute:
            status['native'] = native_checks(args)
        status['status'] = 'passed'
        print('Label validation passed: ' + str(EVIDENCE))
        return 0
    except Exception:
        status['status'] = 'failed'
        raise
    finally:
        (EVIDENCE / 'status.json').write_text(json.dumps(status, indent=2), encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
