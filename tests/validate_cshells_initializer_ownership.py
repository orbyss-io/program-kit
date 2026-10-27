"""On-demand native CShells 0.0.31 resource-owner/admission workaround regression.

Compiles the actual shipped example in an isolated synthetic project. No consumer,
database, browser, publisher action or device toolchain installation is involved.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
sys.path[:0] = [str(ENG), str(ROOT / 'extensions/program-kit-governance/scripts')]
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture
from owned_fixture import FixtureDirectory

FIXTURE = ROOT / 'tests/fixtures/cshells-initializer-ownership'
EXAMPLE = ROOT / 'extensions/program-kit-dotnet/references/examples/cshells-initializer-ownership'
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
EXPECTED = {
    'shipped-async-owner-happy-and-teardown',
    'asynchronous-partial-startup-failure',
    'entered-admission-cancellation',
    'reload-with-active-tracked-scope',
    'failed-replacement-preserves-old-generation',
    'canceled-replacement-preserves-old-generation',
    'sync-owner-nondisposable-admission',
    'scoped-admission-cleanup',
    'transient-admission-cleanup',
    'known-bad-phased-singleton',
    'known-bad-matching-singleton-alias',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def main():
    started = time.monotonic()
    evidence = ROOT / 'artifacts/cshells-initializer-ownership' / uuid.uuid4().hex[:12]
    evidence.mkdir(parents=True)
    sources = [Path(__file__), *sorted(FIXTURE.glob('*')), *sorted(EXAMPLE.glob('*.cs')),
               TEMPLATE / 'global.json', ENG / 'foundation_fixture.py',
               ROOT / 'extensions/program-kit-governance/scripts/compatibility_process.py']
    sources = [path for path in sources if path.is_file()]
    before = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    require({path.name for path in EXAMPLE.glob('*.cs')} == {
        'ResourceFeature.cs', 'ResourceAdmission.cs', 'SyntheticResourceOwner.cs',
        'SyntheticResourceObservation.cs', 'ResourceLifetime.cs'},
        'Expected the actual five shipped example source files')
    result = {'status': 'running', 'scope': __doc__, 'sourceSha256': before, 'steps': [],
              'upstreamFixClaim': False, 'consumerAcceptanceClaim': False,
              'packageVersion': '0.0.31', 'sdkInstallationPerformed': False}

    def write():
        result['elapsedSeconds'] = round(time.monotonic() - started, 3)
        (evidence / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')

    try:
        with FixtureDirectory(prefix='cshells-ownership-', native=True) as temporary:
            work = Path(temporary)
            shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
            (work / 'shipped-example').mkdir()
            for source in EXAMPLE.glob('*.cs'):
                shutil.copyfile(source, work / 'shipped-example' / source.name)
            for name in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props'):
                (work / name).write_text('<Project/>', encoding='utf-8')
            shutil.copyfile(TEMPLATE / 'global.json', work / 'global.json')
            (work / 'NuGet.config').write_text('''<configuration>
<packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources>
<packageSourceMapping><clear/><packageSource key="nuget.org"><package pattern="*"/></packageSource></packageSourceMapping>
<fallbackPackageFolders><clear/></fallbackPackageFolders>
</configuration>''', encoding='utf-8')
            environment = dict(os.environ, NUGET_PACKAGES=str(work / 'cache'),
                NUGET_HTTP_CACHE_PATH=str(work / 'http-cache'), DOTNET_CLI_HOME=str(work / 'dotnet-home'),
                DOTNET_CLI_USE_MSBUILD_SERVER='0', MSBUILDDISABLENODEREUSE='1', PYTHONUTF8='1')

            def run(label, arguments, timeout=60):
                command = ['dotnet', *map(str, arguments)]
                directory = evidence / label
                observed = foundation_fixture.captured(command, work, directory, timeout=timeout, environment=environment)
                result['steps'].append({'id': label, 'command': command, **observed})
                write()
                require(observed['exitCode'] == 0 and observed['cleanupComplete'] and observed['logsDrained'],
                        'Native ownership check failed at ' + label + '; inspect ' + str(directory))

            project = work / 'OwnershipProbe.csproj'
            run('restore', ['restore', project, '--configfile', work / 'NuGet.config', '--disable-build-servers'])
            run('locked-restore', ['restore', project, '--locked-mode', '--configfile', work / 'NuGet.config', '--disable-build-servers'])
            provenance = []
            for identity in ('cshells', 'cshells.abstractions'):
                directory = work / 'cache' / identity / '0.0.31'
                archive = directory / (identity + '.0.0.31.nupkg')
                native = json.loads((directory / '.nupkg.metadata').read_text(encoding='utf-8'))
                require(native.get('source') == 'https://api.nuget.org/v3/index.json', 'Native CShells archive source differs')
                with zipfile.ZipFile(archive) as package:
                    names = [name for name in package.namelist() if name.endswith('.nuspec')]
                    require(len(names) == 1, 'CShells archive identity is ambiguous')
                    document = ET.fromstring(package.read(names[0]))
                    fields = {node.tag.rsplit('}', 1)[-1]: node.text for node in document.iter()}
                    repository = next(node.attrib for node in document.iter() if node.tag.rsplit('}', 1)[-1] == 'repository')
                    require(fields['id'].lower() == identity and fields['version'] == '0.0.31', 'CShells archive identity changed')
                    require(repository.get('commit') == 'b7611aadb49789d3b282749df18ffe68d0eacec5', 'Selected CShells source commit changed')
                shutil.copyfile(archive, evidence / archive.name)
                provenance.append({'id': fields['id'], 'version': fields['version'], 'sha256': sha(archive),
                    'repository': repository, 'nativeSource': native['source'],
                    'nativeMetadataSha256': sha(directory / '.nupkg.metadata')})
            result['packages'] = provenance
            shutil.copyfile(work / 'packages.lock.json', evidence / 'packages.lock.json')
            result['lockSha256'] = sha(work / 'packages.lock.json')
            run('build', ['build', project, '-c', 'Release', '--no-restore', '--disable-build-servers', '--nologo'])
            run('native-cases', [work / 'bin/Release/net10.0/OwnershipProbe.dll', evidence / 'observations.json'], timeout=90)
            observations = json.loads((evidence / 'observations.json').read_text(encoding='utf-8'))
            require(observations.get('status') == 'passed', 'Native ownership cases did not all pass')
            names = [case.get('name') for case in observations.get('cases', [])]
            require(len(names) == len(EXPECTED) and set(names) == EXPECTED, 'Native ownership case identity/count changed')
            result['cases'] = observations['cases']
        result['ownedScratchCleanupObserved'] = True
        require(before == {str(path.relative_to(ROOT)): sha(path) for path in sources}, 'Bound source inputs changed during execution')
        require(not any(path.is_file() and path.name not in {Path(key).name for key in before}
                        for path in EXAMPLE.glob('*.cs')), 'Shipped example inputs changed during execution')
        result['status'] = 'passed'
        write()
        print('Native CShells ownership workaround: 11 safety/control cases passed; evidence: ' + str(evidence / 'results.json'))
        return 0
    except BaseException as error:
        result.update(status='failed', diagnostic=type(error).__name__ + ': ' + str(error))
        write()
        raise


if __name__ == '__main__':
    raise SystemExit(main())
