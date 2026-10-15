"""Exact-candidate CI qualification, immutable handoff and promotion policy.

Network trust is established by GitHub metadata AND cryptographic attestations.
Pure verification functions also support adversarial fixtures without publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

from write_release_receipt import artifact_records, command_output, git, sha256

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ('Run qualify-candidate.yml on main with expected_commit=<exact candidate SHA> before tagging; '
            'retain its complete artifacts. Tagged Release cannot build or run acceptance as recovery.')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Timestamp must include timezone')
    return result.astimezone(timezone.utc)


def now():
    return datetime.now(timezone.utc)


def schema(value, name):
    # Use the existing pinned, project-local runtime, never install a new dependency.
    import importlib.util
    path = ROOT / 'extensions/program-kit-governance/scripts/schema_runtime.py'
    spec = importlib.util.spec_from_file_location('candidate_schema_runtime', path)
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    runtime.activate()
    from jsonschema import Draft202012Validator
    contract = read(ROOT / 'tests/schemas' / (name + '.schema.json'))
    try:
        Draft202012Validator.check_schema(contract)
        Draft202012Validator(contract).validate(value)
    except Exception as error:
        raise ValueError('Invalid ' + name + ' contract: ' + str(error)) from error


def policy():
    value = read(ROOT / 'release-policy.json')
    schema(value, 'release-policy')
    return value


def source():
    return {'commit': git(ROOT, 'rev-parse', 'HEAD'), 'tree': git(ROOT, 'rev-parse', 'HEAD^{tree}'),
            'version': (ROOT / 'VERSION').read_text().strip(),
            'policySha256': sha256(ROOT / 'release-policy.json'),
            'inventorySha256': sha256(ROOT / 'tests/validation-inventory.json')}


def basename(name):
    require(isinstance(name, str) and name not in ('', '.', '..') and
            '/' not in name and '\\' not in name and ':' not in name, 'Asset must be a basename')
    return name


def file_record(path):
    return {'name': basename(path.name), 'size': path.stat().st_size, 'sha256': sha256(path)}


def snapshot(directory, destination):
    require(not git(ROOT, 'status', '--porcelain=v1', '--untracked-files=normal'), 'Payload snapshot requires committed clean source')
    identity = source()
    records = artifact_records(directory, identity['version'])
    value = {'schemaVersion': 1, 'source': identity,
             'assets': [{'name': Path(r['path']).name, 'size': r['size'], 'sha256': r['sha256']} for r in records]}
    schema(value, 'candidate-payload')
    write(destination, value)
    return value


def verify_payload(value, directory, expected_source=None):
    schema(value, 'candidate-payload')
    if expected_source is not None:
        require(value['source'] == expected_source, 'Payload source/policy/inventory mismatch')
    names = [basename(r['name']) for r in value['assets']]
    require(len(names) == len(set(n.casefold() for n in names)), 'Duplicate payload asset')
    for record in value['assets']:
        path = directory / record['name']
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == record['size']
                and sha256(path) == record['sha256'], 'Payload asset missing or changed: ' + record['name'])
    # Independently derive the transitive publication inventory, including Markdown,
    # dependency evidence and checksums. An attacker-controlled checksum cannot add assets.
    actual = artifact_records(directory, value['source']['version'])
    derived = {Path(r['path']).name: (r['size'], r['sha256']) for r in actual}
    require(derived == {r['name']: (r['size'], r['sha256']) for r in value['assets']}, 'Incomplete publication inventory')


def required_checks(lane):
    inventory = read(ROOT / 'tests/validation-inventory.json')['checks']
    return {c['id'] for c in inventory if c.get('qualification', {}).get(lane, False)}


def verify_lane(value, lane, identity, payload_digest, evidence_root, payload_assets=None):
    require(value['lane'] == lane and value['source'] == identity, 'Wrong lane/source')
    require(value['payloadSha256'] == payload_digest, 'Lane tested another payload')
    require(value['platform']['system'] == {'linux': 'Linux', 'windows': 'Windows', 'build': 'Linux'}[lane], 'Wrong platform variant')
    required = required_checks(lane)
    if lane in ('linux', 'windows'):
        required.discard('build-release')
        required.add('prepare-qualified-packages')
    for record in value['journalRecords']:
        relative = PurePosixPath(record['path'])
        require(not relative.is_absolute() and '..' not in relative.parts and '\\' not in record['path'], 'Unsafe original journal path')
        require(sha256(evidence_root / record['path']) == record['sha256'], 'Original journal digest mismatch')
    require([read(evidence_root / r['path']) for r in value['journalRecords']] == value['journals'], 'Original journals changed')
    if payload_assets is not None:
        require(value['beforeAssets'] == payload_assets, 'Lane before-test manifest mismatch')
    steps = [step for journal in value['journals'] for step in journal['steps']]
    require({s['id'] for s in steps} == required and len(steps) == len(required), 'Partial/duplicate check coverage: ' + lane)
    for journal in value['journals']:
        require(journal['source'] == {k: identity[k] for k in ('commit', 'tree')} and
                journal['inventorySha256'] == identity['inventorySha256'] and journal.get('status') == 'passed', 'Journal identity/status mismatch')
        require(journal['platform'] == value['platform']['system'], 'Journal platform mismatch')
        if lane in ('linux', 'windows'):
            require(journal['packageInput']['manifestSha256'] == payload_digest and
                    journal['packageInput']['assetsBefore'] == value['beforeAssets'], 'Missing/changed initial tested-byte inventory')
        if lane == 'linux':
            require(set(journal['browserEngines'].split(',')) == set(policy()['browsers']), 'Missing browser variants')
        for step in journal['steps']:
            require(step['exitCode'] == 0, 'Required check failed: ' + step['id'])
            checks = {c['id']: c for c in read(ROOT / 'tests/validation-inventory.json')['checks']}
            template = (['{python}', 'scripts/release_candidate.py', 'verify-payload', '--manifest',
                         'artifacts/candidate-payload.json'] if step['id'] == 'prepare-qualified-packages'
                        else checks[step['id']]['command'])
            observed = journal['executables']
            expected = [part.format(python=observed['python'], powershell=observed['powershell'],
                                    engines=journal['browserEngines']) for part in template]
            if lane == 'windows' and step['id'] == 'validate_workflow_runtimes':
                require(observed['mixedPython'] and observed['mixedPython'] != observed['python'], 'Distinct Windows shell Python required')
                expected += ['--mixed-python', observed['mixedPython']]
            require(step['command'] == expected, 'Required check command/variant changed: ' + step['id'])
            relative = PurePosixPath(step['log'])
            require(not relative.is_absolute() and '..' not in relative.parts, 'Invalid original log path')
            log = evidence_root / relative
            require(log.is_file() and sha256(log) == step['logSha256'], 'Original log missing/changed: ' + step['id'])
    require(value['beforeAssets'] == value['afterAssets'], 'Tested package bytes changed during lane')


def verify_run(run, jobs, expected, rules, workflow='qualification', complete=True):
    require(run['repository']['full_name'] == rules['repository'], 'Untrusted producer repository')
    require(run['head_repository']['full_name'] == rules['repository'], 'Fork producer rejected')
    require(run['path'] == rules['workflows'][workflow], 'Untrusted producer workflow')
    require(run['event'] == 'workflow_dispatch' and run['head_branch'] == 'main', 'Untrusted producer event/ref')
    require(run['head_sha'] == expected['commit'], 'Producer source mismatch')
    require(int(run['run_attempt']) == int(expected['attempt']), 'Producer attempt mismatch')
    if complete:
        require(run['status'] == 'completed' and run['conclusion'] == 'success', 'Producer run not successful')
    if workflow == 'qualification':
        required = set(rules['requiredJobs']) - (set() if complete else {'finalize'})
        passed = [j['name'] for j in jobs if j['conclusion'] == 'success' and j['head_sha'] == expected['commit']]
        require(all(passed.count(name) == 1 for name in required), 'Missing/failed required qualification job variants')


def verify_qualification(value, identity, run, jobs, rules):
    schema(value, 'candidate-qualification')
    require(value['source'] == identity, 'Qualification exact source/tree/version/policy/inventory mismatch')
    producer = value['producer']
    require(str(producer['runId']) == str(run['id']), 'Qualification run mismatch')
    verify_run(run, jobs, {'commit': identity['commit'], 'attempt': producer['attempt']}, rules)
    require(producer['repository'] == rules['repository'] and producer['workflow'] == rules['workflows']['qualification']
            and producer['workflowRevision'] == identity['commit'], 'Qualification producer identity mismatch')
    require(set(value['lanes']) == {'build', 'linux', 'windows'}, 'Missing qualification lanes')
    for lane in ('build', 'linux', 'windows'):
        expected = (required_checks(lane) - ({'build-release'} if lane != 'build' else set()) |
                    ({'prepare-qualified-packages'} if lane != 'build' else set()))
        require(set(value['coverage'][lane]) == expected and len(value['coverage'][lane]) == len(expected), 'Incomplete qualified coverage')
    require(set(value['browsers']) == set(rules['browsers']), 'Missing qualified browsers')
    require(set(value['artifacts']) == {'payload', 'build', 'linux', 'windows', 'security'}, 'Incomplete artifact graph')
    ids = [r['id'] for r in value['artifacts'].values()]
    require(len(set(ids)) == len(ids), 'Artifact graph identities must be distinct')
    # No enclosing qualification upload identity is permitted by the closed schema.
    for record in value['artifacts'].values():
        require(record['digest'].startswith('sha256:') and len(record['digest']) == 71, 'Missing immutable artifact digest')


def verify_security_content(record, targets):
    require(record['targets'] == targets, 'Security immutable target mismatch')
    if record['status'] == 'passed':
        report = record['report']
        require(not report.get('error'), 'Passing scan contains a tool error')
        scans = report.get('scans', [])
        require(len(scans) == 2 and {s['platform'] for s in scans} == {'linux/amd64', 'linux/arm64'}, 'Missing security platform coverage')
        for scan in scans:
            require(scan['exitCode'] == 0 and not scan['validationErrors'] and scan['image'] in targets
                    and scan['reportedPlatform'] == scan['platform'] and scan['imageID'] == scan['configDigest'], 'Security scan failed or wrong immutable input')
            require(re.fullmatch('sha256:[a-f0-9]{64}', scan['manifestDigest']) and
                    re.fullmatch('sha256:[a-f0-9]{64}', scan['configDigest']) and
                    re.fullmatch('[a-f0-9]{64}', scan['sha256']), 'Incomplete scanner evidence')


def select_security(history, candidate, targets, rules, at=None, original_payload=None):
    require(history, 'Missing security evidence; run refresh-candidate-security.yml')
    ordered = sorted(history, key=lambda r: (timestamp(r['observedAt']), r['runId'], r['attempt']))
    current = at or now()
    previous_failures = set()
    for record in ordered:
        schema(record, 'candidate-security')
        require(record['candidate'] in (candidate, original_payload) and record['targets'] == targets, 'Security candidate/immutable target mismatch')
        verify_security_content(record, targets)
        require(timestamp(record['observedAt']) <= current, 'Security timestamp is in the future')
        if record['status'] != 'passed':
            previous_failures.add(record['identity'])
        else:
            previous_failures.difference_update(record['supersedes'])
    latest = ordered[-1]
    require(latest['status'] == 'passed' and not previous_failures, 'Later failed security scan requires explicit successful supersession')
    require(current - timestamp(latest['observedAt']) <= timedelta(hours=rules['securityMaxAgeHours']),
            'Security evidence stale; run refresh-candidate-security.yml for this unchanged candidate')
    return latest


def select_assessment(history, candidate):
    require(history, 'Missing reviewed readiness disposition; run record-release-assessment.yml')
    unresolved = {}
    ordered = sorted(history, key=lambda a: (timestamp(a['recordedAt']), a['runId'], a['attempt']))
    for assessment in ordered:
        schema(assessment, 'release-assessment')
        require(assessment['candidate'] == candidate, 'Assessment candidate mismatch')
        require(timestamp(assessment['recordedAt']) <= now(), 'Assessment timestamp is in the future')
        require(assessment['review']['actor'] and assessment['review']['reference'], 'Attributable review required')
        for finding in assessment['findings']:
            if finding['kind'] == 'product-defect' and finding['status'] == 'open':
                unresolved[finding['id']] = finding
            elif finding['status'] == 'resolved':
                require(finding['resolution'], 'Explicit finding resolution required')
                unresolved.pop(finding['id'], None)
        for trial in assessment['trials']:
            require(trial['provenance'] in ('human-attested', 'verified-internal'), 'Invalid trial provenance')
            require(trial['manifest']['reference'] and re.fullmatch('[a-f0-9]{64}', trial['manifest']['sha256']), 'Internal trial manifest reference/digest required')
            if trial['outcome'] in ('inconclusive', 'harness-failure'):
                require(trial['disposition'], 'Inconclusive/harness outcome requires disposition')
    require(not unresolved and ordered[-1]['ready'], 'Unresolved confirmed product defect or non-ready assessment blocks promotion')
    return ordered[-1]


def gh(*args, binary=False):
    result = subprocess.run(['gh', *map(str, args)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    require(result.returncode == 0, 'GitHub operation failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout if binary else result.stdout.decode('utf-8')


def api(path):
    return json.loads(gh('api', path))


def pages(path, key):
    values = []
    page = 1
    while True:
        data = api(path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')[key]
        values.extend(data)
        if len(data) < 100:
            return values
        page += 1


def run_metadata(run_id, attempt=None):
    repo = policy()['repository']
    run = api(f'repos/{repo}/actions/runs/{int(run_id)}' + (f'/attempts/{int(attempt)}' if attempt else ''))
    jobs = pages(f'repos/{repo}/actions/runs/{int(run_id)}/attempts/{run["run_attempt"]}/jobs', 'jobs')
    return run, jobs


def artifact_metadata(run_id, name):
    repo = policy()['repository']
    records = pages(f'repos/{repo}/actions/runs/{int(run_id)}/artifacts', 'artifacts')
    matches = [r for r in records if r['name'] == name]
    require(len(matches) == 1, 'Missing/ambiguous candidate artifact: ' + name + '. ' + RECOVERY)
    record = matches[0]
    require(not record['expired'] and timestamp(record['expires_at']) > now(), 'Candidate artifact expired. ' + RECOVERY)
    require(re.fullmatch('sha256:[0-9a-f]{64}', record.get('digest') or ''), 'Artifact lacks immutable digest')
    return record


def download(record, destination):
    """Hard-fail on actual archive digest before extraction; no warning-only action."""
    data = gh('api', f'repos/{policy()["repository"]}/actions/artifacts/{int(record["id"])}/zip', binary=True)
    require('sha256:' + hashlib.sha256(data).hexdigest() == record['digest'], 'Downloaded artifact digest mismatch')
    require(not record['expired'], 'Artifact expired')
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        require(len(set(n.casefold() for n in names)) == len(names), 'Duplicate archive entries')
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in member.filename and
                    ':' not in member.filename and ((member.external_attr >> 16) & 0o170000) != 0o120000, 'Unsafe artifact entry')
        destination.mkdir(parents=True, exist_ok=True)
        for member in archive.infolist():
            target = destination / member.filename
            require(not target.is_symlink() and target.resolve().is_relative_to(destination.resolve()), 'Unsafe existing artifact destination')
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            data = archive.read(member)
            if target.exists():
                require(target.is_file() and target.read_bytes() == data, 'Preserve differing existing artifact evidence: ' + member.filename)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(data)


def attest_verify(path, workflow, commit, run_id=None, attempt=None):
    rules = policy()
    results = json.loads(gh('attestation', 'verify', path, '--repo', rules['repository'],
                           '--signer-workflow', rules['repository'] + '/' + rules['workflows'][workflow],
                           '--source-digest', commit, '--signer-digest', commit,
                           '--source-ref', 'refs/heads/main', '--deny-self-hosted-runners', '--format', 'json'))
    if run_id is not None:
        # Certificate identity comes from GitHub OIDC, not user-supplied predicate fields.
        suffix = f'/actions/runs/{run_id}/attempts/{attempt}'
        require(any(str(r['verificationResult']['signature']['certificate'].get('runInvocationURI', '')).endswith(suffix)
                    for r in results), 'Attestation run/attempt identity mismatch')


def artifact_ref(record):
    return {k: record[k] for k in ('id', 'name', 'digest')}


def fetch_candidate(run_id, destination, expected=None):
    require(not git(ROOT, 'status', '--porcelain=v1', '--untracked-files=normal'), 'Candidate verification requires committed clean source')
    require(not destination.exists(), 'Preserve existing candidate evidence; choose a fresh output directory')
    rules = policy()
    run, jobs = run_metadata(run_id)
    identity = expected or source()
    verify_run(run, jobs, {'commit': identity['commit'], 'attempt': run['run_attempt']}, rules)
    final = artifact_metadata(run_id, f'qualification-{run["run_attempt"]}')
    download(final, destination / 'qualification')
    path = destination / 'qualification/qualification.json'
    attest_verify(path, 'qualification', identity['commit'], run_id, run['run_attempt'])
    value = read(path)
    verify_qualification(value, identity, run, jobs, rules)
    for kind, reference in value['artifacts'].items():
        record = artifact_metadata(run_id, reference['name'])
        require(artifact_ref(record) == reference, 'Immutable artifact metadata mismatch')
        download(record, destination / kind)
    payload_path = destination / 'payload/candidate-payload.json'
    require(sha256(payload_path) == value['payloadSha256'], 'Payload manifest mismatch')
    attest_verify(payload_path, 'qualification', identity['commit'], run_id, run['run_attempt'])
    payload = read(payload_path)
    verify_payload(payload, destination / 'payload', identity)
    require({p.name for p in (destination / 'payload').iterdir()} ==
            {r['name'] for r in payload['assets']} | {'candidate-payload.json'}, 'Unexpected extracted payload inventory')
    for lane in ('build', 'linux', 'windows'):
        verify_lane(read(destination / lane / 'lane.json'), lane, identity, value['payloadSha256'], destination / lane, payload['assets'])
    require(read(destination / 'security/security.json') == value['security'], 'Original security evidence changed')
    return value, sha256(path)


def matching_runs(workflow, commit=None):
    rules = policy()
    name = Path(rules['workflows'][workflow]).name
    runs = pages(f'repos/{rules["repository"]}/actions/workflows/{name}/runs?event=workflow_dispatch' + (f'&head_sha={commit}' if commit else ''), 'workflow_runs')
    return [r for r in runs if (commit is None or r['head_sha'] == commit) and r['head_branch'] == 'main' and
            r['path'] == rules['workflows'][workflow] and r['repository']['full_name'] == rules['repository']]


def find_candidate():
    for run in matching_runs('qualification', source()['commit']):
        if run['conclusion'] != 'success':
            continue
        metadata, jobs = run_metadata(run['id'])
        verify_run(metadata, jobs, {'commit': source()['commit'], 'attempt': metadata['run_attempt']}, policy())
        # Unavailable handoffs are not usable qualification. An older complete
        # matching handoff can still be used; integrity failures never fall back.
        try:
            for kind in ('payload', 'build', 'linux', 'windows', 'security', 'qualification'):
                artifact_metadata(run['id'], f'{kind}-{metadata["run_attempt"]}')
        except ValueError as error:
            if 'expired' in str(error) or 'Missing/ambiguous candidate artifact' in str(error):
                continue
            raise
        return run['id']
    raise ValueError('No successful complete matching qualification. ' + RECOVERY)


def history_for(kind, candidate, commit, destination):
    """Enumerate all applicable attempts; failed/in-flight later records fail closed.

    workflow_dispatch inputs cannot be filtered via run-list API. Each run records
    its candidate input in run-name, enabling fail-closed discovery even before upload.
    """
    rules = policy()
    records, failed_runs = [], []
    runs = []
    for latest in matching_runs(kind):
        for attempt in range(1, int(latest['run_attempt']) + 1):
            runs.append(latest if attempt == latest['run_attempt'] else run_metadata(latest['id'], attempt)[0])
    for run in runs:
        title = {'security': 'Refresh candidate security ', 'assessment': 'Record release assessment '}[kind] + candidate
        if run.get('display_title') != title:
            continue
        verify_run(run, [], {'commit': run['head_sha'], 'attempt': run['run_attempt']}, rules, workflow=kind, complete=False)
        require(run['status'] == 'completed', f'Applicable {kind} run {run["id"]} is incomplete')
        if run['conclusion'] != 'success':
            failed_runs.append((str(run['id']) + '/' + str(run['run_attempt']), run.get('updated_at', run.get('created_at'))))
            continue
        artifact = artifact_metadata(run['id'], f'{kind}-{run["run_attempt"]}')
        directory = destination / str(run['id'])
        download(artifact, directory)
        path = directory / ('security.json' if kind == 'security' else 'assessment.json')
        attest_verify(path, kind, run['head_sha'], run['id'], run['run_attempt'])
        record = read(path)
        require(record['candidate'] == candidate and record['runId'] == run['id'] and record['attempt'] == run['run_attempt'], 'History identity mismatch')
        records.append(record)
    unresolved = [identity for identity, failed_at in failed_runs if not any(identity in record['supersedes'] and
                  failed_at is not None and timestamp(record.get('observedAt', record.get('recordedAt'))) >= timestamp(failed_at)
                  for record in records)]
    require(not unresolved, f'Applicable failed {kind} run requires an explicit reviewed supersession: ' + ', '.join(unresolved))
    return records


def qualification_security_failures(value, candidate):
    """A newer/other failed qualification scan cannot be hidden by an older pass.

    Read every attempt, including failed attempts of a subsequently rerun workflow.
    Job failure is authoritative negative evidence, even if setup prevented a scan
    report. A successful scan-only refresh must explicitly supersede that identity.
    """
    failures = []
    for latest in matching_runs('qualification', value['source']['commit']):
        for attempt in range(1, int(latest['run_attempt']) + 1):
            run, jobs = run_metadata(latest['id'], attempt)
            if run['id'] == value['producer']['runId'] and attempt == value['producer']['attempt']:
                continue
            security = [j for j in jobs if j['name'] == 'security']
            for job in security:
                if job.get('conclusion') in ('skipped', 'success'):
                    continue
                require(job.get('status') == 'completed', 'Applicable qualification security job is still running')
                failures.append({'schemaVersion': 1, 'candidate': candidate, 'targets': value['security']['targets'],
                    'status': 'failed', 'observedAt': job.get('completed_at') or run['updated_at'],
                    'runId': run['id'], 'attempt': attempt, 'identity': str(run['id']) + '/' + str(attempt),
                    'scanner': 'Qualification security job failed/inconclusive; inspect original run evidence',
                    'supersedes': [], 'report': {'jobConclusion': job.get('conclusion')}})
    return failures


def verify_promotion(run_id, destination, tag=None):
    value, digest = fetch_candidate(run_id, destination)
    if tag is not None:
        require(tag == 'v' + value['source']['version'], 'Tag/VERSION mismatch')
    from dependency_maintenance import default_host
    targets = [default_host(ROOT, read(ROOT / 'maintenance-policy.json'))]
    require(value['security']['targets'] == targets, 'Qualification scanned different candidate images')
    security = [value['security'], *qualification_security_failures(value, digest),
                *history_for('security', digest, value['source']['commit'], destination / 'security-history')]
    select_security(security, digest, value['security']['targets'], policy(), original_payload=value['payloadSha256'])
    assessment = select_assessment(history_for('assessment', digest, value['source']['commit'], destination / 'assessments'), digest)
    write(destination / 'promotion.json', {'candidate': digest, 'runId': int(run_id), 'source': value['source'],
                                        'assets': read(destination / 'payload/candidate-payload.json')['assets'], 'assessment': assessment})
    return value, digest


def collect_lane(lane, manifest, output):
    payload = read(manifest)
    verify_payload(payload, ROOT / 'artifacts', source())
    journals = [read(p) for p in sorted((ROOT / 'artifacts/validation-runs').glob('*/journal.json'))]
    require(journals, 'Missing executed validation journals')
    tools = {name: command_output([sys.executable if name == 'python' else name, '--version'])
             for name in ('python', 'node', 'npm', 'dotnet', 'git', 'specify')}
    value = {'lane': lane, 'source': source(), 'payloadSha256': sha256(manifest),
             'platform': {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine()},
             'toolchains': tools, 'journals': journals,
             'journalRecords': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha256(p)} for p in sorted((ROOT / 'artifacts/validation-runs').glob('*/journal.json'))], 'beforeAssets': payload['assets'],
             'afterAssets': [file_record(ROOT / 'artifacts' / r['name']) for r in payload['assets']]}
    verify_lane(value, lane, source(), sha256(manifest), ROOT)
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'artifacts/validation-runs', output / 'artifacts/validation-runs', dirs_exist_ok=True)
    write(output / 'lane.json', value)


def scan_security(candidate, output, supersedes):
    from dependency_maintenance import default_host, scan
    image = default_host(ROOT, read(ROOT / 'maintenance-policy.json'))
    status = 'failed'
    try:
        scan(ROOT, image)
        status = 'passed'
    finally:
        report = ROOT / 'artifacts/dependency-security/result.json'
        value = {'schemaVersion': 1, 'candidate': candidate, 'targets': [image], 'status': status,
                 'observedAt': now().isoformat(), 'runId': int(os.environ['GITHUB_RUN_ID']),
                 'attempt': int(os.environ['GITHUB_RUN_ATTEMPT']),
                 'identity': os.environ['GITHUB_RUN_ID'] + '/' + os.environ['GITHUB_RUN_ATTEMPT'],
                 'scanner': (subprocess.run(['trivy', '--version'], capture_output=True, text=True, check=False).stdout.strip() if shutil.which('trivy') else 'unavailable'), 'supersedes': supersedes,
                 'report': read(report) if report.exists() else {'error': 'scanner failed before report'}}
        write(output / 'security.json', value)
        if report.parent.exists():
            shutil.copytree(report.parent, output / 'reports', dirs_exist_ok=True)


def finalize(output):
    from run_validation import require_release_authority
    require_release_authority('Qualification', False, False, os.environ, os.name)
    require(not git(ROOT, 'status', '--porcelain=v1', '--untracked-files=normal'), 'Qualification finalization requires unchanged clean source')
    rules = policy()
    run_id, attempt = int(os.environ['GITHUB_RUN_ID']), int(os.environ['GITHUB_RUN_ATTEMPT'])
    run, jobs = run_metadata(run_id)
    verify_run(run, jobs, {'commit': source()['commit'], 'attempt': attempt}, rules, complete=False)
    artifacts = {}
    with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as temp:
        directory = Path(temp)
        for kind in ('payload', 'build', 'linux', 'windows', 'security'):
            record = artifact_metadata(run_id, f'{kind}-{attempt}')
            artifacts[kind] = artifact_ref(record)
            download(record, directory / kind)
        payload_path = directory / 'payload/candidate-payload.json'
        payload = read(payload_path)
        verify_payload(payload, directory / 'payload', source())
        digest = sha256(payload_path)
        for lane in ('build', 'linux', 'windows'):
            verify_lane(read(directory / lane / 'lane.json'), lane, source(), digest, directory / lane, payload['assets'])
        security = read(directory / 'security/security.json')
        require(security['candidate'] == digest and security['status'] == 'passed', 'Original security scan failed or wrong payload')
        from dependency_maintenance import default_host
        verify_security_content(security, [default_host(ROOT, read(ROOT / 'maintenance-policy.json'))])
        # Original scan binds the pre-existing payload digest. Final qualification
        # digest cannot be known until this acyclic manifest has been serialized.
        value = {'schemaVersion': 1, 'source': source(), 'producer': {'repository': rules['repository'],
                 'workflow': rules['workflows']['qualification'], 'workflowRevision': source()['commit'],
                 'runId': run_id, 'attempt': attempt}, 'payloadSha256': digest,
                 'lanes': ['build', 'linux', 'windows'], 'coverage': {}, 'browsers': rules['browsers'],
                 'artifacts': artifacts, 'security': security, 'finishedAt': now().isoformat()}
        for lane in value['lanes']:
            value['coverage'][lane] = sorted(s['id'] for j in read(directory / lane / 'lane.json')['journals'] for s in j['steps'])
        schema(value, 'candidate-qualification')
        write(output, value)


def recommendation(paths, rules=None):
    from fnmatch import fnmatchcase
    rules = rules or policy()
    return [dict(family=r['family'], trials=r['trials'], reason=r['reason'], gaps=r['gaps'])
            for r in rules['recommendations'] if any(fnmatchcase(p, pattern) for p in paths for pattern in r['inputs'])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('find')
    sub.add_parser('assert-main').add_argument('--expected-commit', required=True)
    sub.add_parser('assert-recorder').add_argument('--expected-commit', required=True)
    p = sub.add_parser('snapshot'); p.add_argument('--directory', type=Path, default=ROOT / 'artifacts'); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('verify-payload'); p.add_argument('--manifest', type=Path, required=True); p.add_argument('--directory', type=Path, default=ROOT / 'artifacts')
    p = sub.add_parser('import-payload'); p.add_argument('--run-id', required=True)
    p = sub.add_parser('lane'); p.add_argument('--lane', choices=('build', 'linux', 'windows'), required=True); p.add_argument('--manifest', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('finalize'); p.add_argument('--output', type=Path, required=True)
    for name in ('download', 'verify-promotion', 'prepare-trial'):
        p = sub.add_parser(name); p.add_argument('--run-id', required=True); p.add_argument('--output', type=Path, required=True)
        if name == 'verify-promotion': p.add_argument('--tag')
        if name == 'download': p.add_argument('--candidate')
    p = sub.add_parser('security'); p.add_argument('--candidate', required=True); p.add_argument('--output', type=Path, required=True); p.add_argument('--supersedes', default='')
    p = sub.add_parser('record-assessment'); p.add_argument('--candidate', required=True); p.add_argument('--input', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('recommend'); p.add_argument('--base', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'find': print(find_candidate())
        elif args.command == 'assert-main':
            require(os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and os.environ.get('GITHUB_REF') == 'refs/heads/main'
                    and os.environ.get('GITHUB_SHA') == args.expected_commit == source()['commit'], 'Expected candidate, checkout and main workflow source must agree')
        elif args.command == 'assert-recorder':
            require(os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and os.environ.get('GITHUB_REF') == 'refs/heads/main'
                    and args.expected_commit == source()['commit'], 'Recorder must execute on trusted main and check out the exact candidate')
        elif args.command == 'snapshot': snapshot(args.directory, args.output)
        elif args.command == 'verify-payload': verify_payload(read(args.manifest), args.directory, source())
        elif args.command == 'import-payload':
            run, _ = run_metadata(args.run_id)
            require(run['head_sha'] == source()['commit'] and run['path'] == policy()['workflows']['qualification']
                    and run['repository']['full_name'] == policy()['repository'] and run['event'] == 'workflow_dispatch'
                    and run['head_branch'] == 'main', 'Untrusted in-workflow payload producer')
            record = artifact_metadata(args.run_id, f'payload-{run["run_attempt"]}')
            download(record, ROOT / 'artifacts')
            attest_verify(ROOT / 'artifacts/candidate-payload.json', 'qualification', source()['commit'], args.run_id, run['run_attempt'])
            verify_payload(read(ROOT / 'artifacts/candidate-payload.json'), ROOT / 'artifacts', source())
        elif args.command == 'lane': collect_lane(args.lane, args.manifest, args.output)
        elif args.command == 'finalize': finalize(args.output)
        elif args.command == 'download':
            _, digest = fetch_candidate(args.run_id, args.output)
            if args.candidate: require(args.candidate == digest, 'Requested qualification digest mismatch')
            print('Verified qualification: ' + digest)
        elif args.command == 'verify-promotion':
            _, digest = verify_promotion(args.run_id, args.output, args.tag)
            print('Non-publishing promotion verification passed: ' + digest)
        elif args.command == 'security': scan_security(args.candidate, args.output, args.supersedes.split(',') if args.supersedes else [])
        elif args.command == 'record-assessment':
            value = read(args.input)
            value.update(candidate=args.candidate, recordedAt=now().isoformat(), runId=int(os.environ['GITHUB_RUN_ID']), attempt=int(os.environ['GITHUB_RUN_ATTEMPT']))
            require(value['review']['actor'] == os.environ['GITHUB_ACTOR'], 'Review actor must be the authenticated dispatch actor')
            require(all(t['provenance'] == 'human-attested' for t in value['trials']), 'Submitted JSON cannot prove independently verified trial execution')
            schema(value, 'release-assessment')
            write(args.output, value)
        elif args.command == 'recommend': print(json.dumps(recommendation(git(ROOT, 'diff', '--name-only', args.base + '..HEAD').splitlines()), indent=2))
        elif args.command == 'prepare-trial':
            from release_trial import prepare
            prepare(args.run_id, args.output)
        return 0
    except (ValueError, RuntimeError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error) + '\n' + RECOVERY, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
