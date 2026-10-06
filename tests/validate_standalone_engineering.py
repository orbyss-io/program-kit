"""Build, run behavior checks and pack a disposable app after deleting governance."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    artifacts = ROOT / 'artifacts/standalone-engineering'
    artifacts.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    sdk = ROOT / 'artifacts/tools/dotnet/10.0.202'
    if (sdk / ('dotnet.exe' if os.name == 'nt' else 'dotnet')).is_file():
        env['DOTNET_ROOT'] = str(sdk)
        env['PATH'] = str(sdk) + os.pathsep + env.get('PATH','')
    env['MSBUILDDISABLENODEREUSE'] = '1'
    env['DOTNET_CLI_USE_MSBUILD_SERVER'] = '0'
    commands = []
    with tempfile.TemporaryDirectory(prefix='app-', dir=artifacts) as temporary:
        root = Path(temporary)
        def write(relative, content):
            path = root / relative
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding='utf-8')
        def run(command, expected=0):
            if command[0] == 'dotnet' and (sdk / ('dotnet.exe' if os.name == 'nt' else 'dotnet')).is_file():
                command[0] = str(sdk / ('dotnet.exe' if os.name == 'nt' else 'dotnet'))
            start = time.perf_counter()
            result = subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,
                                    encoding='utf-8',errors='replace',timeout=300)
            record = {'command':command,'exitCode':result.returncode,'elapsedSeconds':round(time.perf_counter()-start,3)}
            commands.append(record)
            (artifacts/f'{len(commands):02d}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
            if expected is not None and result.returncode != expected:
                raise AssertionError(str(record)+'\n'+result.stdout+result.stderr)
            return result
        run([sys.executable,str(ROOT/'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
             '--target',str(root),'--profile-selected','--foundation-host-accepted',
             '--building-block-sources-approved','--web-profile','none'])
        run([sys.executable, 'eng/repository_architecture.py', '--manifest', 'eng/architecture.json', '--planned'])
        write('eng/architecture.json', json.dumps({'runtimeComposition': {'projects': [
            {'path': 'src/Slots.Core/Slots.Core.csproj', 'role': 'provider'}]}}))
        invalid = run([sys.executable, 'eng/repository_architecture.py', '--manifest', 'eng/architecture.json', '--planned'], expected=2)
        assert 'Core project role cannot be relabeled' in invalid.stderr
        write('eng/architecture.json', json.dumps({'runtimeComposition': {'projects': [
            {'path': 'src/Slots/Slots.csproj', 'role': 'composition',
             'persistenceOwnerNamespaces': ['Slots.Persistence']}], 'bindings': []}}))
        invalid = run([sys.executable, 'eng/repository_architecture.py', '--manifest', 'eng/architecture.json', '--planned'], expected=2)
        assert 'namespace waiver' in invalid.stderr
        write('App.slnx','<Solution><Project Path="src/Slots.Core/Slots.Core.csproj" /><Project Path="tests/Slots.Tests/Slots.Tests.csproj" /></Solution>')
        write('src/Slots.Core/Slots.Core.csproj','<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><PackageId>Slots.Core</PackageId></PropertyGroup></Project>')
        write('src/Slots.Core/Slots.cs','''namespace Slots;
/// <summary>Defines a pure domain admission policy.</summary>
public static class Policy
{
    /// <summary>Admits only available positive capacity.</summary>
    public static bool Admit(int capacity) => capacity > 0;
}
''')
        write('tests/Slots.Tests/Slots.Tests.csproj','<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><IsPackable>false</IsPackable></PropertyGroup><ItemGroup><ProjectReference Include="../../src/Slots.Core/Slots.Core.csproj" /></ItemGroup></Project>')
        write('tests/Slots.Tests/Program.cs','''if (!Slots.Policy.Admit(1) || Slots.Policy.Admit(0) || Slots.Policy.Admit(-1))
    throw new Exception("Domain admission behavior failed");
System.IO.Directory.CreateDirectory("artifacts/tests");
System.IO.File.WriteAllText("artifacts/tests/domain.xml", "<testsuite><testcase classname='Slots' name='capacity_admission'/></testsuite>");
''')
        write('eng/architecture.json',json.dumps({'schemaVersion':1,'runtimeComposition':{'projects':[
            {'path':'src/Slots.Core/Slots.Core.csproj','role':'core'},
            {'path':'tests/Slots.Tests/Slots.Tests.csproj','role':'test'}]}}))
        write('eng/verify.ps1','''$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Build.ps1') -SkipReleaseBundle -LockedMode
if (-not $?) { throw 'Build failed' }
dotnet run --project tests/Slots.Tests/Slots.Tests.csproj -c Release --no-build
if ($LASTEXITCODE -ne 0) { throw 'Domain behavior failed' }
''')
        # Use a normal package source, optionally the already restored exact package.
        feed = ROOT/'artifacts/dotnet-engineering/packages'
        if list((feed/'orbyss.foundation.analyzers/0.2.4').glob('*.nupkg')):
            from xml.sax.saxutils import escape
            write('NuGet.config','<configuration><packageSources><clear/><add key="cached-package" value="'+escape(str(feed))+'"/></packageSources></configuration>')
        write('docs/architecture/decisions/accepted.md','Accepted domain ownership; unchanged.')
        write('.specify/governance/bootstrap-completion.json','{"status":"Completed"}')
        write('specs/001-slots/spec.md','Reserve slots; active unfinished feature.')
        write('specs/001-slots/obligation-review.json','{"basis":"obsolete"}')
        write('.program-kit/evidence/old-proof.json','{"exit_code":0,"old":true}')
        # Remove only these explicitly resolved disposable directories.
        for relative in ('.specify','.program-kit','docs','specs'):
            path=(root/relative).resolve()
            assert path.parent == root.resolve()
            shutil.rmtree(path)
        run(['dotnet','restore','App.slnx','--configfile','NuGet.config','--force-evaluate','--verbosity','quiet'])
        run([shutil.which('pwsh') or shutil.which('powershell'),'-NoProfile','-File','eng/Invoke-RepositoryVerification.ps1'])
        assert list((root/'artifacts/packages').rglob('Slots.Core.*.nupkg'))
        assert (root/'artifacts/tests/domain.xml').is_file()
        assert (root/'artifacts/tests/architecture.xml').is_file()
        # Current wrong code, not a receipt, must prevent acceptance.
        write('src/Slots.Core/Slots.cs','''namespace Slots;
/// <summary>Defines a deliberately wrong admission policy.</summary>
public static class Policy
{
    /// <summary>Incorrectly admits zero capacity.</summary>
    public static bool Admit(int capacity) => capacity >= 0;
}
''')
        failed=run([shutil.which('pwsh') or shutil.which('powershell'),'-NoProfile','-File','eng/Invoke-RepositoryVerification.ps1'],expected=None)
        assert failed.returncode != 0, 'Wrong application behavior was accepted'
        result={'governanceDeleted':True,'codingAgentsStarted':False,'commands':commands,
                'applicationChecksPassedBeforeMutation':True,'wrongBehaviorRejected':True,
                'plannedRelabelAndNamespaceWaiverRejected':True}
        (artifacts/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print('Standalone restore/build/behavior/architecture/pack passed; wrong behavior rejected. Timings: '+str([c['elapsedSeconds'] for c in commands]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
