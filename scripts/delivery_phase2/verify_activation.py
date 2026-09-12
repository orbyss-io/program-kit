"""Refresh and recheck the existing synthetic activation; never creates a new decision."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_provider import AzureProvider
from azure_transport import AzureTransport
import azure_activation as activation
import azure_planning as planning
from delivery_contract import authority


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    evidence = Path(args.evidence).resolve()
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError('Preserve previous verification evidence')
    root = evidence / 'consumer'
    decision = authority.read(evidence / 'activation-proposal.json')
    profile = authority.read(root / '.program-kit/delivery/profile.json')
    if (profile['azure']['organization'] != 'Unfussiness'
            or profile['azure']['projectId'] != '2dd96afc-aaf1-4cc8-b376-27ea4f84ef03'
            or decision['binding']['repositoryId'] != '204d5894-5d90-4ab6-bb22-b999b88e6a43'):
        raise ValueError('Only the approved synthetic Phase 2 consumer can be refreshed')
    before = {str(path): (root / path).read_bytes() for path in (authority.BINDING, authority.HISTORY)}
    hashes = {}
    for name in ('program-kit-governance', 'program-kit-delivery'):
        source = ROOT / 'extensions' / name
        shutil.copytree(source, root / '.specify/extensions' / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__'))
        for path in source.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    provider = AzureProvider(AzureTransport('Unfussiness'), profile)
    repeated = activation.apply(provider, root, decision, authority.digest(decision),
        'User accepted Phase 2 synthetic per-repository activation and repeat-activation test')
    statuses = {}
    for activity in ('refinement', 'implementation', 'delivery', 'acceptance'):
        result = subprocess.run([sys.executable, str(root / '.specify/extensions/program-kit-delivery/scripts/delivery.py'),
            '--repository', str(root), 'check-admission', '--activity', activity], cwd=root, capture_output=True, text=True)
        statuses[activity] = {'exitCode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        if result.returncode != (0 if activity == 'refinement' else 2):
            raise AssertionError(f'{activity} admission differed: {result.stdout} {result.stderr}')
    for path, content in before.items():
        if (root / path).read_bytes() != content:
            raise AssertionError('Repeated activation altered consumer authority records')
    head, state = planning.state_for(provider)
    unresolved = [key for key, operation in state['operations'].items() if operation['state'] != 'applied']
    if unresolved:
        raise AssertionError('Synthetic acceptance left unresolved dispatches: ' + str(unresolved))
    result = {'repeatActivation': repeated, 'installedAdmission': statuses, 'consumerRecordsPreserved': True,
        'coordinationCommit': head, 'unresolvedOperations': unresolved, 'sourceHashes': hashes,
        'humanPortalCase': 'pending-user-action'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'sourceHashes'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
