"""Compile the owner example against the qualified selected Foundation and inspect actual HTML.

Native mode uses exact selected package restore and the maintained ui-browser runtime. Prepared
archives can be supplied explicitly. No device installation, provider login or consumer UX claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
EXAMPLE = ROOT / 'extensions/program-kit-dotnet/references/examples/ApplicationAuthenticationPresentation.cs'
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
import building_blocks as blocks


def admit_archive(archive, version, member, raw):
    with zipfile.ZipFile(archive) as payload:
        nuspecs = [item for item in payload.namelist() if item.endswith('.nuspec')]
        if len(nuspecs) != 1: raise ValueError('Prepared Foundation archive identity is ambiguous')
        metadata = ET.fromstring(payload.read(nuspecs[0]))
        versions = [item.text for item in metadata.iter() if item.tag.rsplit('}', 1)[-1] == 'version']
        if versions != [version] or payload.read(member) != raw:
            raise ValueError('Prepared assembly differs from its native exact-version archive')


def unit_checks(directory):
    archive = directory / 'synthetic-admission.nupkg'
    member = 'lib/net10.0/Fixture.dll'
    with zipfile.ZipFile(archive, 'w') as payload:
        payload.writestr('fixture.nuspec', '<package><metadata><version>1.2.3</version></metadata></package>')
        payload.writestr(member, b'owned-native-bytes')
    admit_archive(archive, '1.2.3', member, b'owned-native-bytes')
    for version, raw in [('1.2.4', b'owned-native-bytes'), ('1.2.3', b'changed-native-bytes')]:
        try: admit_archive(archive, version, member, raw)
        except ValueError: pass
        else: raise AssertionError('Stale version or assembly accepted')
    with zipfile.ZipFile(archive, 'a') as payload: payload.writestr('second.nuspec', '<package />')
    try: admit_archive(archive, '1.2.3', member, b'owned-native-bytes')
    except ValueError: pass
    else: raise AssertionError('Ambiguous archive accepted')
    return {'archiveAdmissionCases': 4, 'scope': 'Exact archive/version/assembly admission; no compiled presentation or browser proof.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit', action='store_true', help='Fast package-admission contracts; no package restore or browser launch')
    parser.add_argument('--execute', action='store_true', help='Compile and run native presentation/browser proof')
    parser.add_argument('--baseline-profile', help='Explicit retained qualified profile instead of the current qualified default')
    parser.add_argument('--package-root', type=Path, help='Explicit prepared NuGet package cache matching the selected profile')
    parser.add_argument('--browser-root', type=Path, default=ROOT / 'artifacts/ui-browser/web/generated/program-kit/acceptance/tests')
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    args = parser.parse_args()
    engines = args.engines.split(',')
    if not engines or len(set(engines)) != len(engines) or set(engines) - {'chromium', 'firefox', 'webkit'}:
        parser.error('Select distinct supported browser engines')
    directory = ROOT / 'artifacts/tests/authentication-presentation' / uuid.uuid4().hex[:8]
    directory.mkdir(parents=True)
    evidence = {'scope': __doc__, 'sources': {}, 'assemblies': [], 'commands': [], 'status': 'running'}
    def run(command, timeout=120, expected=0):
        result = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        index = len(evidence['commands'])
        (directory / f'command-{index}.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        evidence['commands'].append({'arguments': command, 'exitCode': result.returncode})
        if result.returncode != expected:
            raise RuntimeError(f'Authentication presentation command {index} failed; inspect {directory}')
        return result.stdout
    try:
        catalog = blocks.new_project_catalog(args.baseline_profile)
        registry = json.loads((blocks.profile_registry() / 'index.json').read_text())
        evidence['profile'] = args.baseline_profile or registry['default']
        evidence['profileOverride'] = args.baseline_profile is not None
        versions = {name: catalog['packages']['nuget:Orbyss.Foundation.' + name]['version'] for name in ['Authentication', 'Web.ProblemDetails']}
        evidence['selectedVersions'] = versions
        evidence['unit'] = unit_checks(directory)
        if not args.execute:
            evidence['status'] = 'passed'; print('Authentication presentation admission passed: ' + str(directory)); return
        for source in [EXAMPLE, ROOT / 'tests/fixtures/authentication-presentation/Probe.cs', ROOT / 'tests/fixtures/authentication-presentation/browser.mjs']:
            shutil.copyfile(source, directory / source.name)
            evidence['sources'][str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
        shutil.copyfile(TEMPLATE / 'files/global.json', directory / 'global.json')
        refs = []
        assemblies = directory / 'admitted-assemblies'; assemblies.mkdir()
        # Direct exact-version references avoid any restore/network/cache mutation. This tests the
        # published port/representation seam; normal package/closure qualification remains separate.
        for name in (['authentication', 'authentication.core', 'web.problemdetails', 'web.problemdetails.core', 'json', 'json.aspnetcore', 'collections.core'] if args.package_root else []):
            version = versions['Authentication']
            if version != versions['Web.ProblemDetails']: raise ValueError('Prepared family requires a coherent selected runtime version')
            package = args.package_root.resolve() / ('orbyss.foundation.' + name) / version
            native = list((package / 'lib/net10.0').glob('*.dll'))
            if len(native) != 1: raise ValueError('Prepared selected Foundation assembly is missing: ' + name)
            archive = package / ('orbyss.foundation.' + name + '.' + version + '.nupkg')
            admit_archive(archive, version, 'lib/net10.0/' + native[0].name, native[0].read_bytes())
            target = assemblies / native[0].name; shutil.copyfile(native[0], target)
            evidence['assemblies'].append({'source': str(native[0]), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'version': version,
                'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest()})
            refs.append(f'<Reference Include="{escape(target.stem)}"><HintPath>{escape(str(target))}</HintPath></Reference>')
        if not args.package_root:
            refs = [f'<PackageReference Include="Orbyss.Foundation.{escape(name)}" Version="{escape(version)}" />' for name, version in versions.items()]
            refs.extend(f'<PackageReference Include="{escape(name)}" Version="{escape(version)}" />' for name, version in blocks.effective_dependency_context(ROOT)['sharedAbi']['pins'].items())
        (directory / 'Presentation.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors><ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally><RestorePackagesWithLockFile>true</RestorePackagesWithLockFile><RestorePackagesPath>nuget/packages</RestorePackagesPath></PropertyGroup><ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App" />' + ''.join(refs) + '</ItemGroup></Project>')
        (directory / 'Directory.Build.props').write_text('<Project />')
        (directory / 'Directory.Build.targets').write_text('<Project />')
        if args.package_root:
            (directory / 'NuGet.Config').write_text('<configuration><packageSources><clear /></packageSources></configuration>')
        else:
            shutil.copyfile(TEMPLATE / 'files/NuGet.config', directory / 'NuGet.Config')
        run(['dotnet', 'restore', 'Presentation.csproj', '--use-lock-file', '--force-evaluate', '--configfile', 'NuGet.Config'])
        run(['dotnet', 'restore', 'Presentation.csproj', '--locked-mode', '--configfile', 'NuGet.Config'])
        output = directory / 'rendered'
        run(['dotnet', 'run', '--project', 'Presentation.csproj', '--no-restore', '--disable-build-servers', '--', str(output)])
        if not args.package_root:
            assets = json.loads((directory / 'obj/project.assets.json').read_text())
            for identity, library in assets['libraries'].items():
                if library['type'] != 'package': continue
                name, version = identity.rsplit('/', 1)
                archive = directory / 'nuget/packages' / library['path'] / (name.lower() + '.' + version.lower() + '.nupkg')
                evidence['assemblies'].append({'identity': identity, 'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest()})
        browser_root = args.browser_root.resolve()
        package = json.loads((browser_root / 'node_modules/playwright/package.json').read_text())
        expected = json.loads((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/eng/web/package.json').read_text())['devDependencies']['@playwright/test']
        if package['version'] != expected: raise ValueError('Prepared Playwright differs from selected exact pin')
        if run(['node', '--version']).strip().removeprefix('v') != (TEMPLATE / 'files/.nvmrc').read_text().strip().removeprefix('v'):
            raise ValueError('Node differs from selected exact pin')
        script = (ROOT / 'tests/fixtures/authentication-presentation/browser.mjs').read_text().replace('__PLAYWRIGHT__', (browser_root / 'node_modules/playwright/index.mjs').as_uri())
        (directory / 'browser.mjs').write_text(script)
        observed = run(['node', 'browser.mjs', str(output), args.engines])
        evidence['browser'] = json.loads(observed)
        evidence['browserVersion'] = package['version']
        authentication_source = TEMPLATE / 'web-profiles/common/eng/web/tests/authentication.spec.ts'
        authentication = authentication_source.read_text()
        hook_start = authentication.index("process.env.PLAYWRIGHT_NO_COPY_PROMPT = '1';")
        hook_end = authentication.index('const identityAuthority')
        hook = authentication[hook_start:hook_end]
        if 'test.afterEach(' not in hook: raise ValueError('Maintained authentication privacy hook is absent')
        secret = 'synthetic-private-credential-' + uuid.uuid4().hex
        test_import = (browser_root / 'node_modules/@playwright/test/index.mjs').as_uri()
        (directory / 'package.json').write_text('{"type":"module"}')
        (directory / 'privacy.spec.ts').write_text(f"import {{expect,test}} from {json.dumps(test_import)};\n" + hook
            + "test('owned credential assertion privacy proof',async({page})=>{await page.setContent('<input aria-label=Credential>');"
            + 'await page.getByLabel("Credential").fill(' + json.dumps(secret) + ');'
            + 'await expect(page.getByLabel("Credential")).toHaveValue("unrelated-public-expectation",{timeout:100});});\n')
        privacy_config = {'testDir': str(directory), 'testMatch': 'privacy.spec.ts', 'workers': 1, 'retries': 0,
            'outputDir': str(directory / 'privacy-results'), 'reporter': [['junit', {'outputFile': str(directory / 'privacy.xml')}]],
            'use': {'browserName': engines[0], 'trace': 'off', 'screenshot': 'off', 'video': 'off'}}
        (directory / 'privacy.config.mjs').write_text('export default ' + json.dumps(privacy_config) + ';\n')
        privacy_index = len(evidence['commands'])
        privacy_stdout = run(['node', str(browser_root / 'node_modules/playwright/cli.js'), 'test', '--config', 'privacy.config.mjs'], expected=1)
        report_bytes = (directory / 'privacy.xml').read_bytes()
        report = ET.fromstring(report_bytes)
        cases = list(report.iter('testcase'))
        if len(cases) != 1 or not any(child.tag in ('failure', 'error') for child in cases[0]):
            raise ValueError('Credential assertion must remain an actual failed test')
        if secret in privacy_stdout or secret in (directory / f'command-{privacy_index}.log').read_text() or secret.encode() in report_bytes:
            raise ValueError('Credential assertion escaped authentication privacy controls')
        if not any(category in report_bytes for category in (b'expect(private authentication assertion)', b'Private authentication check failed; payload suppressed.')):
            raise ValueError('Safe authentication assertion classification disappeared from its failed report')
        if list((directory / 'privacy-results').rglob('error-context.md')):
            raise ValueError('Automatic authentication DOM failure snapshot was retained')
        evidence['privacy'] = {'actualTestExitCode': 1, 'assertionStillFailed': True, 'safeFailureClassificationRetained': True, 'stdoutAndJUnitSecretAbsent': True,
            'automaticFailureDomAbsent': True, 'engine': engines[0], 'maintainedSourceSha256': hashlib.sha256(authentication_source.read_bytes()).hexdigest(),
            'hookSha256': hashlib.sha256(hook.encode()).hexdigest(), 'scope': 'Actual maintained worker hook/reporting with a deliberately failing synthetic credential assertion; no provider/consumer claim.'}
        evidence['status'] = 'passed'
        print('Authentication owner presentation passed; evidence: ' + str(directory))
    except Exception:
        evidence['status'] = 'failed'
        raise
    finally:
        (directory / 'result.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
