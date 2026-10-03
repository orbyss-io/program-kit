"""Test the coordinated core source patch without altering the installed tool."""
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run_patched(script):
    if os.environ.get('PROGRAM_KIT_CORE_SOURCE_FIXTURE') == '1':
        return None
    distribution = importlib.metadata.distribution('specify-cli')
    if distribution.version != '1.0.1':
        raise RuntimeError('The source patch fixture requires the exact Spec Kit 1.0.1 baseline')
    installed = Path(distribution.locate_file('specify_cli'))
    with tempfile.TemporaryDirectory(prefix='program-kit-core-source-') as directory:
        root = Path(directory)
        package = root / 'src/specify_cli'
        shutil.copytree(installed, package)
        assets = installed / 'core_pack'
        for name in ('scripts', 'extensions'):
            shutil.copytree(assets / name, root / name)
        shutil.copytree(assets / 'commands', root / 'templates/commands')
        patch = ROOT / 'patches/spec-kit-1.0.1-python-runtime.patch'
        argv = ['git', 'apply', '--exclude=README.md', '--exclude=docs/**', '--exclude=.github/**', '--exclude=tests/**', str(patch)]
        subprocess.run([*argv[:2], '--check', *argv[2:]], cwd=root, check=True)
        subprocess.run(argv, cwd=root, check=True)
        for name in ('scripts', 'extensions'):
            shutil.copytree(root / name, package / 'core_pack' / name, dirs_exist_ok=True)
        shutil.copytree(root / 'templates/commands', package / 'core_pack/commands', dirs_exist_ok=True)
        environment = dict(os.environ, PROGRAM_KIT_CORE_SOURCE_FIXTURE='1', PYTHONUTF8='1',
            PYTHONPATH=str(root / 'src') + os.pathsep + os.environ.get('PYTHONPATH', ''))
        return subprocess.run([sys.executable, str(script), *sys.argv[1:]], env=environment, check=False).returncode
