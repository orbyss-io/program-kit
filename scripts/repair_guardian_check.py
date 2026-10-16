"""Trusted dispatcher: inspect current PR data and publish one App-owned check.

Only the separately installed App token may call this entry point. Never executes
or imports a submitted file. An interrupted/failed run cannot yield success.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request

try:
    import guardian
except ImportError:
    import repair_evidence_guardian as guardian

CHECK = 'program-kit-evidence/guardian'


def run(api, repository, number, validator):
    guardian.c.require(repository == guardian.c.EVIDENCE and type(number) is int and number > 0
                       and re.fullmatch(r'[0-9a-f]{40}', validator), 'guardian-dispatch-identity')
    pr = api('GET', f'repos/{repository}/pulls/{number}')
    guardian.c.require(pr['state'] == 'open' and pr['base']['ref'] == 'main'
                       and pr['base']['repo']['full_name'] == repository, 'guardian-open-main-pr-required')
    head, base = pr['head']['sha'], pr['base']['sha']
    endpoint = f'repos/{repository}/check-runs'
    check = api('POST', endpoint, {'name': CHECK, 'head_sha': head, 'status': 'in_progress',
                'external_id': f'{number}:{head}:{base}:{validator}'})
    conclusion, proof = 'failure', None
    try:
        proof = guardian.inspect(lambda path: api('GET', path), repository, number, head, base, validator)
        conclusion = 'success'
    except Exception:
        # Never forward submitted strings, API errors or evidence to public logs.
        pass
    api('PATCH', endpoint + '/' + str(check['id']), {'status': 'completed', 'conclusion': conclusion,
        'output': {'title': 'Repair evidence contract ' + conclusion,
                   'summary': json.dumps({'submittedCommit': head, 'baseCommit': base, 'validatorCommit': validator,
                                          'contractVersion': guardian.c.VERSION, 'guardianVersion': guardian.c.GUARDIAN,
                                          'meaning': 'Contract validation only; maintainer content review remains required.'})}})
    return proof


def remote(method, endpoint, payload=None):
    guardian.c.require(endpoint.startswith('repos/' + guardian.c.EVIDENCE + '/'), 'guardian-api-destination')
    request = urllib.request.Request('https://api.github.com/' + endpoint, method=method,
        data=None if payload is None else json.dumps(payload).encode(), headers={
            'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json', 'Cache-Control': 'no-cache, no-store',
            'User-Agent': 'program-kit-evidence-guardian'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(4 * guardian.c.MAX_TOTAL + 1)
        guardian.c.require(len(data) <= 4 * guardian.c.MAX_TOTAL, 'guardian-api-response-budget')
        return json.loads(data)


if __name__ == '__main__':
    try:
        raw = os.environ['GUARDIAN_PR']
        guardian.c.require(bool(re.fullmatch(r'[1-9][0-9]{0,9}', raw)), 'guardian-pr-number')
        if run(remote, os.environ['GUARDIAN_REPOSITORY'], int(raw), os.environ['GUARDIAN_VALIDATOR']) is None:
            raise ValueError('guardian-rejected')
        print('Repair evidence contract passed; maintainer content review remains required.')
    except Exception:
        print('PKRF guardian-check-unavailable-or-rejected; no acceptance established')
        raise SystemExit(1)
