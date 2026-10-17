"""Qualify the actual installed typed operation through emitted native tooling."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import sys
import tarfile
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
sys.path[:0] = [str(ENG), str(ROOT / 'extensions/program-kit-governance/scripts')]
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture
import oasdiff_cli


def official_oasdiff(directory, version):
    """Explicit CI project-tool preparation, never a device runtime installation."""
    system = {'Windows': 'windows', 'Linux': 'linux'}.get(platform.system())
    architecture = {'AMD64': 'amd64', 'x86_64': 'amd64', 'aarch64': 'arm64', 'ARM64': 'arm64'}.get(platform.machine())
    if system is None or architecture is None: raise ValueError('Pinned comparison tool needs a qualified Windows/Linux architecture')
    name = 'oasdiff_' + version + '_' + system + '_' + architecture + '.tar.gz'
    url = 'https://api.github.com/repos/oasdiff/oasdiff/releases/tags/v' + version
    headers = {'User-Agent': 'Program-Kit-deterministic-project-tool'}
    if os.environ.get('GITHUB_TOKEN'): headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        raw = response.read(4 * 1_048_576 + 1)
    if len(raw) > 4 * 1_048_576: raise ValueError('Official comparison release metadata exceeds its bound')
    release = json.loads(raw)
    if release['tag_name'] != 'v' + version or release.get('draft') or release.get('prerelease'):
        raise ValueError('Comparison release does not match its exact stable pin')
    (directory / 'official-release.json').write_bytes(raw)
    for identity in ('checksums.txt', name):
        matches = [a for a in release['assets'] if a['name'] == identity]
        if len(matches) != 1: raise ValueError('Exact official comparison asset is missing or ambiguous')
        asset = matches[0]
        expected_prefix = 'https://github.com/oasdiff/oasdiff/releases/download/v' + version + '/'
        if not asset['browser_download_url'].startswith(expected_prefix): raise ValueError('Comparison asset has an unexpected release origin')
        with urllib.request.urlopen(asset['browser_download_url'], timeout=60) as response, (directory / identity).open('xb') as output:
            total = 0; digest = hashlib.sha256()
            while chunk := response.read(1_048_576):
                total += len(chunk)
                if total > 64 * 1_048_576: raise ValueError('Official comparison asset exceeds its bound')
                digest.update(chunk); output.write(chunk)
        if asset.get('digest') != 'sha256:' + digest.hexdigest(): raise ValueError('Official comparison asset digest differs')
    archive = directory / name
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest + '  ' + name not in (directory / 'checksums.txt').read_text(encoding='utf-8'):
        raise ValueError('Official comparison release checksum differs')
    binary = 'oasdiff.exe' if system == 'windows' else 'oasdiff'
    target = directory / binary
    with tarfile.open(archive, 'r:gz') as payload:
        matches = [m for m in payload.getmembers() if m.isfile() and m.name == binary]
        if len(matches) != 1 or matches[0].size > 64 * 1_048_576: raise ValueError('Official binary member is missing, ambiguous or oversized')
        with payload.extractfile(matches[0]) as stream: target.write_bytes(stream.read())
    if system != 'windows': target.chmod(0o755)
    oasdiff_cli.require(target, ROOT, version)
    (directory / 'verified-tool.json').write_text(json.dumps({'version': version, 'release': release['html_url'],
        'releaseId': release['id'], 'archiveSha256': digest, 'binarySha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'deviceInstallationPerformed': False}, indent=2) + '\n', encoding='utf-8')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--oasdiff', type=Path, help='Existing reviewed exact project analysis binary')
    parser.add_argument('--prepare-oasdiff', action='store_true', help='Explicit official exact pinned project-tool preparation')
    parser.add_argument('--prepare-only', action='store_true', help='Tool preparation only; establishes no application execution')
    args = parser.parse_args()
    if bool(args.oasdiff) == args.prepare_oasdiff: parser.error('Select one existing --oasdiff or explicit --prepare-oasdiff')
    directory = ROOT / 'artifacts/tests/typed-operation' / uuid.uuid4().hex[:8]; directory.mkdir(parents=True)
    result = {'schemaVersion': 1, 'status': 'running', 'scope': __doc__, 'productAcceptanceEstablished': False}
    try:
        version = (ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.oasdiff-version').read_text().strip()
        binary = official_oasdiff(directory, version) if args.prepare_oasdiff else args.oasdiff.resolve(strict=True)
        oasdiff_cli.require(binary, ROOT, version)
        result['comparisonTool'] = {'version': version, 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
        if args.prepare_only:
            result.update(status='prepared', operationExecuted=False); return
        arguments = [sys.executable, str(ROOT / 'tests/validate_composition_start.py'), '--execute', '--single-host',
            '--tooling', '--oasdiff', str(binary), '--engines', args.engines]
        observed = foundation_fixture.captured(arguments, ROOT, directory / 'execution', timeout=1800)
        if observed['exitCode'] or not observed['cleanupComplete'] or not observed['logsDrained']:
            raise ValueError('Actual installed typed flow failed; inspect ' + str(directory))
        output = (directory / 'execution/stdout.log').read_text(encoding='utf-8')
        actual = json.loads(output.strip().splitlines()[-1])
        required = ('runtimeExercised', 'toolingExercised', 'actualTypedRequestResponse', 'actualGeneratedTypesAndClient',
            'actualProviderPortResolution', 'actualNondefaultScalarOptions', 'independentDurableWriteObservation',
            'actualHostRestartRetainsEffect', 'actualPackedSettingsMetadata')
        if actual.get('status') != 'passed' or any(actual.get(key) is not True for key in required):
            raise ValueError('Actual required typed-operation obligations missing or unsuccessful')
        consumer = (ROOT / actual['consumer']).resolve()
        if not consumer.is_relative_to(ROOT / 'artifacts/t'): raise ValueError('Typed flow returned an unowned consumer')
        resolved = json.loads((consumer / 'eng/foundation-composition.resolved.json').read_bytes())
        result.update(status='passed', actual=actual, selectedPackages=resolved['packages'], hostImage=resolved['hostImage'])
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error)); raise
    finally:
        (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print('Actual installed typed-operation proof: ' + str(directory / 'results.json'))


if __name__ == '__main__': main()
