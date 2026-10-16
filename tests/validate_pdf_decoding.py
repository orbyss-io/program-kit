"""Execute public PdfPig filter adaptation on bounded synthetic inputs only."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import uuid
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT/'extensions/program-kit-dotnet/references/examples/pdf-decoding'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-lock', action='store_true', help='Maintenance only: prepare the exact example lock before ordinary locked validation')
    args = parser.parse_args()
    evidence = ROOT/'artifacts/pdf-decoding'/uuid.uuid4().hex
    evidence.mkdir(parents=True)
    consumer = ROOT/'artifacts/t'/('pdf-'+uuid.uuid4().hex[:12])
    consumer.mkdir(parents=True)
    for file in EXAMPLE.iterdir():
        if file.is_file():
            shutil.copyfile(file, consumer/file.name)
    sdk_source = ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/global.json'
    sdk = json.loads(sdk_source.read_text())['sdk']
    (consumer/'global.json').write_text(json.dumps({'sdk': sdk}))
    (consumer/'NuGet.config').write_text('<configuration><packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
    expected = b''.join(bytes([index % 97])*((index % 31)+1) for index in range(900))
    def encode(data, level=6, strategy=zlib.Z_DEFAULT_STRATEGY):
        stream = zlib.compressobj(level=level, wbits=15, strategy=strategy)
        return stream.compress(data)+stream.flush()
    vectors = {'expected': expected, 'stored': encode(expected, level=0),
               'fixed': encode(expected, strategy=zlib.Z_FIXED), 'dynamic': encode(expected, level=9),
               'content': encode(b'0 0 m 1 1 l S'), 'image': encode(bytes([0, 1, 2, 3]))}
    for name, block in (('stored', 0), ('fixed', 1), ('dynamic', 2)):
        assert (vectors[name][2] >> 1) & 3 == block, 'Fixture must actually exercise '+name+' DEFLATE blocks'
    fixture = evidence/'vectors.json'
    fixture.write_text(json.dumps({key: base64.b64encode(value).decode() for key, value in vectors.items()}))
    env = os.environ.copy()
    # A cold owned cache makes this execution's native locked restore validate the
    # downloaded package content, rather than trusting an old extraction marker.
    env.update(NUGET_PACKAGES=str(consumer/'artifacts/nuget'),
               NUGET_HTTP_CACHE_PATH=str(consumer/'artifacts/http'),
               DOTNET_CLI_HOME=str(ROOT/'artifacts/cache/pdf-decoding/dotnet'),
               MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0',
               DOTNET_CLI_TELEMETRY_OPTOUT='1', PYTHONUTF8='1')
    steps = []
    result = {'status': 'running', 'scope': 'Public-package synthetic filter/content/image regressions only',
              'consumer': str(consumer), 'platform': platform.platform(), 'sdk': sdk,
              'processMemoryLimitQualified': False, 'applicationAcceptance': False, 'paidDispatch': False, 'steps': steps}
    def run(command, timeout=180):
        index = len(steps)
        step = {'command': list(map(str, command)), 'status': 'running'}; steps.append(step)
        observed = subprocess.run(command, cwd=consumer, env=env, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        (evidence/f'{index}.stdout.log').write_text(observed.stdout, encoding='utf-8')
        (evidence/f'{index}.stderr.log').write_text(observed.stderr, encoding='utf-8')
        step.update(status='passed' if observed.returncode == 0 else 'failed', exitCode=observed.returncode)
        assert observed.returncode == 0, observed.stdout+observed.stderr
        return observed.stdout
    try:
        assert run(['dotnet', '--version']).strip() == sdk['version']
        lock = EXAMPLE/'packages.lock.json'
        assert args.prepare_lock or lock.is_file(), 'Prepare the example native lock through maintenance first'
        run(['dotnet', 'restore', 'PdfDecodingExample.csproj', '--configfile', 'NuGet.config',
             '--force-evaluate' if args.prepare_lock else '--locked-mode', '--disable-build-servers'])
        if args.prepare_lock:
            shutil.copyfile(consumer/'packages.lock.json', lock)
        run(['dotnet', 'build', 'PdfDecodingExample.csproj', '--no-restore', '-c', 'Release', '--disable-build-servers', '-m:1'])
        native_lock = json.loads((consumer/'packages.lock.json').read_text())['dependencies']['net10.0']
        assets = json.loads((consumer/'obj/project.assets.json').read_text())['targets']['net10.0']
        executed = {}
        for name, package in assets.items():
            identity, version = name.split('/')
            archive_path = Path(env['NUGET_PACKAGES'])/identity.lower()/version/(identity.lower()+'.'+version+'.nupkg')
            archive_bytes = archive_path.read_bytes()
            metadata = json.loads((archive_path.parent/'.nupkg.metadata').read_text())
            assert metadata['contentHash'] == native_lock[identity]['contentHash'] and metadata['source'] == 'https://api.nuget.org/v3/index.json'
            # Signed NuGet content hashes exclude signature material. The raw
            # archive hash has a different purpose and is retained separately.
            raw_sha512 = base64.b64encode(hashlib.sha512(archive_bytes).digest()).decode()
            assert raw_sha512 == archive_path.with_suffix('.nupkg.sha512').read_text().strip(), 'Downloaded archive changed after native locked restore'
            with zipfile.ZipFile(archive_path) as archive:
                for asset in package.get('runtime', {}):
                    if not asset.endswith('.dll'):
                        continue
                    actual = consumer/'bin/Release/net10.0'/Path(asset).name
                    expected_bytes = archive.read(asset)
                    assert actual.read_bytes() == expected_bytes, 'Executed dependency differs from public locked archive'
                    executed[actual.name] = {'package': name, 'archiveSha256': hashlib.sha256(archive_bytes).hexdigest(),
                                             'asset': asset, 'sha256': hashlib.sha256(expected_bytes).hexdigest()}
        native = json.loads(run(['dotnet', 'bin/Release/net10.0/PdfDecodingExample.dll', str(fixture)], timeout=30))
        required = json.loads((EXAMPLE/'required-cases.json').read_text())
        assert required and len(required) == len(set(required))
        assert native['status'] == 'passed' and native['executedCases'] == len(required)
        assert len(native['cases']) == len(set(native['cases'])) and set(native['cases']) == set(required), 'Required native case removed/substituted'
        result.update(status='passed', native=native, executedRuntime=executed,
            exampleDllSha256=hashlib.sha256((consumer/'bin/Release/net10.0/PdfDecodingExample.dll').read_bytes()).hexdigest(),
            sourceSha256={file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                          for file in [Path(__file__), sdk_source, *EXAMPLE.iterdir()] if file.is_file()},
            packageLockSha256=hashlib.sha256((consumer/'packages.lock.json').read_bytes()).hexdigest())
        print('Public PDF decoding example: '+str(evidence/'results.json'))
        return 0
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error))
        raise
    finally:
        (evidence/'results.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
