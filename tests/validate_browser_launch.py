"""Real selected browser launch/close evidence and bounded failure prerequisite."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
sys.path[:0] = [str(ENG), str(ROOT / 'extensions/program-kit-dotnet/scripts'), str(ROOT / 'extensions/program-kit-governance/scripts')]
import composition_run
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--browser-root', type=Path, default=ROOT / 'artifacts/ui-browser/web/generated/program-kit/acceptance/tests')
    args = parser.parse_args()
    engines = args.engines.split(',')
    if not engines or len(set(engines)) != len(engines) or set(engines) - {'chromium', 'webkit', 'firefox'}:
        parser.error('Select distinct supported browser engines')
    directory = ROOT / 'artifacts/tests/browser-launch' / uuid.uuid4().hex[:8]
    directory.mkdir(parents=True)
    browser_root = args.browser_root.resolve()
    selected = json.loads((browser_root / 'package.json').read_text())
    actual = json.loads((browser_root / 'node_modules/playwright/package.json').read_text())['version']
    assert actual == selected['devDependencies']['@playwright/test']
    source = (ENG / 'web/composition-readiness.mjs').read_text()
    library = (browser_root / 'node_modules/playwright/index.mjs').as_uri()
    source = source.replace("from 'playwright'", 'from ' + json.dumps(library))
    script = directory / 'launch.mjs'; script.write_text(source)
    plan = directory / 'plan.json'; output = directory / 'result.json'
    plan.write_text(json.dumps({'engines': engines, 'launchOnly': True, 'hosts': []}))
    run = foundation_fixture.captured(['node', str(script), str(plan), str(output)], ROOT, directory / 'positive-process', timeout=180)
    if run['exitCode'] != 0 or not run['cleanupComplete'] or not run['logsDrained']:
        raise ValueError('Selected real browser launch failed; inspect ' + str(output))
    result = json.loads(output.read_text())
    assert result['status'] == 'ready' and result['checks'] == []
    assert result['launches'] == [{'engine': engine, 'launched': True, 'closed': True} for engine in engines]
    assert result['planSha256'] == hashlib.sha256(plan.read_bytes()).hexdigest()
    (directory / 'positive-plan.json').write_bytes(plan.read_bytes())
    # A discovered existing file that is not an executable exercises real OS launch failure.
    sentinel = directory / 'PRIVATE_BROWSER_DIAGNOSTIC_SENTINEL.exe'; sentinel.write_text('not executable')
    failing = source.replace("import { chromium, webkit, firefox }", "import { chromium as actualChromium, webkit, firefox }")
    failing = failing.replace('const engines = { chromium, webkit, firefox };',
        'const chromium = { launch: () => actualChromium.launch({ executablePath: ' + json.dumps(str(sentinel)) + ', headless: true }) };\nconst engines = { chromium, webkit, firefox };')
    script.write_text(failing)
    plan.write_text(json.dumps({'engines': ['chromium'], 'launchOnly': True, 'hosts': []}))
    run = foundation_fixture.captured(['node', str(script), str(plan), str(output)], ROOT, directory / 'negative-process', timeout=180)
    assert run['exitCode'] == 2 and run['cleanupComplete'] and run['logsDrained']
    failed = json.loads(output.read_text())
    assert failed['status'] == 'failed' and failed['launches'] == []
    assert failed['failure'] == {'engine': 'chromium', 'phase': 'launch'}
    assert 'PRIVATE_BROWSER_DIAGNOSTIC_SENTINEL' not in output.read_text() + (directory / 'negative-process/stdout.log').read_text() + (directory / 'negative-process/stderr.log').read_text()
    (directory / 'negative-plan.json').write_bytes(plan.read_bytes())
    (directory / 'negative-result.json').write_text(json.dumps(failed, indent=2))
    (directory / 'positive-result.json').write_text(json.dumps(result, indent=2))
    # Acquisition and launch use Commands' one owned cache; fail launch before later effects.
    command = composition_run.Commands(directory, directory / 'processes')
    assert command.environment['PLAYWRIGHT_BROWSERS_PATH'] == str(directory / 'artifacts/cache/browsers')
    calls = []
    class Boundary:
        environment = command.environment
        def run(self, arguments, **kwargs): calls.append((arguments, kwargs))
    with patch.object(composition_run, 'browser_engines', return_value=engines), \
         patch.object(composition_run.qualification, 'npm_command', return_value=(['npm', 'ci'], {})), \
         patch.object(composition_run.qualification, 'playwright_command', side_effect=lambda root, args: ['node', 'cli.js', *args]), \
         patch.object(composition_run, 'browser_check', side_effect=ValueError('launch prerequisite failed')):
        try: composition_run.prepare_browsers(directory, {}, {}, Boundary(), directory)
        except ValueError as error: assert str(error) == 'launch prerequisite failed'
        else: raise AssertionError('Failed launch was admitted')
    assert calls[1][0][-len(engines):] == engines
    assert len(calls) == 2  # no acquisition or launch retry
    toolchain = directory / 'artifacts/program-kit/toolchain.json'; toolchain.parent.mkdir(parents=True)
    toolchain.write_text('{"observed":"test boundary"}')
    graph = {'defaultEnvironment': 'local', 'environments': {'local': {'resources': {}}}}
    class Receipt:
        environment = command.environment
        closed = True
        stale = False
        def run(self, arguments, **kwargs):
            plan_path, result_path = Path(arguments[-2]), Path(arguments[-1])
            payload = {'status': 'ready', 'planSha256': 'stale' if self.stale else hashlib.sha256(plan_path.read_bytes()).hexdigest(),
                       'launches': [{'engine': engine, 'launched': True, 'closed': self.closed} for engine in engines], 'checks': []}
            result_path.write_text(json.dumps(payload))
    receipt = Receipt()
    with patch.object(composition_run, 'browser_engines', return_value=engines):
        admitted = composition_run.browser_check(directory, graph, {}, receipt, directory, launch_only=True)
        assert admitted['status'] == 'ready'
        selected_plan = json.loads((directory / 'browser-launch.json').read_text())
        assert selected_plan['browserCache'] == command.environment['PLAYWRIGHT_BROWSERS_PATH']
        assert selected_plan['toolchainSha256'] == hashlib.sha256(toolchain.read_bytes()).hexdigest()
        for field in ('closed', 'stale'):
            receipt.closed, receipt.stale = field != 'closed', field == 'stale'
            try: composition_run.browser_check(directory, graph, {}, receipt, directory, launch_only=True)
            except ValueError: pass
            else: raise AssertionError('Incomplete or stale browser launch receipt was admitted')
    print('Selected real launch/close, unlaunchable-file redaction, cache/engine/failure boundary passed; evidence: ' + str(directory))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
