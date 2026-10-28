"""Actual archive-only intake installation. No product input or coding agent."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import intake_session


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-dir', default='artifacts')
    args = parser.parse_args()
    assets = (ROOT / args.assets_dir).resolve(strict=True)
    if not assets.is_relative_to(ROOT):
        raise ValueError('Test assets must remain under the contributor checkout')
    evidence = ROOT / 'artifacts/intake-install'
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='it-', dir=ROOT / 'artifacts') as directory:
        base = Path(directory).resolve()
        if base.parent != ROOT / 'artifacts' or not base.name.startswith('it-'):
            raise ValueError('Unexpected disposable test boundary')
        record = evidence / base.name; record.mkdir()
        project = base / 'consumer'; project.mkdir()
        intake_session.install_components(shutil.which('specify'), shutil.which('git'), project, record, assets)
        runtime = project / '.specify/extensions/program-kit-governance/scripts'
        for command in ([sys.executable, str(runtime / 'governance_state.py'), 'validate-installation'],):
            result = subprocess.run(command, cwd=project, capture_output=True, text=True, encoding='utf-8', timeout=90)
            (record / 'coherence.log').write_text(result.stdout + result.stderr, encoding='utf-8')
            if result.returncode: raise AssertionError('Installed coherence failed; inspect ' + str(record))
        version = (ROOT / 'VERSION').read_text().strip()
        installed = {}
        for component in ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet'):
            destination = project / '.specify/extensions' / component
            assert not destination.is_symlink() and not (destination / '.specify-dev').exists()
            with zipfile.ZipFile(assets / f'{component}-{version}.zip') as archive:
                # Verify entire transported component payload, including generated
                # release guidance, rather than just a representative source hash.
                for name in archive.namelist():
                    if name.endswith('/'): continue
                    actual = destination / name
                    assert actual.is_file() and actual.read_bytes() == archive.read(name), component + '/' + name
            installed[component] = 'all archive members match installed files'
        assert not (project / '.specify/workflows/program-kit-bootstrap').exists()
        assert (project / intake_session.SKILL).is_file()
        # The installation has no material from any private consumer.
        assert not (project / 'product-idea.md').exists()
        assert (project / '.specify/bundle-records.json').is_file()
        report = {'schemaVersion': 1, 'installed': installed, 'workflow': 'retired; not installed',
                  'coherence': 'passed', 'inputManifest': 'installation-inputs.json',
                  'scope': 'installation only; no intake, bootstrap, provider or coding agent executed'}
        (record / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        print('Archive-only native intake installation passed; retained evidence: ' + str(record))


if __name__ == '__main__':
    main()
