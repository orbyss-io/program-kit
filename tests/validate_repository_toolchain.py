"""Wrong global Node and missing npm/SDK recover through exact repository-local tools."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ENGINEERING = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
sys.path.insert(0, str(ENGINEERING))
import toolchain
import js_toolchain


class RepositoryToolchainTests(unittest.TestCase):
    def test_missing_tools_do_not_change_pins_or_global_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            required = {'dotnet': '10.0.202', 'node': '24.20.0', 'npm': '11.19.0'}
            legacy = root / 'machine/node.exe'
            legacy.parent.mkdir()
            legacy.write_text('22.19.0')
            pins = {root / 'global.json': json.dumps({'sdk': {'version': required['dotnet']}}),
                    root / '.nvmrc': required['node'], root / '.npm-version': required['npm']}
            for path, text in pins.items(): path.write_text(text)
            def executable(value): return legacy if value == 'node' else None
            def version(command, *_): return Path(command[-1]).read_text()
            with patch.object(js_toolchain, 'executable', side_effect=executable), \
                 patch.object(js_toolchain, 'manager_node', return_value=None), \
                 patch.object(js_toolchain, 'known_node_candidates', return_value=[]), \
                 patch.object(js_toolchain, 'version', side_effect=version):
                resolved, _ = toolchain.resolve(root, required, 'dotnet', 'node', '', 'auto', '')
                self.assertEqual({'dotnet': None, 'node': '22.19.0', 'npm': None}, resolved)
                self.assertEqual(['dotnet', 'node', 'npm'], toolchain.mismatch(required, resolved))
                paths = {'dotnet': root / 'artifacts/tools/dotnet/10.0.202/dotnet.exe',
                         'node': root / 'artifacts/tools/node/24.20.0/node.exe',
                         'npm': root / 'artifacts/tools/npm/11.19.0/node_modules/npm/bin/npm-cli.js'}
                for name, path in paths.items():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(required[name])
                resolved, commands = toolchain.resolve(root, required, 'dotnet', 'node', '', 'auto', '')
                self.assertEqual(required, resolved)
                self.assertEqual([], toolchain.mismatch(required, resolved))
                self.assertEqual(str(paths['dotnet'].resolve()), commands['dotnet'][0])
                self.assertEqual([str(paths['node'].resolve()), str(paths['npm'].resolve())], commands['npm'])
                archive_node = root / 'artifacts/tools/node/node-v24.20.0-win-x64/node.exe'
                archive_npm = root / 'artifacts/tools/npm/11.19.0/package/bin/npm-cli.js'
                archive_node.parent.mkdir(parents=True)
                archive_npm.parent.mkdir(parents=True)
                paths['node'].replace(archive_node)
                paths['npm'].replace(archive_npm)
                resolved, commands = toolchain.resolve(root, required, 'dotnet', 'node', '', 'auto', '')
                self.assertEqual(required, resolved)
                self.assertEqual([str(archive_node.resolve()), str(archive_npm.resolve())], commands['npm'])
                archive_node.replace(paths['node'])
                archive_npm.replace(paths['npm'])
                paths['node'].write_text('22.19.0')
                resolved, _ = toolchain.resolve(root, required, 'dotnet', 'node', '', 'auto', '')
                self.assertIn('node', toolchain.mismatch(required, resolved))
            self.assertEqual('22.19.0', legacy.read_text())
            for path, text in pins.items(): self.assertEqual(text, path.read_text())


if __name__ == '__main__': unittest.main()
