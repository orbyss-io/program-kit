"""Trusted base code. Read exact PR blobs via API; never execute submitted data."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.request

try:
    import repair_contract as c
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'extensions/program-kit-governance/scripts'))
    import repair_contract as c


def inspect(api, repository, number, expected_head, expected_base, validator_commit):
    c.require(repository == c.EVIDENCE and type(number) is int and number > 0, 'guardian-repository-or-pr')
    c.require(all(re.fullmatch(r'[0-9a-f]{40}', x) for x in (expected_head, expected_base, validator_commit)), 'guardian-commit')
    pr = api(f'repos/{repository}/pulls/{number}')
    c.require(pr['head']['sha'] == expected_head and pr['base']['sha'] == expected_base and pr['base']['ref'] == 'main'
              and pr['base']['repo']['full_name'] == repository, 'guardian-source-changed')
    commit = api(f'repos/{repository}/git/commits/{expected_head}')
    c.require(len(commit['parents']) == 1, 'guardian-single-addition-commit-required')
    parent = commit['parents'][0]['sha']
    if parent != expected_base:
        comparison = api(f'repos/{repository}/compare/{parent}...{expected_base}')
        c.require(comparison.get('merge_base_commit', {}).get('sha') == parent and
                  comparison.get('status') in ('ahead', 'identical'), 'guardian-parent-not-trusted-base-ancestor')
    files = []
    for page in range(1, 32):
        batch = api(f'repos/{repository}/pulls/{number}/files?per_page=100&page={page}')
        files.extend(batch)
        c.require(len(files) <= c.MAX_FILES, 'guardian-file-count')
        if len(batch) < 100:
            break
    c.require(len(files) == pr['changed_files'] and files, 'guardian-incomplete-inventory')
    prefixes = set()
    for entry in files:
        c.safe_name(entry['filename'])
        parts = entry['filename'].split('/')
        c.require(len(parts) >= 4 and parts[0] == 'requests' and re.fullmatch(c.ID, parts[1]) and
                  re.fullmatch(r'r[1-9][0-9]*', parts[2]) and entry['status'] == 'added', 'guardian-permitted-additions-only')
        prefixes.add('/'.join(parts[:3]))
    c.require(len(prefixes) == 1, 'guardian-one-request-revision')
    prefix = next(iter(prefixes))
    tree = api(f'repos/{repository}/git/trees/{expected_head}?recursive=1')
    c.require(not tree.get('truncated'), 'guardian-tree-incomplete')
    entries = {x['path']: x for x in tree['tree'] if x['path'].startswith(prefix + '/') and x['type'] != 'tree'}
    c.require(set(entries) == {x['filename'] for x in files}, 'guardian-exact-submitted-inventory')
    with tempfile.TemporaryDirectory(prefix='guardian-data-') as temporary:
        total = 0
        for entry in files:
            item = entries[entry['filename']]
            c.require(item['type'] == 'blob' and item['mode'] == '100644' and item['size'] <= c.MAX_FILE, 'guardian-mode-or-budget')
            total += item['size']
            c.require(total <= c.MAX_TOTAL, 'guardian-total-budget')
            blob = api(f"repos/{repository}/git/blobs/{item['sha']}")
            c.require(blob['encoding'] == 'base64' and blob['size'] == item['size'], 'guardian-blob-metadata')
            data = base64.b64decode(blob['content'])
            # Git object identity is independent of request manifest SHA-256.
            import hashlib
            c.require(len(data) == item['size'] and hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == item['sha'], 'guardian-blob-identity')
            path = c.inside(temporary, entry['filename'][len(prefix) + 1:])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        proof = c.guard(temporary, expected_head, validator_commit)
        value = json.loads((Path(temporary) / 'request.json').read_bytes())
        c.require(prefix == f"requests/{value['requestId']}/r{value['revision']}", 'guardian-prefix-identity')
        if value['revision'] > 1:
            previous = api(f"repos/{repository}/contents/requests/{value['requestId']}/r{value['revision'] - 1}/request.json?ref={expected_base}")
            c.require(c.sha(base64.b64decode(previous['content'])) == value['supersedes'], 'guardian-superseded-revision-missing-or-changed')
    latest = api(f'repos/{repository}/pulls/{number}')
    c.require(latest['head']['sha'] == expected_head and latest['base']['sha'] == expected_base, 'guardian-source-moved-during-check')
    return proof


def remote(endpoint):
    request = urllib.request.Request('https://api.github.com/' + endpoint, headers={
        'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json',
        'Cache-Control': 'no-cache, no-store', 'User-Agent': 'program-kit-evidence-guardian'})
    with urllib.request.urlopen(request, timeout=30) as response:
        # Response bounds include base64 overhead. Never download arbitrary URLs.
        data = response.read(4 * c.MAX_TOTAL + 1)
        c.require(len(data) <= 4 * c.MAX_TOTAL, 'guardian-api-response-budget')
        return json.loads(data)


if __name__ == '__main__':
    try:
        result = inspect(remote, os.environ['GUARDIAN_REPOSITORY'], int(os.environ['GUARDIAN_PR']),
                         os.environ['GUARDIAN_HEAD'], os.environ['GUARDIAN_BASE'], os.environ['GUARDIAN_VALIDATOR'])
        print(json.dumps(result, indent=2))
    except Exception:
        # Raw API errors, filenames and content may contain secrets. Keep logs opaque.
        print('PKRF guardian-rejected: inspect inventory, schema, identity, bounds and permitted changes locally', file=sys.stderr)
        raise SystemExit(1)
