"""Actual selected renderer source + native Vite runtime in real browser palette checks.

This deliberately qualifies the renderer seam, not package host activation or a
clean device. No publisher source is edited and no registry package is published.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'extensions/program-kit-dotnet/scripts'), str(TEMPLATE / 'files/eng'),
                str(ROOT / 'extensions/program-kit-governance/scripts')]
from composition_fixture import two_apps
import composition_render as render
import prepare_hosted_pages
import foundation_qualification as qualification
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture
from native_start.test_hosted_frontend_update import BuildCommands
from owned_fixture import native_path

PROFILE = 'foundation-0.3.3-build-0.3.1-exporter-0.2.5-forms-0.2.1-localization-0.1.2'
SOURCE_NAMES = ('HostedPageRendering.cs', 'HostedPageRevision.cs', 'HostedBrandLocale.cs', 'HostedViteChunk.cs',
                'HostedAssetDescriptor.cs', 'AdmittedHostedRevision.cs', 'AdmittedHostedPageRoute.cs', 'HostedPageAdmission.cs')


def browser_matrix(args, directory, current, index, provenance, baseline, timings):
    output = directory / 'rendered'
    browser_root = args.browser_root.resolve()
    packages = {name: json.loads((browser_root / 'node_modules' / name / 'package.json').read_text())['version']
                for name in ('playwright', '@axe-core/playwright')}
    selected = json.loads((browser_root / 'package.json').read_text())
    if packages['playwright'] != selected['devDependencies']['@playwright/test'] or packages['@axe-core/playwright'] != selected['devDependencies']['@axe-core/playwright']:
        raise ValueError('Prepared browser harness differs from its exact selected pins')
    script = (ROOT / 'tests/fixtures/hosted-palette/browser.mjs').read_text()
    script = script.replace('__PLAYWRIGHT__', (browser_root / 'node_modules/playwright/index.mjs').as_uri())
    script = script.replace('__AXE__', (browser_root / 'node_modules/@axe-core/playwright/dist/index.mjs').as_uri())
    script = script.replace('__PRESENTATION_RECORDING__', Path(native_path(ROOT / 'tests/fixtures/hosted-palette/presentation-recording.mjs')).as_uri())
    (directory / 'browser.mjs').write_text(script)
    environment = dict(os.environ)
    (directory / 'timings.json').write_text(json.dumps(timings, indent=2))
    browser_started = time.monotonic()
    observed = foundation_fixture.captured(['node', 'browser.mjs', str(output), args.engines], directory,
                                          directory / ('browser-process-' + uuid.uuid4().hex[:8]),
                                          environment=environment, timeout=180)
    if observed['exitCode'] != 0 or not observed['cleanupComplete'] or not observed['logsDrained']:
        raise ValueError('Hosted palette browser matrix failed; inspect preserved process and result evidence in ' + str(directory))
    timings['browserMatrixSeconds'] = round(time.monotonic() - browser_started, 3)
    result = json.loads((output / 'result.json').read_text())
    (directory / 'provenance.json').write_text(json.dumps({'selectedProfile': PROFILE, 'sourceCommit': index['sourceCommit'],
        'sources': provenance, 'sdk': json.loads((directory / 'global.json').read_text())['sdk'], 'browserPackages': packages,
        'browserCache': environment.get('PLAYWRIGHT_BROWSERS_PATH', 'operator default cache'), 'viteRevision': current['id'],
        'baselineCommit': '711293b2dda187616891df11fe760a3d5d0cf5f5', 'baselineStylesSha256': hashlib.sha256(baseline).hexdigest(), 'timings': timings,
        'scope': 'Compiled exact selected renderer sources with actual native Vite output; framework renderer seam, no full host activation or clean device claim.',
        'result': result}, indent=2))
    print('Hosted palette browser checks passed; evidence: ' + str(directory))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--browser-root', type=Path, default=ROOT / 'artifacts/ui-browser/web/generated/program-kit/acceptance/tests')
    parser.add_argument('--prepared', type=Path, help='Reuse a preserved disposable renderer/native build fixture for browser-only repairs.')
    args = parser.parse_args()
    engines = args.engines.split(',')
    if not engines or len(set(engines)) != len(engines) or set(engines) - {'chromium', 'webkit', 'firefox'}:
        parser.error('Select distinct supported browser engines')
    directory = args.prepared.resolve() if args.prepared else ROOT / 'artifacts/tests/hosted-palette' / uuid.uuid4().hex[:8]
    if not directory.is_relative_to(ROOT / 'artifacts/tests/hosted-palette'):
        parser.error('Prepared fixture must be inside artifacts/tests/hosted-palette')
    directory.mkdir(parents=True, exist_ok=bool(args.prepared))
    commands = BuildCommands(directory)
    started = time.monotonic()
    timings = {'infrastructureRepairSeconds': 0, 'infrastructureRepairScope': 'No infrastructure repair performed; existing SDK/Node/browser runtime and operator caches disclosed.'}
    registry = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles'
    index_path = registry / 'candidates' / PROFILE / 'knowledge/index.json'
    index = json.loads(index_path.read_text())
    provenance = []
    for name in SOURCE_NAMES:
        path = 'src/Orbyss.Foundation.Web.HostedPages/' + name
        rows = [row for row in index['documents'] if row.get('publisherPath') == path]
        if len(rows) != 1: raise ValueError('Exact selected renderer source is absent or ambiguous: ' + path)
        row = rows[0]
        raw = (registry / row['path']).read_bytes()[row['byteOffset']:row['byteOffset'] + row['byteLength']]
        if hashlib.sha256(raw).hexdigest() != row['sha256']: raise ValueError('Selected renderer source hash mismatch')
        if args.prepared:
            if (directory / name).read_bytes() != raw: raise ValueError('Prepared selected renderer source differs')
        else: (directory / name).write_bytes(raw)
        provenance.append(row)
    if args.prepared:
        current = json.loads((directory / 'web/policy-web/dist/manifest.json').read_text())['revisions'][-1]
        timings = json.loads((directory / 'timings.json').read_text())
        baseline = subprocess.run(['git', 'show', '711293b2dda187616891df11fe760a3d5d0cf5f5:extensions/program-kit-dotnet/templates/dotnet/hosted-pages/web/src/styles.css'], cwd=ROOT, capture_output=True, timeout=30, check=True).stdout
        return browser_matrix(args, directory, current, index, provenance, baseline, timings)
    for name in ('global.json', '.nvmrc', '.npm-version'):
        shutil.copyfile(TEMPLATE / 'files' / name, directory / name)
    shutil.copyfile(ROOT / '.python-version', directory / '.python-version')
    shutil.copyfile(ROOT / 'tests/fixtures/hosted-palette/Program.cs', directory / 'Program.cs')
    (directory / 'Palette.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup><ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App" /></ItemGroup></Project>')
    (directory / 'NuGet.Config').write_text('<configuration><packageSources><clear /></packageSources></configuration>')
    output = directory / 'rendered'
    commands.run(['dotnet', 'run', '--project', 'Palette.csproj', '--', str(output)])
    graph = two_apps(ROOT)
    frontend = graph['resources']['policy-web']
    for name, (raw, _) in render.materialize(directory, graph, TEMPLATE).items():
        if name.startswith(frontend['directory'] + '/'):
            target = directory / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
    builder = directory / 'eng/vendor/foundation-0.3.3/create_hosted_manifest.py'
    builder.parent.mkdir(parents=True)
    shutil.copyfile(TEMPLATE / 'files/eng/vendor/foundation-0.3.3/create_hosted_manifest.py', builder)
    commands.run([sys.executable, str(TEMPLATE / 'files/eng/toolchain.py'), '--repository', str(directory)])
    npm, npm_environment = qualification.npm_command(directory, ['ci', '--ignore-scripts', '--fetch-retries=0', '--fetch-timeout=30000'])
    commands.run(npm, cwd=directory / frontend['directory'], environment=npm_environment, timeout=120)
    timings['preparationSeconds'] = round(time.monotonic() - started, 3)
    styles = directory / frontend['directory'] / 'src/styles.css'
    repaired = styles.read_bytes()
    baseline = subprocess.run(['git', 'show', '711293b2dda187616891df11fe760a3d5d0cf5f5:extensions/program-kit-dotnet/templates/dotnet/hosted-pages/web/src/styles.css'],
                              cwd=ROOT, capture_output=True, timeout=30, check=True).stdout
    styles.write_bytes(baseline)
    before_started = time.monotonic()
    prepare_hosted_pages.build(directory, graph, commands, selected_hosts=['application-host'])
    timings['beforePreparedBuildSeconds'] = round(time.monotonic() - before_started, 3)
    dist = directory / frontend['directory'] / 'dist'
    original = json.loads((dist / 'manifest.json').read_text())['revisions'][-1]
    original_vite = original['vite'][frontend['entry']]
    shutil.copyfile(dist / original_vite['file'], output / 'before-runtime.js')
    (output / 'before-runtime.css').write_bytes(b'\n'.join((dist / name).read_bytes() for name in original_vite['css']))
    styles.write_bytes(repaired)
    after_started = time.monotonic()
    prepare_hosted_pages.build(directory, graph, commands, selected_hosts=['application-host'])
    timings['afterPreparedBuildSeconds'] = round(time.monotonic() - after_started, 3)
    manifest = json.loads((dist / 'manifest.json').read_text())
    current = manifest['revisions'][-1]
    vite = current['vite'][frontend['entry']]
    shutil.copyfile(dist / vite['file'], output / 'runtime.js')
    (output / 'runtime.css').write_bytes(b'\n'.join((dist / name).read_bytes() for name in vite['css']))
    return browser_matrix(args, directory, current, index, provenance, baseline, timings)


if __name__ == '__main__':
    raise SystemExit(main())
