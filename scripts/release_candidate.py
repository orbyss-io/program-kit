"""Inspect exact CI-built packages. Human publication authority lives in GitHub environments.

This module transports no developer execution claims and starts no coding agent.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timedelta, timezone

from release_assets import artifact_records, git, sha256

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = 'Run qualify-candidate.yml on main with expected_commit=<exact SHA>; inspect that run before publication.'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Timestamp must include timezone')
    return result.astimezone(timezone.utc)


def now():
    return datetime.now(timezone.utc)


def policy():
    return read(ROOT / 'release-policy.json')


def source():
    return {'commit': git(ROOT, 'rev-parse', 'HEAD'), 'tree': git(ROOT, 'rev-parse', 'HEAD^{tree}'),
            'version': (ROOT / 'VERSION').read_text().strip(),
            'policySha256': sha256(ROOT / 'release-policy.json')}


def basename(name):
    require(isinstance(name, str) and name not in ('', '.', '..') and
            not any(c in name for c in '/\\:'), 'Asset must be a basename')
    return name


def snapshot(directory, destination):
    require(not git(ROOT, 'status', '--porcelain=v1', '--untracked-files=normal'), 'Candidate requires committed clean source')
    identity = source()
    value = {'schemaVersion': 1, 'source': identity,
             'assets': [{'name': Path(r['path']).name, 'size': r['size'], 'sha256': r['sha256']}
                        for r in artifact_records(directory, identity['version'])]}
    write(destination, value)
    return value


def verify_payload(value, directory, expected_source=None):
    require(set(value) == {'schemaVersion', 'source', 'assets'} and value['schemaVersion'] == 1, 'Invalid package manifest')
    if expected_source is not None:
        require(value['source'] == expected_source, 'Payload source/policy mismatch')
    names = [basename(r['name']) for r in value['assets']]
    require(names and len(names) == len(set(n.casefold() for n in names)), 'Empty or duplicate payload inventory')
    for record in value['assets']:
        require(set(record) == {'name', 'size', 'sha256'} and type(record['size']) is int and record['size'] >= 0 and
                re.fullmatch('[0-9a-f]{64}', record['sha256']), 'Invalid asset record')
        path = directory / record['name']
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == record['size'] and
                sha256(path) == record['sha256'], 'Payload asset missing or changed: ' + record['name'])
    # Derive the shipped inventory independently from its actual indexes and checksums.
    actual = artifact_records(directory, value['source']['version'])
    require({Path(r['path']).name: (r['size'], r['sha256']) for r in actual} ==
            {r['name']: (r['size'], r['sha256']) for r in value['assets']}, 'Incomplete publication inventory')


def gh(*args, binary=False):
    result = subprocess.run(['gh', *map(str, args)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    require(result.returncode == 0, 'GitHub operation failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout if binary else result.stdout.decode('utf-8')


def api(path):
    return json.loads(gh('api', path))


def pages(path, key):
    values, page = [], 1
    while True:
        data = api(path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')[key]
        values.extend(data)
        if len(data) < 100:
            return values
        page += 1


def run_metadata(run_id):
    base = f'repos/{policy()["repository"]}/actions/runs/{int(run_id)}'
    run = api(base)
    return run, pages(base + f'/attempts/{run["run_attempt"]}/jobs', 'jobs')


def verify_run(run, jobs, identity, rules=None):
    rules = rules or policy()
    require(run['repository']['full_name'] == rules['repository'] and
            run['path'] == rules['workflow'] and run['event'] == 'workflow_dispatch' and
            run['head_branch'] == 'main' and run['head_sha'] == identity['commit'] and
            run['status'] == 'completed' and run['conclusion'] == 'success', 'Not a successful exact-source main candidate run')
    for required in rules['requiredJobs']:
        matches = [j for j in jobs if j['name'] == required]
        require(len(matches) == 1 and matches[0]['conclusion'] == 'success', 'Missing or unsuccessful required job: ' + required)


def artifact_metadata(run_id, name):
    records = pages(f'repos/{policy()["repository"]}/actions/runs/{int(run_id)}/artifacts', 'artifacts')
    matches = [r for r in records if r['name'] == name]
    require(len(matches) == 1, 'Missing/ambiguous candidate artifact: ' + name)
    record = matches[0]
    require(not record['expired'] and timestamp(record['expires_at']) > now(), 'Candidate artifact expired')
    require(re.fullmatch('sha256:[0-9a-f]{64}', record.get('digest') or ''), 'Artifact lacks immutable digest')
    return record


def download(record, destination):
    data = gh('api', f'repos/{policy()["repository"]}/actions/artifacts/{int(record["id"])}/zip', binary=True)
    require('sha256:' + hashlib.sha256(data).hexdigest() == record['digest'], 'Downloaded artifact digest mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        require(len(set(n.casefold() for n in names)) == len(names), 'Duplicate archive entries')
        for member in archive.infolist():
            original = member.orig_filename
            path = PurePosixPath(original)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in original and
                    ':' not in original and '\0' not in original and ((member.external_attr >> 16) & 0o170000) != 0o120000, 'Unsafe artifact entry')
        destination.mkdir(parents=True, exist_ok=True)
        for member in archive.infolist():
            target = destination / member.filename
            require(not target.is_symlink() and target.resolve().is_relative_to(destination.resolve()), 'Unsafe destination')
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            content = archive.read(member)
            if target.exists():
                require(target.is_file() and target.read_bytes() == content, 'Preserve differing existing artifact: ' + member.filename)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(content)


def fetch_candidate(run_id, destination, expected=None):
    require(not destination.exists(), 'Choose a fresh candidate output directory')
    identity = expected or source()
    run, jobs = run_metadata(run_id)
    verify_run(run, jobs, identity)
    latest = latest_candidate_run(identity)
    require(latest['id'] == run['id'] and latest['run_attempt'] == run['run_attempt'],
            'A newer exact-source candidate run exists; inspect its outcome instead of older passing results')
    download(artifact_metadata(run_id, f'payload-{run["run_attempt"]}'), destination / 'payload')
    path = destination / 'payload/candidate-payload.json'
    manifest = read(path)
    verify_payload(manifest, path.parent, identity)
    require({p.name for p in path.parent.iterdir()} ==
            {r['name'] for r in manifest['assets']} | {'candidate-payload.json'}, 'Unexpected payload files')
    download(artifact_metadata(run_id, f'security-{run["run_attempt"]}'), destination / 'security')
    security_current(destination)
    return manifest, sha256(path)


def latest_candidate_run(identity):
    rules = policy()
    runs = pages(f'repos/{rules["repository"]}/actions/workflows/{Path(rules["workflow"]).name}/runs?event=workflow_dispatch&head_sha={identity["commit"]}', 'workflow_runs')
    matching = [run for run in runs if run['head_branch'] == 'main' and run['path'] == rules['workflow'] and
                run['repository']['full_name'] == rules['repository'] and run['head_sha'] == identity['commit']]
    require(matching, 'No exact-source main candidate run. ' + RECOVERY)
    return max(matching, key=lambda run: (timestamp(run['created_at']), int(run['id'])))


def find_candidate():
    identity = source()
    latest = latest_candidate_run(identity)
    run, jobs = run_metadata(latest['id'])
    verify_run(run, jobs, identity)
    artifact_metadata(run['id'], f'payload-{run["run_attempt"]}')
    return run['id']


def verify_promotion(run_id, destination, tag=None, expected_payload=None, security_observed_at=None):
    manifest, digest = fetch_candidate(run_id, destination)
    require(expected_payload is None or digest == expected_payload, 'Candidate artifact changed since approval')
    if security_observed_at is not None:
        age = now() - timestamp(security_observed_at)
        require(timedelta(0) <= age <= timedelta(hours=policy()['securityMaxAgeHours']),
                'Security expired while waiting for approval; dispatch Release again before publishing')
    require(tag is None or tag == 'v' + manifest['source']['version'], 'Tag/VERSION mismatch')
    write(destination / 'promotion.json', {'source': manifest['source'], 'runId': int(run_id),
          'payloadSha256': digest, 'assets': manifest['assets']})
    return manifest, digest


def import_payload():
    run_id = os.environ['GITHUB_RUN_ID']
    run, _ = run_metadata(run_id)
    # Pull requests execute a merge ref; REST head_sha may describe the source branch.
    require(os.environ['GITHUB_SHA'] == source()['commit'] and run['repository']['full_name'] == policy()['repository'] and
            run['path'] in (policy()['workflow'], '.github/workflows/ci.yml'), 'Unexpected in-workflow payload producer')
    directory = ROOT / 'artifacts/payload'
    download(artifact_metadata(run_id, f'payload-{run["run_attempt"]}'), directory)
    verify_payload(read(directory / 'candidate-payload.json'), directory, source())


def assert_environment():
    rules = policy()
    environment = api(f'repos/{rules["repository"]}/environments/{rules["publicationEnvironment"]}')
    require(any(r['type'] == 'required_reviewers' and r.get('reviewers') and not r.get('prevent_self_review', False)
                for r in environment['protection_rules']),
            'Configure the publication environment with required reviewers before dispatching Release; self approval must be allowed for a sole maintainer')


def scan_security(manifest, output):
    from dependency_maintenance import default_host, scan
    verify_payload(read(manifest), manifest.parent, source())
    image = default_host(ROOT, read(ROOT / 'maintenance-policy.json'))
    status = 'failed'
    try:
        scan(ROOT, image)
        status = 'passed'
    finally:
        report = ROOT / 'artifacts/dependency-security/result.json'
        write(output / 'security.json', {'status': status, 'source': source(), 'payloadSha256': sha256(manifest),
              'target': image, 'observedAt': now().isoformat(),
              'report': read(report) if report.exists() else {'error': 'No scanner report'}})
        if report.parent.exists():
            shutil.copytree(report.parent, output / 'reports', dirs_exist_ok=True)


def security_current(directory):
    """Authenticate binding first; freshness alone may require one scan refresh."""
    from dependency_maintenance import default_host
    manifest = directory / 'payload/candidate-payload.json'
    record = read(directory / 'security/security.json')
    require(record['status'] == 'passed' and record['source'] == source() and
            record['payloadSha256'] == sha256(manifest) and
            record['target'] == default_host(ROOT, read(ROOT / 'maintenance-policy.json')), 'Candidate security binding/result mismatch')
    age = now() - timestamp(record['observedAt'])
    require(age >= timedelta(0), 'Security observation is in the future')
    return age <= timedelta(hours=policy()['securityMaxAgeHours'])


def ensure_security(directory, output):
    if security_current(directory):
        shutil.copytree(directory / 'security', output, dirs_exist_ok=False)
        print('Reusing current candidate security; no scan repeated.')
    else:
        scan_security(directory / 'payload/candidate-payload.json', output)


def timing_summary():
    run, jobs = run_metadata(os.environ['GITHUB_RUN_ID'])
    elapsed = (now() - timestamp(run['created_at'])).total_seconds()
    target = int(os.environ['CI_BUDGET_SECONDS'])
    lines = [f'Package validation: {source()["commit"]}', '',
             f'Elapsed including queue/setup/transfer: **{elapsed:.1f}s**; target {target}s.', '',
             '| Job | Outcome | Seconds |', '|---|---|---:|']
    for job in jobs:
        if job.get('started_at') and job.get('completed_at'):
            seconds = (timestamp(job['completed_at']) - timestamp(job['started_at'])).total_seconds()
            lines.append(f'| {job["name"]} | {job["conclusion"]} | {seconds:.1f} |')
    print('\n'.join(lines))
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as output:
        output.write('\n'.join(lines) + '\n')
    if elapsed > target:
        raise ValueError('Package CI runtime exceeded its budget; inspect timings and resolve the cause or revise the budget in review.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('find')
    sub.add_parser('import-payload')
    sub.add_parser('assert-environment')
    sub.add_parser('timing')
    sub.add_parser('assert-main').add_argument('--expected-commit', required=True)
    p = sub.add_parser('snapshot'); p.add_argument('--directory', type=Path, default=ROOT / 'artifacts'); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('verify-payload'); p.add_argument('--manifest', type=Path, required=True); p.add_argument('--directory', type=Path, default=ROOT / 'artifacts')
    for name in ('download', 'verify-promotion', 'prepare-trial'):
        p = sub.add_parser(name); p.add_argument('--run-id', required=True); p.add_argument('--output', type=Path, required=True)
        if name == 'verify-promotion':
            p.add_argument('--tag'); p.add_argument('--expected-payload'); p.add_argument('--security-observed-at')
    p = sub.add_parser('security'); p.add_argument('--payload-manifest', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('security-status'); p.add_argument('--directory', type=Path, required=True)
    p = sub.add_parser('ensure-security'); p.add_argument('--directory', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'find': print(find_candidate())
        elif args.command == 'import-payload': import_payload()
        elif args.command == 'assert-environment': assert_environment()
        elif args.command == 'timing': timing_summary()
        elif args.command == 'assert-main':
            require(re.fullmatch('[0-9a-f]{40}', args.expected_commit) and
                    os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and os.environ.get('GITHUB_REF') == 'refs/heads/main' and
                    os.environ.get('GITHUB_SHA') == args.expected_commit == source()['commit'], 'Dispatch main source, expected commit and checkout must agree')
        elif args.command == 'snapshot': snapshot(args.directory, args.output)
        elif args.command == 'verify-payload': verify_payload(read(args.manifest), args.directory, source())
        elif args.command == 'download': fetch_candidate(args.run_id, args.output)
        elif args.command == 'verify-promotion': verify_promotion(args.run_id, args.output, args.tag, args.expected_payload, args.security_observed_at)
        elif args.command == 'security': scan_security(args.payload_manifest, args.output)
        elif args.command == 'security-status':
            with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
                output.write('fresh=' + str(security_current(args.directory)).lower() + '\n')
        elif args.command == 'ensure-security': ensure_security(args.directory, args.output)
        elif args.command == 'prepare-trial':
            from release_trial import prepare
            prepare(args.run_id, args.output)
        return 0
    except (ValueError, RuntimeError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error) + '\n' + RECOVERY, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
