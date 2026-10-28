"""Read-only historical proxy markers; simulated evidence supplies no authority.

The same-session bootstrap workflow adapter and all worker/engine dispatch are retired.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import proxy_intake

DIRECTORY = Path('.specify/proxy-bootstrap')
BINDING = DIRECTORY / 'session.json'
ENVIRONMENT = 'PROGRAM_KIT_PROXY_BOOTSTRAP_SESSION'
MODE = 'simulated-proxy'

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def binding(root):
    root = root.resolve()
    value = load(root / BINDING)
    if (value.get('kind') != 'same-session-proxy-bootstrap' or value.get('authority') != 'none'
            or value.get('root') != str(root) or value.get('independentLiveWorker') is not False
            or not value.get('runId', '').startswith('proxy-')):
        raise ValueError('Invalid or relocated proxy bootstrap binding')
    for name, key in ((proxy_intake.MARKER, 'proxySha256'),
                      (proxy_intake.INTAKE, 'intakeSha256'),
                      (Path('.intake-session-owner'), 'ownerSha256'),
                      (Path('product-idea.md'), 'scenarioSha256')):
        if proxy_intake.digest(root / name) != value[key]:
            raise ValueError('Proxy bootstrap input changed: ' + name.as_posix())
    return value


def active(root, run_id=None):
    """Only an explicit, root-bound proxy invocation can consume simulated evidence."""
    if not os.environ.get(ENVIRONMENT):
        return False
    value = binding(root)
    if os.environ[ENVIRONMENT] != value['session'] or (run_id and run_id != value['runId']):
        raise ValueError('Proxy bootstrap invocation does not match its bound session/run')
    return True


def require_active(root, run_id=None):
    if not active(root, run_id):
        raise ValueError('Simulated proxy evidence is valid only inside its explicit bootstrap rehearsal')



def pending(root):
    value = binding(root)
    request = load(root / DIRECTORY / 'pending.json')
    state = load(root / '.specify/workflows/runs' / value['runId'] / 'state.json')
    if (request['runId'] != value['runId'] or state['status'] != 'paused'
            or state['current_step_id'] != request['step']):
        raise ValueError('Proxy request is not the current paused native step')
    return request


def main() -> int:
    from workflow_lifecycle import RETIREMENT
    print(RETIREMENT, file=sys.stderr)
    return 2

if __name__ == '__main__':
    raise SystemExit(main())
