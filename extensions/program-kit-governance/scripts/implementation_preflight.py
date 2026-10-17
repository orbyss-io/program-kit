"""Validate the planned compilation graph and supply implementation guidance."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from phase_obligations import inside, check, render


def foundation_readiness(root):
    source = root / 'eng/foundation-composition.json'
    if not source.is_file():
        selection = root / 'docs/architecture/building-block-selection.json'
        accepted = json.loads(selection.read_text(encoding='utf-8')) if selection.is_file() else {}
        runtime_compositions = {'api_baseline', 'browser_bff', 'browser_spa', 'hosted_application_pages'}
        if (root / 'eng/foundation-settings.contract.json').is_file() or (
                accepted.get('status') == 'Accepted' and any(
                    row.get('composition') in runtime_compositions for row in accepted.get('instances', []))):
            raise ValueError('PKM003 populate/migrate eng/foundation-composition.json from the Accepted runtime '
                             'bindings and prepare it before starting consumer implementation.')
        return
    # Preparation is explicit. Implementation reuses the same generated native
    # run/readiness operation as a human and the golden consumer test.
    sys.path.insert(0, str(root / 'eng'))
    import device_toolchain
    python = device_toolchain.require_python(root)
    result = subprocess.run([str(python), 'eng/composition_run.py', 'run'], cwd=root, timeout=300)
    if result.returncode:
        raise ValueError('Foundation readiness failed. Use the preserved native diagnostic; '
                         'complete explicit composition preparation before implementing consumer features.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--stage', choices=('setup','source'), default='source', help='Setup permits native project materialization; source requires evaluated selected projects. Neither consumes governance receipts')
    parser.add_argument('--operation', help='Operation explicitly permitted by scoped deferral, or active repair')
    parser.add_argument('--repair', action='store_true', help='Repair/diagnose the active presented outcome only')
    parser.add_argument('--configuration', default='Debug')
    parser.add_argument('--framework', help='Select the applicable target for a multi-target coding context')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        result = check(root, inside(root, args.feature_dir), 'implementation', operation=args.operation, repair=args.repair,
                       configuration=args.configuration, framework=args.framework, coding_stage=args.stage)
        if not args.repair:
            foundation_readiness(root)
        print(render(result, 'implementation'))
        return 0
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print(str(error))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
