"""Exercise a real accepted consumer's upgrade on a disposable copy; no agents."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--release-root')
    parser.add_argument('--evidence')
    args = parser.parse_args()
    source = Path(args.consumer).resolve()
    root = Path(__file__).resolve().parents[1]
    release = Path(args.release_root).resolve() if args.release_root else root
    folders = ('.specify', '.agents', 'docs')
    # Capture the actual installed tools and authority, excluding downloaded
    # bundles/caches from the consumer's business-file inventory.
    watched = (*folders, '.program-kit')
    before = {folder: hashes(source / folder) for folder in watched}
    with tempfile.TemporaryDirectory(prefix='program-kit-accepted-upgrade-') as temporary:
        target = Path(temporary)
        for folder in folders:
            if (source / folder).is_dir():
                shutil.copytree(source / folder, target / folder)
        kit = source / '.program-kit'
        if kit.is_dir():
            shutil.copytree(kit, target / '.program-kit', ignore=shutil.ignore_patterns('upgrade', 'cache'))
        runtime = root / '.program-kit/cache/json-schema'
        shutil.copytree(runtime, target / '.program-kit/cache/json-schema', dirs_exist_ok=True)
        # Commands remain mechanical; never dispatch the workflow/agent producer.
        streams = []
        def run(command):
            result = subprocess.run([sys.executable, *map(str, command)], cwd=target,
                                    capture_output=True, text=True, encoding='utf-8',
                                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            streams.append({'command': list(map(str, command)), 'exit_code': result.returncode,
                            'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
        recovery = 'extensions/program-kit-governance/scripts/bootstrap_recovery.py'
        run([release / recovery, 'prepare', '--run-id', args.run_id])
        authority = ['docs/architecture/building-block-selection.json',
                     '.specify/governance/bootstrap-approval.json',
                     '.specify/memory/constitution.md',
                     f'.specify/workflows/runs/{args.run_id}/state.json']
        preserved = {p: (target / p).read_bytes() for p in authority}
        run([root / 'scripts/upgrade_program_kit.py', '--release-root', release,
             '--target', target, '--integration', 'codex'])
        run([target / '.specify' / recovery, 'prepare', '--run-id', args.run_id])
        run([target / '.specify/extensions/program-kit-governance/scripts/governance_state.py', 'validate-installation'])
        assert all((target / p).read_bytes() == data for p, data in preserved.items())
        assert not (target / '.program-kit/building-blocks.lock.json').exists()
        selection = json.loads((target / authority[0]).read_text(encoding='utf-8'))
        assert all(not (target / item['path']).exists() for item in selection['targets'])
        assert not (target / '.specify/governance/bootstrap-completion.json').exists()
        evidence = {'upgrade': 'passed', 'installed_recovery_prepare': 'passed',
                    'installed_coherence': 'passed', 'authority_preserved': True,
                    'lock_created': False, 'targets_materialized': False,
                    'provider_compatibility': 'not evaluated', 'completion_created': False,
                    'streams': streams}
    assert before == {folder: hashes(source / folder) for folder in watched}, 'Original consumer changed during probe'
    evidence['original_consumer_unchanged'] = True
    if args.evidence:
        destination = Path(args.evidence)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in evidence.items() if key != 'streams'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
