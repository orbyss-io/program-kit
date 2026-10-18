"""Explicit named-check adapter for this finite package-free .NET lesson.

Build and execution are separate: a failed compile never satisfies a behavioral red.
The caller registers exact source/tool inputs with the native verification owner.
"""
from pathlib import Path
import subprocess
import sys


def main():
    directory = Path(__file__).resolve().parent
    project = directory / 'SnapshotProof.csproj'
    build = subprocess.run(['dotnet', 'build', str(project), '--configuration', 'Release', '--nologo', '-m:1', '-p:UseSharedCompilation=false'],
                           capture_output=True, text=True, encoding='utf-8', timeout=45)
    print(build.stdout, end='')
    print(build.stderr, end='', file=sys.stderr)
    if build.returncode:
        return build.returncode
    print('BUILD_SUCCEEDED_BEFORE_BEHAVIOR', flush=True)
    assembly = directory / 'bin/Release/net10.0/SnapshotProof.dll'
    run = subprocess.run(['dotnet', str(assembly), *sys.argv[1:]], capture_output=True, text=True,
                         encoding='utf-8', timeout=15)
    print(run.stdout, end='')
    print(run.stderr, end='', file=sys.stderr)
    return run.returncode


if __name__ == '__main__':
    raise SystemExit(main())
