"""Read-only consumer probe: exercise recovery preparation on a disposable evidence copy."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer', required=True)
    parser.add_argument('--run-id', default='bd6be6ca')
    args = parser.parse_args()
    consumer = Path(args.consumer).resolve()
    root = Path(__file__).resolve().parents[1]
    relative_run = Path('.specify/workflows/runs') / args.run_id
    files = set()
    for name in ('bootstrap-approval.json', 'bootstrap-assessment-approval.json'):
        record = json.loads((consumer / '.specify/governance' / name).read_text(encoding='utf-8'))
        files.update(record['artifacts'])
    files.update(str(p.relative_to(consumer)) for p in (consumer / relative_run).rglob('*') if p.is_file())
    for folder in ('.specify/governance', '.specify/memory'):
        files.update(str(p.relative_to(consumer)) for p in (consumer / folder).rglob('*') if p.is_file())
    files.update(['docs/architecture/readiness-report.md', 'docs/architecture/bootstrap-intake.json'])
    for name in (
        '.specify/extensions/program-kit-governance/extension.yml',
        '.specify/extensions/program-kit-building-blocks/extension.yml',
        '.specify/extensions/program-kit-dotnet/extension.yml',
        '.specify/extensions/program-kit-governance/program-kit-governance-config.yml',
        '.specify/extensions/program-kit-governance/program-kit-governance-config.local.yml',
        '.specify/presets/program-kit-governance-preset/preset.yml', '.specify/presets/.registry',
        '.specify/workflows/program-kit-bootstrap/workflow.yml', '.specify/workflows/workflow-registry.json',
        '.specify/bundle-records.json', '.specify/integration.json', '.program-kit/managed.json',
    ):
        if (consumer / name).is_file():
            files.add(name)
    before = {p: digest(consumer / p) for p in files}
    with tempfile.TemporaryDirectory(prefix='program-kit-consumer-recovery-probe-') as temporary:
        copy = Path(temporary)
        for name in files:
            source = (consumer / name).resolve()
            if not source.is_relative_to(consumer):
                raise ValueError(f'Unsafe artifact path: {name}')
            destination = copy / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        # Exercise the patched command directly; no consumer installation or workflow mutation.
        result = subprocess.run([sys.executable, str(root / 'extensions/program-kit-governance/scripts/bootstrap_recovery.py'),
                                 'prepare', '--run-id', args.run_id], cwd=copy, capture_output=True,
                                text=True, encoding='utf-8')
        if result.returncode:
            raise AssertionError(result.stderr or result.stdout)
        original_state = copy / relative_run / 'state.json'
        assert digest(original_state) == digest(consumer / relative_run / 'state.json')
        assert not (copy / '.specify/governance/bootstrap-completion.json').exists()
        frozen = copy / '.specify/governance/bootstrap-recovery' / args.run_id / 'original'
        approval_hash = digest(consumer / '.specify/governance/bootstrap-approval.json')
        assert digest(frozen / approval_hash) == approval_hash
        evidence = {'run_id': args.run_id, 'preparation': 'passed on disposable copy',
                    'state_sha256': digest(original_state),
                    'approval_sha256': digest(consumer / '.specify/governance/bootstrap-approval.json'),
                    'readiness_sha256': digest(consumer / 'docs/architecture/readiness-report.md'),
                    'watched_files': len(before), 'consumer_unchanged': True,
                    'completion_created': False, 'provider_compatibility': 'not established by this probe'}
    assert before == {p: digest(consumer / p) for p in files}, 'Consumer evidence changed during read-only probe'
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
