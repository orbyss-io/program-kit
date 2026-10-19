"""Install the actual five component packages once; exercise an installed validator.

This bounds the package/registration contract. It does not run bootstrap, agents,
compilation, upgrades, service integrations, or every installed command.
"""
from __future__ import annotations

import argparse
import os
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import zipfile

import yaml
from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition: raise AssertionError(message)


def extract(archive_path, target):
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            path = PurePosixPath(member.orig_filename)
            require(not path.is_absolute() and '..' not in path.parts and ':' not in member.orig_filename and
                    '\\' not in member.orig_filename and ((member.external_attr >> 16) & 0o170000) != 0o120000,
                    'Unsafe component archive entry')
        archive.extractall(target)


def execute(command, cwd, expected=0):
    scratch = cwd / '.fixture-tmp'
    scratch.mkdir(exist_ok=True)
    environment = {**os.environ, 'TEMP':str(scratch), 'TMP':str(scratch), 'PYTHONUTF8':'1'}
    result = subprocess.run([str(x) for x in command], cwd=cwd, env=environment, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=90)
    if result.returncode != expected:
        raise AssertionError(f'{command} returned {result.returncode}, expected {expected}:\n{result.stdout}\n{result.stderr}')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-dir', default='artifacts')
    args = parser.parse_args()
    assets = (ROOT / args.assets_dir).resolve()
    require(assets.is_relative_to(ROOT), 'Package fixture assets must stay within this checkout')
    version = (ROOT / 'VERSION').read_text().strip()
    components = ('program-kit-dotnet','program-kit-building-blocks','program-kit-governance',
                  'program-kit-governance-preset','program-kit-bootstrap')
    for name in (*components, 'program-kit'):
        require((assets / f'{name}-{version}.zip').is_file(), 'Build the actual candidate archives before this smoke')
    import specify_cli
    site_packages = Path(specify_cli.__file__).parent.parent
    bridge = [sys.executable, ROOT / 'scripts/invoke_specify.py', '--site-packages', site_packages, '--']
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
    import schema_runtime
    runtime = schema_runtime.runtime_path(ROOT)
    require((runtime / '.ready').is_file(), 'Prepare the pinned schema runtime before this fixture')
    started = time.monotonic()
    with FixtureDirectory() as directory:
        fixture = Path(directory)
        project = fixture / 'clean consumer with spaces'
        project.mkdir()
        expanded = fixture / 'packages'
        for name in (*components, 'program-kit'):
            extract(assets / f'{name}-{version}.zip', expanded / name)
        require((expanded / 'program-kit/scripts/install_local_extension.py').is_file(),
                'Install bundle lacks its native release-copy adapter')
        # Exercise the actual compact bundle's reader, not only loose component
        # archives. Read default lifecycle facts and a historical publisher fact.
        bundled = expanded / 'program-kit/extensions/program-kit-building-blocks'
        index = json.loads((bundled / 'references/dependency-profiles/index.json').read_text())
        historical = next(identity for identity, entry in index['profiles'].items()
                          if identity != index['default'] and entry.get('qualificationRecipe'))
        for identity, package in ((index['default'], 'CShells.Abstractions'),
                                  (historical, 'Orbyss.Foundation.Json')):
            result = execute([sys.executable, bundled / 'scripts/publisher_knowledge.py',
                              '--profile', identity, '--package', package], project)
            fact = json.loads(result.stdout.split('\n', 1)[1])
            require(fact['id'] == package and bool(fact['facts']),
                    'Compacted bundle lost selected publisher facts')
        execute([*bridge, 'init', '.', '--force','--non-interactive','--integration','copilot',
                 '--script','py','--ignore-agent-tools'], project)
        # Only transport changes: native core resolves pins, installs each
        # primitive, and owns first-install contribution/ownership records.
        from local_bundle_fixture import install_local_bundle, verify_release_copies
        component_sources = {('extensions',name):expanded/name for name in components[:3]}
        component_sources[('presets',components[3])] = expanded/components[3]
        component_sources[('workflows',components[4])] = expanded/components[4]
        install_local_bundle(project, expanded/'program-kit', bridge,
                             lambda label,argv:execute(argv,project), component_sources=component_sources, integration='copilot')
        records = json.loads((project/'.specify/bundle-records.json').read_text(encoding='utf-8'))
        record = next(item for item in records['bundles'] if item['bundle_id']=='program-kit')
        expected_components = set(component_sources)
        require({(c['kind'],c['id']) for c in record['contributed_components']} == expected_components,
                'Native bundle does not own all promised components')
        require({(c['kind'],c['id']) for c in record['required_components']} == expected_components,
                'Native bundle required-component registrations are incomplete')
        config = yaml.safe_load((project/'.specify/extensions.yml').read_text(encoding='utf-8'))
        require(set(components[:3]) <= set(config['installed']), 'Missing installed extension registration')
        require(config['settings']['auto_execute_hooks'] is True, 'Installed required hooks are disabled')
        for event, declarations in yaml.safe_load((expanded/'program-kit-governance/extension.yml').read_text(encoding='utf-8'))['hooks'].items():
            declarations = declarations if isinstance(declarations,list) else [declarations]
            expected = [d['command'] for d in sorted(declarations,key=lambda d:d.get('priority',10))]
            actual = [h for h in config['hooks'][event] if h.get('extension')=='program-kit-governance']
            require([h['command'] for h in actual] == expected and all(h['enabled'] and not h['optional'] for h in actual),
                    'Missing, reordered or optional required hooks: '+event)
        for relative in ('.specify/presets/program-kit-governance-preset/preset.yml',
                         '.specify/workflows/program-kit-bootstrap/workflow.yml',
                         '.specify/bundle-records.json',
                         '.github/skills/speckit-program-kit-governance-sync/SKILL.md',
                         '.github/skills/speckit-program-kit-building-blocks-sync/SKILL.md'):
            require((project/relative).is_file(),'Missing installed registration/entrypoint: '+relative)
        resolver = project/'.specify/scripts/python/resolve_template.py'
        resolved = execute([sys.executable,resolver,'spec-template','--json'],project)
        require(bool(json.loads(resolved.stdout)['TEMPLATE_CONTENT'].strip()),'Installed phase template resolution is empty')
        # Copy an explicitly prepared runtime; this fixture installs no tools.
        target_runtime = schema_runtime.runtime_path(project)
        target_runtime.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(runtime,target_runtime)
        governance = project/'.specify/extensions/program-kit-governance/scripts/governance_state.py'
        execute([sys.executable,governance,'validate-installation'],project)
        schema = project/'smoke.schema.json'
        schema.write_text(json.dumps({'$schema':'https://json-schema.org/draft/2020-12/schema',
            'type':'object','properties':{'name':{'type':'string'}},'required':['name'],'additionalProperties':False}))
        instance = project/'smoke.json'
        validator = project/'.specify/extensions/program-kit-governance/scripts/json_schema.py'
        for value, expected in (({'name':'installed'},0),({},1)):
            instance.write_text(json.dumps(value))
            result = execute([sys.executable,validator,'validate','--schema',schema,'--input',instance],project,expected)
            require(json.loads(result.stdout)['valid'] is (expected==0),'Installed validator gave inconsistent result')
        verify_release_copies(project, expanded / 'program-kit')
    elapsed = time.monotonic()-started
    print(f'Package installation/entrypoint smoke passed in {elapsed:.3f}s; no agent, build or application acceptance claimed.')
    return 0


if __name__ == '__main__': raise SystemExit(main())
