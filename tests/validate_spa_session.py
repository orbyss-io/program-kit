"""Exact emitted SPA session helper: strict types and real browser gestures.

This primitive proof does not qualify native OIDC, a Host or application acceptance.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
sys.path[:0] = [str(ENG), str(ROOT / 'extensions/program-kit-governance/scripts')]
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture
import js_toolchain

REQUIRED = {
    'silent renewal cannot move the original absolute deadline',
    'idle and token expiry both terminate the local session',
    'provider failure cannot restore locally cleared authentication',
    'native provider dispatch stays in the original gesture stack after synchronous clearing',
    'asynchronous local clearing cannot dispatch a provider operation',
    'actual browser popup observes the original trusted gesture and cleared local state',
    'cross-tab coordination sends only the fixed signed-out event',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--install-browser', action='store_true', help='Explicit pinned browser preparation; CI may also install its owned Linux dependencies')
    args = parser.parse_args(); engines = args.engines.split(',')
    if not engines or len(set(engines)) != len(engines) or set(engines) - {'chromium', 'firefox', 'webkit'}:
        parser.error('Select distinct supported engines')
    template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/web-profiles'
    common, spa = template / 'common/eng/web', template / 'spa-pkce/eng/web'
    directory = ROOT / 'artifacts/tests/spa-session' / uuid.uuid4().hex[:8]; directory.mkdir(parents=True)
    for name in ('package.json', 'package-lock.json', 'tsconfig.json'): shutil.copy2(common / name, directory / name)
    (directory / 'tests').mkdir()
    sources = (spa / 'spa-session.ts', spa / 'tests/spa-session.spec.ts')
    for source in sources: shutil.copy2(source, directory / source.relative_to(spa))
    inputs = (*sources, *(common / name for name in ('package.json', 'package-lock.json', 'tsconfig.json')))
    config = "import { defineConfig } from '@playwright/test'; export default defineConfig({testDir:'./tests',workers:1,use:{trace:'off',screenshot:'off',video:'off'},projects:" + json.dumps([{'name': name, 'use': {'browserName': name}} for name in engines]) + '});\n'
    (directory / 'playwright.config.ts').write_text(config, encoding='utf-8')
    node, node_version = js_toolchain.resolve_node(ROOT, (ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.nvmrc').read_text().strip(), 'node', 'auto')
    if node is None: raise ValueError('Prepare the active shared managed Node before this check')
    npm, npm_version = js_toolchain.resolve_npm(ROOT, node, (ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.npm-version').read_text().strip(), 'npm')
    if npm is None: raise ValueError('Prepare the active shared managed npm before this check')
    environment, _, _ = js_toolchain.trust_environment(ROOT, js_toolchain.require_writable_cache(ROOT / 'artifacts/spa-session-npm-cache'))
    environment['PATH'] = str(node.parent) + os.pathsep + environment.get('PATH', '')
    environment['PLAYWRIGHT_BROWSERS_PATH'] = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', str(ROOT / 'artifacts/cache/playwright-browsers'))
    result = {'schemaVersion': 1, 'status': 'running', 'engines': engines,
        'scope': __doc__, 'requiredCasesPerEngine': sorted(REQUIRED),
        'toolchain': {'node': node_version, 'npm': npm_version},
        'sourceSha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    def run(arguments, label, timeout=240):
        observed = foundation_fixture.captured(arguments, directory, directory / label, timeout=timeout, environment=environment)
        if observed['exitCode'] or not observed['cleanupComplete'] or not observed['logsDrained']:
            raise ValueError('SPA session ' + label + ' failed; inspect ' + str(directory))
    try:
        run(npm + ['ci', '--ignore-scripts', '--no-audit', '--no-fund', '--strict-ssl=true', '--fetch-retries=0', '--fetch-timeout=30000'], 'restore')
        cli = str(directory / 'node_modules/@playwright/test/cli.js')
        if args.install_browser:
            run([str(node), cli, 'install', *engines, *(['--with-deps'] if sys.platform.startswith('linux') else [])], 'browsers', 600)
        run([str(node), str(directory / 'node_modules/typescript/bin/tsc'), '--noEmit'], 'typecheck')
        run([str(node), cli, 'test', '--reporter=json'], 'execution')
        report = json.loads((directory / 'execution/stdout.log').read_text(encoding='utf-8'))
        observed = {engine: set() for engine in engines}
        def visit(suite):
            for spec in suite.get('specs', []):
                for test in spec['tests']:
                    project = test['projectName']
                    if project not in observed or test.get('status') != 'expected' or len(test['results']) != 1 or test['results'][0]['status'] != 'passed':
                        raise ValueError('Required SPA test failed, skipped, retried or has an unknown project')
                    if spec['title'] in observed[project]: raise ValueError('Duplicate required SPA test')
                    observed[project].add(spec['title'])
            for child in suite.get('suites', []): visit(child)
        visit(report)
        if any(cases != REQUIRED for cases in observed.values()): raise ValueError('Required SPA case identities missing or substituted')
        if any(hashlib.sha256(p.read_bytes()).hexdigest() != result['sourceSha256'][p.relative_to(ROOT).as_posix()] for p in inputs):
            raise ValueError('Shipping SPA sources changed during execution')
        result.update(status='passed', actualCases={engine: sorted(cases) for engine, cases in observed.items()})
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error)); raise
    finally:
        (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print('SPA session proof: ' + str(directory / 'results.json'))


if __name__ == '__main__': main()
