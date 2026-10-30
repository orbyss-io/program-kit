"""Compile the four-file contract with the selected public analyzer, then reject combined valid C#."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT/'extensions/program-kit-dotnet/templates/dotnet/files'
EXAMPLE = ROOT/'extensions/program-kit-dotnet/references/examples/contract-layout'
sys.path.insert(0, str(TEMPLATE/'scripts'))
from central_packages import central_package_versions
from source_quality import guidance


def main():
    evidence = ROOT/'artifacts/contract-layout'/uuid.uuid4().hex
    evidence.mkdir(parents=True)
    consumer = ROOT/'artifacts/t'/('layout-'+uuid.uuid4().hex[:12])
    consumer.mkdir(parents=True)
    selected = central_package_versions(TEMPLATE)['orbyss.foundation.analyzers']
    result = {'status': 'running', 'selectedAnalyzerVersion': selected, 'consumer': str(consumer),
              'scope': 'Public selected analyzer and synthetic contract layout; no consumer acceptance', 'steps': []}
    env = os.environ.copy()
    env.update(NUGET_PACKAGES=str(consumer/'artifacts/nuget'), NUGET_HTTP_CACHE_PATH=str(consumer/'artifacts/http'),
               DOTNET_CLI_HOME=str(ROOT/'artifacts/cache/contract-layout/dotnet'),
               MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0', PYTHONUTF8='1')
    def run(name, arguments, success=True):
        observed = subprocess.run(arguments, cwd=consumer, env=env, capture_output=True,
                                  text=True, encoding='utf-8', timeout=180)
        for stream in ('stdout', 'stderr'):
            (evidence/(name+'.'+stream+'.log')).write_text(getattr(observed, stream), encoding='utf-8')
        result['steps'].append({'name': name, 'command': arguments, 'exitCode': observed.returncode})
        assert (observed.returncode == 0) == success, str(evidence/(name+'.stdout.log'))
        return observed.stdout+observed.stderr
    try:
        for file in EXAMPLE.iterdir():
            if file.is_file():
                shutil.copyfile(file, consumer/file.name)
        for name in ('global.json', '.editorconfig'):
            shutil.copyfile(TEMPLATE/name, consumer/name)
        (consumer/'NuGet.config').write_text('<configuration><packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
        pin = '-p:SelectedAnalyzerVersion='+selected
        run('restore', ['dotnet', 'restore', 'ContractLayout.csproj', '--configfile', 'NuGet.config', pin, '--disable-build-servers'])
        run('locked', ['dotnet', 'restore', 'ContractLayout.csproj', '--configfile', 'NuGet.config', '--locked-mode', pin, '--disable-build-servers'])
        build = ['dotnet', 'build', 'ContractLayout.csproj', '--no-restore', pin, '--disable-build-servers', '-m:1']
        run('four-separate-files', build)
        files = sorted(consumer.glob('*.cs'))
        assert {f.name for f in files} == {'ILabelRule.cs', 'LabelRequest.cs', 'LabelDecision.cs', 'LabelFailure.cs'}
        (consumer/'Combined.cs').write_text('namespace ProgramKit.Examples.Contracts;\n'+'\n'.join(
            re.sub(r'^namespace ProgramKit\.Examples\.Contracts;\s*', '', f.read_text(), count=1) for f in files))
        for file in files:
            file.unlink()  # Only these four owned fixture files; originals remain in the reference.
        diagnostic = run('combined-types-negative', build, success=False)
        assert 'error ORB1003' in diagnostic and not re.search(r'error CS\d+', diagnostic), diagnostic
        archive = Path(env['NUGET_PACKAGES'])/'orbyss.foundation.analyzers'/selected/('orbyss.foundation.analyzers.'+selected+'.nupkg')
        with zipfile.ZipFile(archive) as package:
            analyzers = {name: hashlib.sha256(package.read(name)).hexdigest() for name in package.namelist()
                         if name.startswith('analyzers/') and name.endswith('.dll')}
            assert analyzers
            for name in analyzers:
                assert hashlib.sha256((archive.parent/name).read_bytes()).hexdigest() == analyzers[name]
        result.update(status='passed', cases=['four-types-four-files-build', 'combined-valid-CSharp-ORB1003'],
                      packageSha256=hashlib.sha256(archive.read_bytes()).hexdigest(), analyzerAssets=analyzers,
                      nativeLockSha256=hashlib.sha256((consumer/'packages.lock.json').read_bytes()).hexdigest(),
                      sourceSha256={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in [Path(__file__), TEMPLATE/'.editorconfig', TEMPLATE/'config/program-kit/build/ProgramKit.Packages.props', *EXAMPLE.iterdir()] if p.is_file()})
        print('Native selected analyzer contract layout: '+str(evidence/'results.json'))
        return 0
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error))
        raise
    finally:
        (evidence/'results.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
