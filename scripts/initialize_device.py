"""Initializer device preflight before repository mutation. Downloads policy/data, never tools."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import sys
import tempfile
import subprocess
import urllib.request

PINS = 'extensions/program-kit-dotnet/templates/dotnet/files'
INPUTS = ('.nvmrc', '.npm-version', 'global.json', 'eng/device_toolchain.py', 'eng/js_toolchain.py')


def check(project: Path, pins: Path, authority: str) -> None:
    print('Program Kit initial device readiness; authoritative pins: ' + authority, flush=True)
    spec = importlib.util.spec_from_file_location('initialize_device_policy', pins / 'eng/device_toolchain.py')
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    policy.contributor(project, pins_directory=pins, exact_specify=False)
    print('PKT000 shared device tools are ready; initialization may continue. '
          'Repository setup, profile-specific prerequisites and future pin changes retain their own checks.', flush=True)


def initialize(project: Path, ref: str, release: Path | None = None) -> None:
    if not re.fullmatch(r'v\d+\.\d+\.\d+', ref):
        raise ValueError('Device preflight requires the exact initializer release tag')
    if release is not None:
        if (release / 'VERSION').read_text(encoding='utf-8').strip() != ref[1:]:
            raise ValueError('Device preflight source version differs from initializer tag')
        check(project, release / PINS, str(release / PINS) + ' (' + ref + ')')
        return
    # These are the same release-owned diagnostic sources and pins used after installation.
    # No SDK, runtime, npm, Python or Spec Kit binary/package is downloaded or installed here.
    base = 'https://raw.githubusercontent.com/orbyss-io/program-kit/' + ref + '/' + PINS
    with tempfile.TemporaryDirectory(prefix='program-kit-device-preflight-') as directory:
        pins = Path(directory)
        for name in INPUTS:
            path = pins / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(base + '/' + name, timeout=30) as response:
                path.write_bytes(response.read())
        check(project, pins, base)


def invoke_native(project,ref,release,launcher,arguments):
    """Use exact release-owned capture around the installed native CLI, with no tool acquisition."""
    if not re.fullmatch(r'v\d+\.\d+\.\d+',ref):raise ValueError('Exact initializer release tag required')
    if release is not None:
        if (release/'VERSION').read_text().strip()!=ref[1:]:raise ValueError('Initializer bridge release version differs')
        bridge=release/'scripts/invoke_specify.py'
        return subprocess.run([sys.executable,str(bridge),'--launcher',str(launcher),'--',*arguments],cwd=project).returncode
    files=('scripts/invoke_specify.py','extensions/program-kit-governance/scripts/render_profile.py',
           'extensions/program-kit-dotnet/templates/dotnet/files/eng/owned_scratch.py')
    with tempfile.TemporaryDirectory(prefix='program-kit-native-capture-') as directory:
        root=Path(directory)
        for relative in files:
            path=root/relative;path.parent.mkdir(parents=True,exist_ok=True)
            with urllib.request.urlopen('https://raw.githubusercontent.com/orbyss-io/program-kit/'+ref+'/'+relative,timeout=30) as response:
                payload=response.read(1_048_577)
                if len(payload)>1_048_576:raise ValueError('Oversized native capture source')
                path.write_bytes(payload)
        return subprocess.run([sys.executable,str(root/'scripts/invoke_specify.py'),'--launcher',str(launcher),'--',*arguments],cwd=project).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--ref', required=True)
    parser.add_argument('--release-root', type=Path, help='Use the explicitly staged same-version release or source checkout')
    parser.add_argument('--native-launcher',type=Path)
    parser.add_argument('--native-arguments',nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.native_launcher or args.native_arguments is not None:
            if not args.native_launcher or not args.native_arguments:raise ValueError('Exact native launcher and arguments are required')
            return invoke_native(args.project_root.resolve(),args.ref,args.release_root.resolve() if args.release_root else None,
                                 args.native_launcher,args.native_arguments)
        initialize(args.project_root.resolve(), args.ref, args.release_root.resolve() if args.release_root else None)
        return 0
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        print('Initialization paused before repository changes. Complete user-terminal remediation, '
              'refresh the session and rerun this initializer. Failed policy/pin downloads also block; '
              'do not substitute local tool distributions or a different release.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
