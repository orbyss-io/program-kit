"""Local preparation from CI-qualified bytes, with separate host-bound evidence.

No candidate build, deterministic acceptance or paid worker dispatch occurs here.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

from release_candidate import (ROOT, attest_verify, fetch_candidate, git, now, policy, read,
                               require, run_metadata, sha256, source, verify_payload,
                               verify_qualification, write)


def host():
    return {'node': platform.node(), 'sourceRoot': str(ROOT.resolve()), 'pythonExecutable': sys.executable,
            'launchers': {name: shutil.which(name) or 'unavailable' for name in ('git', 'specify', 'codex', 'node', 'npm', 'dotnet', 'uv')}}


def validate_preparation(root, path, schemas):
    from live.v2.common import load_object, safe_relative, validate
    value = load_object(path)
    validate(value, load_object(schemas / 'ci-trial-preparation.schema.json'))
    require(value['host'] == host(), 'CI trial preparation belongs to another local host/root/interpreter')
    for record in [*value['artifacts'], *value['preparationLogs']]:
        file = root / safe_relative(record['path'])
        require(file.resolve().is_relative_to(root.resolve()) and file.is_file() and
                file.stat().st_size == record['size'] and sha256(file) == record['sha256'], 'Local preparation artifact/log changed')
    ci = value['ci']
    final = root / safe_relative(ci['qualificationPath'])
    payload_path = root / safe_relative(ci['payloadPath'])
    require(sha256(final) == ci['qualificationSha256'], 'Local preparation qualification changed')
    qualification = read(final)
    run, jobs = run_metadata(ci['runId'])
    verify_qualification(qualification, source(), run, jobs, policy())
    attest_verify(final, 'qualification', value['source']['commit'], ci['runId'], qualification['producer']['attempt'])
    require(sha256(payload_path) == qualification['payloadSha256'], 'Local preparation payload manifest changed')
    payload = read(payload_path)
    verify_payload(payload, root / 'artifacts', source())
    expected = [{'path': 'artifacts/' + r['name'], 'size': r['size'], 'sha256': r['sha256']} for r in payload['assets']]
    require(value['artifacts'] == expected, 'Local preparation must record the complete qualified package inventory')
    return value, sha256(path)


def prepare(run_id, output):
    sys.path.insert(0, str(ROOT / 'tests'))
    from live.v2 import cli
    from live.v2.candidate import install_candidate_from_receipt
    output = output.resolve()
    require(output.is_relative_to((ROOT / 'artifacts').resolve()), 'Preparation output must be inside this source artifacts directory')
    require(not output.exists(), 'Preserve existing trial preparation; choose a fresh output directory')
    require(not git(ROOT, 'status', '--porcelain=v1'), 'Commit candidate before local CI trial preparation')
    started = now().isoformat()
    value, digest = fetch_candidate(run_id, output / 'candidate')
    identity = source()
    tools = {'python': platform.python_version(), **{name: cli.tool_version(name) for name in cli.LIVE_TOOLCHAINS}}
    receipt = {'schemaVersion': '2.0', 'status': 'ci-trial-prepared', 'acceptanceScope': 'local-preparation-from-ci',
               'releaseValidationPassed': False, 'version': identity['version'],
               'source': {'commit': identity['commit'], 'tree': identity['tree'], 'clean': True},
               'platform': {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine()},
               'host': host(), 'toolchains': tools, 'artifacts': [], 'preparationLogs': [], 'steps': [],
               'catalog': {}, 'startedAt': started, 'finishedAt': started,
               'ci': {'runId': int(run_id), 'qualificationSha256': digest,
                      'qualificationPath': (output / 'candidate/qualification/qualification.json').relative_to(ROOT).as_posix(),
                      'payloadPath': (output / 'candidate/payload/candidate-payload.json').relative_to(ROOT).as_posix()}}
    cli.preflight(ROOT, receipt)
    from run_validation import require_device_toolchain
    require_device_toolchain()
    payload = read(output / 'candidate/payload/candidate-payload.json')
    for record in payload['assets']:
        target = ROOT / 'artifacts' / record['name']
        require(not target.exists() or sha256(target) == record['sha256'], 'Preserve differing existing local asset before import: ' + record['name'])
        shutil.copyfile(output / 'candidate/payload' / record['name'], target)
        receipt['artifacts'].append({'path': target.relative_to(ROOT).as_posix(), 'size': record['size'], 'sha256': record['sha256']})
    receipt['catalog']['sha256'] = subprocess.check_output([sys.executable,
        str(ROOT / 'extensions/program-kit-building-blocks/scripts/building_blocks.py'), 'catalog-hash'], text=True).strip()
    (output / 'consumer').mkdir(parents=True)
    receipts = install_candidate_from_receipt(ROOT, output / 'consumer', output / 'packages', receipt, output / 'setup')
    write(output / 'installation-operations.json', {'operations': receipts, 'claim': 'consumer preparation only; no deterministic or AI acceptance'})
    logs = [output / 'installation-operations.json', *sorted((output / 'setup').rglob('*.log'))]
    receipt['preparationLogs'] = [{'path': p.relative_to(ROOT).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)} for p in logs]
    receipt['steps'] = [{'id': 'install-disposable-consumer', 'command': ['install_candidate_from_receipt'], 'exitCode': 0,
                         'startedAt': started, 'finishedAt': now().isoformat()}]
    receipt['finishedAt'] = now().isoformat()
    path = output / 'ci-trial-preparation.json'
    write(path, receipt)
    validate_preparation(ROOT, path, cli.schemas(ROOT))
    cli.preflight(ROOT, receipt)
    print('Local CI trial preparation: ' + str(path) + '; no paid session started.')
    return path
