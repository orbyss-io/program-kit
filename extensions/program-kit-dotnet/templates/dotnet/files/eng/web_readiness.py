"""Read-only admission for an explicitly prepared local web test suite."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import js_toolchain


def check(repository: Path, evidence: Path) -> None:
    _, environment = js_toolchain.context(repository, evidence)
    commands = json.loads(evidence.read_text(encoding='utf-8'))['commands']
    suite = repository / 'eng/web'
    # Absolute local imports prevent npm exec, npx, global executables or a
    # missing package from acquiring anything during verification.
    probe = r'''
const fs = require('node:fs'), path = require('node:path');
const suite = process.argv[1];
const declared = require(path.join(suite, 'package.json')).devDependencies;
for (const [name, version] of Object.entries(declared)) {
  const installed = require(path.join(suite, 'node_modules', name, 'package.json'));
  if (installed.version !== version) throw new Error('Prepared dependency differs: ' + name);
}
const primary = path.join(suite, 'node_modules', '@playwright/test');
const playwright = require(require.resolve('playwright', { paths: [primary] }));
const browser = playwright.chromium.executablePath();
if (!fs.statSync(browser).isFile()) throw new Error('Prepared Chromium binary is absent');
'''
    result = subprocess.run(commands['node'] + ['-e', probe, str(suite)], env=environment,
                            cwd=suite, capture_output=True, encoding='utf-8', errors='replace',
                            timeout=30, check=False)
    if result.returncode:
        raise ValueError('PKW106 web test dependencies or Chromium are unprepared/stale. '
                         'Run ./eng/Prepare-Web.ps1 explicitly, then retry ./eng/Test-Web.ps1. '
                         'No package or browser was installed by this check.\n' + result.stderr[-3000:])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path('.'))
    parser.add_argument('--evidence', type=Path, default=Path('artifacts/program-kit/toolchain.json'))
    args = parser.parse_args()
    try:
        root = args.repository.resolve()
        check(root, args.evidence if args.evidence.is_absolute() else root / args.evidence)
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
