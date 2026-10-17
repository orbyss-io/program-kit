"""Publish only a previously verified promotion; never build or run acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from release_candidate import ROOT, api, gh, git, policy, read, require, source, verify_payload


def publication_plan(records, existing, fetch):
    """Idempotent same-byte retries; differing public bytes are irreversible evidence."""
    by_name = {a['name']: a for a in existing}
    require(len(by_name) == len(existing), 'Duplicate existing public assets')
    expected = {r['name'] for r in records}
    require(set(by_name) <= expected, 'Unexpected existing public assets; inspect partial publication')
    missing = []
    for record in records:
        if record['name'] not in by_name:
            missing.append(record['name'])
            continue
        public = fetch(by_name[record['name']])
        require(len(public) == record['size'] and hashlib.sha256(public).hexdigest() == record['sha256'],
                'Differing existing public asset; never clobber: ' + record['name'])
    return missing


def public_bytes(asset):
    return gh('api', '-H', 'Accept: application/octet-stream',
              f'repos/{policy()["repository"]}/releases/assets/{int(asset["id"])}', binary=True)


def existing_release(tag):
    # Distinguish absent release from auth/network failures; only a confirmed 404
    # permits creation. Never treat a failed availability lookup as success.
    import subprocess
    result = subprocess.run(['gh', 'api', f'repos/{policy()["repository"]}/releases/tags/{tag}'], capture_output=True)
    if result.returncode:
        require(b'HTTP 404' in result.stderr, 'Release lookup failed: ' + result.stderr.decode('utf-8', 'replace'))
        return None
    return json.loads(result.stdout)


def verify_public(tag, promotion):
    release = existing_release(tag)
    require(release is not None, 'Published release is missing')
    missing = publication_plan(promotion['assets'], release['assets'], public_bytes)
    require(not missing, 'Published release missing qualified assets: ' + ', '.join(missing))


def publish(tag, directory):
    promotion = read(directory / 'promotion.json')
    require(promotion['source'] == source() and tag == 'v' + source()['version'], 'Promotion source/tag mismatch')
    require(git(ROOT, 'rev-parse', f'refs/tags/{tag}^{{commit}}') == source()['commit'], 'Local publication tag points to another source')
    remote = api(f'repos/{policy()["repository"]}/git/ref/tags/{tag}')['object']
    for _ in range(4):
        if remote['type'] == 'commit': break
        require(remote['type'] == 'tag', 'Unexpected remote tag object')
        remote = api(f'repos/{policy()["repository"]}/git/tags/{remote["sha"]}')['object']
    require(remote['type'] == 'commit' and remote['sha'] == source()['commit'], 'Remote publication tag points to another source')
    verify_payload(read(directory / 'payload/candidate-payload.json'), directory / 'payload', source())
    notes = (directory / 'payload' / ('RELEASE-NOTES-' + source()['version'] + '.md')).read_text(encoding='utf-8')
    notes += '\n\nPackage validation: https://github.com/' + policy()['repository'] + '/actions/runs/' + str(promotion['runId']) + '\n'
    notes_path = directory / 'publication-notes.md'
    notes_path.write_text(notes, encoding='utf-8')
    release = existing_release(tag)
    if release is None:
        # A concurrent creation never authorizes replacing its assets.
        gh('release', 'create', tag, '--repo', policy()['repository'], '--verify-tag',
           '--title', 'Program Kit ' + tag, '--notes-file', notes_path)
        release = existing_release(tag)
    missing = publication_plan(promotion['assets'], release['assets'], public_bytes)
    if missing:
        gh('release', 'upload', tag, '--repo', policy()['repository'],
           *[directory / 'payload' / name for name in missing])
    gh('release', 'edit', tag, '--repo', policy()['repository'], '--notes-file', notes_path)
    verify_public(tag, promotion)


def create_tag(tag, directory):
    promotion = read(directory / 'promotion.json')
    require(promotion['source'] == source() and tag == 'v' + source()['version'], 'Candidate source/tag mismatch')
    # Same-source retries preserve the existing tag. A correction requires a
    # separately reviewed manual recovery; never force, delete, or move here.
    endpoint = f'repos/{policy()["repository"]}/git/ref/tags/{tag}'
    result = subprocess.run(['gh', 'api', endpoint], capture_output=True)
    if result.returncode:
        require(b'HTTP 404' in result.stderr, 'Tag lookup failed: ' + result.stderr.decode('utf-8', 'replace'))
        gh('api', '--method', 'POST', f'repos/{policy()["repository"]}/git/refs',
           '-f', 'ref=refs/tags/' + tag, '-f', 'sha=' + source()['commit'])
    else:
        remote = json.loads(result.stdout)['object']
        for _ in range(4):
            if remote['type'] == 'commit': break
            require(remote['type'] == 'tag', 'Unexpected remote tag object')
            remote = api(f'repos/{policy()["repository"]}/git/tags/{remote["sha"]}')['object']
        require(remote['type'] == 'commit' and remote['sha'] == source()['commit'],
                'Existing stable tag points to another source; obtain approval for manual recovery')
    git(ROOT, 'fetch', 'origin', f'refs/tags/{tag}:refs/tags/{tag}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--verify-public-only', action='store_true')
    parser.add_argument('--create-tag', action='store_true')
    args = parser.parse_args()
    if args.verify_public_only:
        verify_public(args.tag, read(args.directory / 'promotion.json'))
    elif args.create_tag:
        create_tag(args.tag, args.directory)
    else:
        publish(args.tag, args.directory)


if __name__ == '__main__':
    main()
