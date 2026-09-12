"""Explicit synthetic installed-consumer activation in the approved Azure Phase 2 project."""
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
from delivery_contract import authority
from delivery import prepare
import governance_state
import schema_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--graph-results', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError('Preserve existing activation evidence; use its proposal for recovery')
    output.mkdir(parents=True)
    root = output / 'consumer'
    root.mkdir()
    source_profile = ROOT / 'artifacts/delivery-phase2/profile.json'
    profile = authority.read(source_profile)
    if profile['azure']['organization'] != 'Unfussiness' or profile['azure']['projectId'] != '2dd96afc-aaf1-4cc8-b376-27ea4f84ef03':
        raise ValueError('Activation acceptance is confined to the approved private Phase 2 project')
    provider = AzureProvider(AzureTransport('Unfussiness'), profile)
    repos = provider.api.list(f'/{provider.project}/_apis/git/repositories')
    code = next(r for r in repos if r['name'] == 'ProgramKit.Delivery.Phase2')
    teams = provider.api.list(f'/_apis/projects/{provider.project}/teams')
    team = next(t for t in teams if t['name'] == 'ProgramKit.Delivery.Phase2 Team')
    for name in ('program-kit-governance', 'program-kit-delivery'):
        shutil.copytree(ROOT / 'extensions' / name, root / '.specify/extensions' / name)
    shutil.copytree(schema_runtime.runtime_path(), schema_runtime.runtime_path(root),
                    ignore=shutil.ignore_patterns('__pycache__'))
    roadmap = root / 'docs/architecture/specification-roadmap.md'
    roadmap.parent.mkdir(parents=True)
    roadmap.write_text('### SPC-001: Synthetic receiving integration\n' + ''.join(
        f'- **{key}**: {"Ready" if key == "Status" else "Synthetic accepted fixture scope"}\n'
        for key in sorted(governance_state.REQUIRED_RECORD_FIELDS)), encoding='utf-8')
    snapshot = root / '.program-kit/delivery/profile.json'
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(source_profile.read_bytes())
    graph = authority.read(Path(args.graph_results))
    prefix = graph['runId']
    binding = {'schemaVersion': 1, 'recordType': 'binding', 'state': 'prepared', 'space': profile['space'],
        'repositoryId': code['id'], 'teamId': team['id'], 'provider': 'azure', 'activationId': None,
        'profile': {'repositoryId': provider.coord['repositoryId'], 'commit': 'ce64fa9388c364c015f85c88f4c4462aa25e6310',
            'path': 'delivery/profile.json', 'sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
            'snapshot': '.program-kit/delivery/profile.json'},
        'artifactPaths': {'roadmap': 'docs/architecture/specification-roadmap.md'},
        'teamDefaults': {'area': None, 'iteration': None},
        'workBindings': {'SPC-001': {'requirementId': prefix + '-R', 'executionMode': 'delegated', 'taskId': prefix + '-T'}}}
    prepare(root, binding)
    decision = activation.prepare(provider, root, binding)
    (output / 'activation-proposal.json').write_text(json.dumps(decision, indent=2), encoding='utf-8')
    source = 'User accepted Phase 2 synthetic per-repository activation and repeat-activation test'
    activated = activation.apply(provider, root, decision, authority.digest(decision), source)
    before = (root / authority.HISTORY).read_bytes()
    repeated = activation.apply(provider, root, decision, authority.digest(decision), source)
    if (root / authority.HISTORY).read_bytes() != before:
        raise AssertionError('Repeat activation changed immutable local history')
    cli = root / '.specify/extensions/program-kit-delivery/scripts/delivery.py'
    statuses = {}
    for activity in ('refinement', 'implementation', 'delivery', 'acceptance'):
        result = subprocess.run([sys.executable, str(cli), '--repository', str(root), 'check-admission', '--activity', activity],
                                cwd=root, capture_output=True, text=True)
        statuses[activity] = {'exitCode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        expected = 0 if activity == 'refinement' else 2
        if result.returncode != expected:
            raise AssertionError(f'{activity} admission differed: {result.stdout} {result.stderr}')
    evidence = {'activation': activated, 'repeat': repeated, 'repositoryId': code['id'], 'teamId': team['id'],
        'installedAdmission': statuses, 'historyPreserved': True, 'humanPortalCase': 'pending-user-action'}
    (output / 'results.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps(evidence))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
