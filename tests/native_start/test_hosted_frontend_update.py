"""Real generated Vite builds must retain immutable assets across UI edits."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
sys.path.insert(0, str(TEMPLATE / 'files/eng'))
from composition_fixture import two_apps
import composition_render
import prepare_hosted_pages
import runtime_closure


class BuildCommands:
    def __init__(self, root):
        self.root = root

    def run(self, arguments, cwd=None, environment=None, timeout=300):
        result = subprocess.run(arguments, cwd=cwd or self.root, env=environment,
                                capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        if result.returncode:
            raise ValueError(result.stdout + '\n' + result.stderr)


class HostedFrontendUpdateTests(unittest.TestCase):
    def test_prepare_source_edit_update_retains_previous_assets_and_mount(self):
        scratch = ROOT / 'artifacts/cache/hosted-bundle-tests'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary)
            graph = two_apps(ROOT)
            generated = composition_render.materialize(root, graph, TEMPLATE)
            frontend = graph['resources']['policy-web']
            for name, (payload, _) in generated.items():
                if name.startswith(frontend['directory'] + '/'):
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(payload)
            for name in ('global.json', '.nvmrc', '.npm-version'):
                shutil.copyfile(TEMPLATE / 'files' / name, root / name)
            shutil.copyfile(ROOT / '.python-version', root / '.python-version')
            builder = 'eng/vendor/foundation-0.3.3/create_hosted_manifest.py'
            (root / builder).parent.mkdir(parents=True)
            shutil.copyfile(TEMPLATE / 'files' / builder, root / builder)
            commands = BuildCommands(root)
            commands.run([sys.executable, str(TEMPLATE / 'files/eng/toolchain.py'), '--repository', str(root)])
            hosts = ['application-host']
            prepare_hosted_pages.build(root, graph, commands, restore=True, selected_hosts=hosts)
            output = root / frontend['directory'] / 'dist'
            original = json.loads((output / 'manifest.json').read_text())
            prior = original['revisions'][-1]
            prior_bytes = {asset['file']: (output / asset['file']).read_bytes() for asset in prior['assets']}
            self.assert_hashed_mount(commands, output, frontend, prior, 'Application foundation')

            # Edit both public UI inputs: each changed asset needs a new path.
            source = root / frontend['directory'] / frontend['entry']
            source.write_text(source.read_text().replace('Application foundation', 'Edited application'), encoding='utf-8')
            styles = source.with_name('styles.css')
            styles.write_text(styles.read_text() + '\nh1 { color: rebeccapurple; }\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'PKC110 frontend inputs changed'):
                prepare_hosted_pages.admission(root, graph, 'policy-web')
            prepare_hosted_pages.build(root, graph, commands, selected_hosts=hosts)
            updated = json.loads((output / 'manifest.json').read_text())
            self.assertNotEqual(original['currentRevision'], updated['currentRevision'])
            self.assertEqual([prior['id'], updated['currentRevision']], [item['id'] for item in updated['revisions']])
            self.assertEqual(prior, updated['revisions'][0])
            current = updated['revisions'][-1]
            self.assert_hashed_mount(commands, output, frontend, current, 'Edited application')
            self.assert_hashed_mount(commands, output, frontend, prior, 'Application foundation')
            self.assertTrue(set(prior_bytes).isdisjoint(asset['file'] for asset in current['assets']))
            for name, payload in prior_bytes.items():
                self.assertEqual(payload, (output / name).read_bytes())
            for revision in updated['revisions']:
                for asset in revision['assets']:
                    self.assertEqual(asset['sha256'], runtime_closure.sha256(output / asset['file']))
            admission = prepare_hosted_pages.admission(root, graph, 'policy-web')
            self.assertEqual(updated['currentRevision'], admission['CurrentRevision'])

    def assert_hashed_mount(self, commands, output, frontend, revision, heading):
        entry = revision['vite'][frontend['entry']]
        self.assertTrue(entry['isEntry'])
        self.assertTrue(entry['css'])
        for name in [entry['file'], *entry['css']]:
            self.assertRegex(name, r'^assets/[^/]+-[A-Za-z0-9_-]+\.(js|css)$')
        # Import both revisions as actual ES modules, checking the runtime seam.
        script = '''
            const entry = await import(process.argv[1]);
            if (typeof entry.mount !== 'function') throw new Error('mount export missing');
            globalThis.document = { createElement: () => ({}) };
            const root = { replaceChildren: (...children) => { root.children = children; } };
            await entry.mount(root);
            if (root.children[0].textContent !== process.argv[2]) throw new Error('wrong revision mounted');
        '''
        commands.run(['node', '--input-type=module', '-e', script, (output / entry['file']).as_uri(), heading])


if __name__ == '__main__':
    unittest.main()
