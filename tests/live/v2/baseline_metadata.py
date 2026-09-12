"""Supervise a baseline npm view using only that consumer's installed runtime behavior."""
import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from live.v2.cli import SECRET_KEYS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--package', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'(?:@[a-z0-9_.-]+/)?[a-z0-9_.-]+', args.package) or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?', args.version):
        raise ValueError('Baseline metadata requires an exact package/version')
    repository = args.repository.resolve()
    evidence = (repository / args.evidence).resolve()
    if not evidence.is_relative_to(repository):
        raise ValueError('Metadata evidence must stay inside the disposable consumer')
    source = repository / '.program-kit/eng/js_toolchain.py'
    spec = importlib.util.spec_from_file_location('baseline_installed_runtime', source)
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    result = runtime.run_npm(repository, repository / '.program-kit/evidence/toolchain.json',
                             ['view', f'{args.package}@{args.version}', '--json'], repository, 180, capture_stdout=True)
    if result.returncode:
        return result.returncode
    output = result.stdout
    for key in SECRET_KEYS:
        if os.environ.get(key):
            output = output.replace(os.environ[key], '[REDACTED]')
    metadata = json.loads(output)
    if metadata.get('name') != args.package or metadata.get('version') != args.version:
        raise ValueError('Baseline returned different metadata')
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps({'baselineSupervisorObservation':True,'metadata':metadata}, indent=2)+'\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
