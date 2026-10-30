"""Validate shipped native components and founding entrypoints without a workflow."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml
from specify_cli.bundles.manifest import BundleManifest
from specify_cli.extensions import ExtensionManifest
from specify_cli.presets import PresetManifest

EXPECTED_HOOKS = {
    'before_specify', 'after_specify',
    'before_plan', 'after_plan', 'before_tasks', 'after_tasks',
    'before_implement', 'after_implement',
}
RETIRED_COMMANDS = {
    'assessment', 'research', 'tooling', 'roadmap', 'bootstrap-closure',
    'bootstrap-recovery', 'proxy-bootstrap', 'bootstrap',
    'constitution-begin', 'constitution-review', 'constitution-ratify',
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def source_file(root, relative):
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()) and path.is_file(),
            'Component source is missing or outside its owner: ' + str(relative))
    return path


def validate_template_inputs(root):
    """Ignored local build inputs cannot substitute for versioned scaffolding."""
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'],
                            capture_output=True, text=True, encoding='utf-8', check=True)
    tracked = set(result.stdout.split('\0'))
    template = root / 'extensions/program-kit-dotnet/templates/dotnet'
    for manifest in template.rglob('managed-files.json'):
        for entry in json.loads(manifest.read_text(encoding='utf-8'))['files']:
            source = (template / entry.get('sourceRoot', 'files') /
                      entry.get('source', entry['path'])).resolve()
            relative = source.relative_to(root.resolve()).as_posix()
            require(source.is_file() and relative in tracked,
                    'Scaffold input is missing from versioned source: ' + relative)


def main():
    root = Path(__file__).resolve().parents[1]
    validate_template_inputs(root)
    for path in (root / 'extensions').rglob('*.json'):
        json.loads(path.read_text(encoding='utf-8'))
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    catalog = json.loads((root / 'catalogs/extensions.json').read_text(encoding='utf-8'))
    components = {}
    for identity in ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet'):
        owner = root / 'extensions' / identity
        manifest = owner / 'extension.yml'
        ExtensionManifest(manifest)
        data = yaml.safe_load(manifest.read_text(encoding='utf-8'))
        require(data['extension']['id'] == identity and data['extension']['version'] == version,
                'Extension identity/version is incoherent: ' + identity)
        commands = data.get('provides', {}).get('commands', [])
        names = [item['name'] for item in commands]
        require(len(names) == len(set(names)), 'Duplicate registered command: ' + identity)
        require(catalog['extensions'][identity]['provides']['commands'] == len(names),
                'Catalog command count differs from its native manifest: ' + identity)
        for kind in ('commands', 'scripts'):
            for item in data.get('provides', {}).get(kind, []):
                source_file(owner, item['file'])
        for item in data.get('provides', {}).get('config', []):
            source_file(owner, item['template'])
        components[identity] = data

    governance = components['program-kit-governance']
    registered = {item['name'] for item in governance['provides']['commands']}
    required = {'product-intake', 'grilling', 'specification-intake',
                'architecture', 'architecture-check', 'readiness', 'implementation-check',
                'phase-context', 'sync', 'upgrade', 'repair-request', 'view-c4'}
    require({'speckit.program-kit-governance.' + name for name in required} <= registered,
            'An ordinary founding/delivery/maintenance entrypoint is missing')
    require(not registered & {'speckit.program-kit-governance.' + name for name in RETIRED_COMMANDS},
            'A retired workflow producer remains an active command')
    require([item['name'] for item in components['program-kit-building-blocks']['provides']['commands']]
            == ['speckit.program-kit-building-blocks.sync'], 'Building-block synchronization ownership changed')
    require([item['name'] for item in components['program-kit-dotnet']['provides']['commands']]
            == ['speckit.program-kit-dotnet.regenerate-eng'],
            '.NET commands must expose only deterministic regeneration; synchronization retains its existing owner')
    hooks = governance.get('hooks', {})
    require(set(hooks) == EXPECTED_HOOKS, 'Ordinary lifecycle hook coverage changed')
    for event, declarations in hooks.items():
        for declaration in declarations if isinstance(declarations, list) else [declarations]:
            require(declaration.get('optional') is False and declaration.get('enabled', True),
                    'Required hook was weakened: ' + event)
            require(declaration['command'] in registered or declaration['command'] in {'speckit.clarify', 'speckit.analyze'},
                    'Hook names an unavailable command: ' + event)
    preset_root = root / 'presets/program-kit-governance-preset'
    PresetManifest(preset_root / 'preset.yml')
    preset = yaml.safe_load((preset_root / 'preset.yml').read_text(encoding='utf-8'))
    require(preset['preset']['version'] == version, 'Preset version differs from extensions')
    entries = preset['provides']['templates']
    templates = {item['name']: item for item in entries if item['type'] == 'template'}
    require(set(templates) == {'constitution-template', 'spec-template', 'plan-template', 'tasks-template'},
            'Governance preset lost an ordinary lifecycle template')
    for name, item in templates.items():
        require(item.get('strategy') == 'append',
                'Template composition strategy changed: ' + name)
    commands = {item['name']: item for item in entries if item['type'] == 'command'}
    require(set(commands) == {'speckit.tasks', 'speckit.implement', 'speckit.analyze'},
            'Native governance command contribution changed')
    for name, item in commands.items():
        require(item.get('strategy') == 'append',
                'Native command composition strategy changed: ' + name)
        require(not item.get('replaces'), 'Knowledge contribution must preserve the native command: ' + name)
    for entry in entries:
        source_file(preset_root, entry['file'])

    BundleManifest.from_file(root / 'bundle.yml')
    bundle = yaml.safe_load((root / 'bundle.yml').read_text(encoding='utf-8'))
    require(bundle['bundle']['version'] == version, 'Bundle version differs from components')
    require({item['id'] for item in bundle['provides']['extensions']} == set(components),
            'Native composition no longer owns exactly the three maintained extensions')
    require(all(item['version'] == version for item in bundle['provides']['extensions']),
            'Bundle extension pins differ from their source')
    require(bundle['provides']['presets'] == [{'id': 'program-kit-governance-preset', 'version': version,
                                              'priority': 10, 'strategy': 'append'}],
            'Bundle preset contribution changed')
    require(not bundle['provides'].get('workflows'), 'Active bundle still delivers a founding workflow')
    require(not (root / 'workflows/program-kit-bootstrap/workflow.yml').exists(),
            'Retired active workflow source remains present')
    workflows = json.loads((root / 'catalogs/workflows.json').read_text(encoding='utf-8'))
    require(not workflows.get('workflows'), 'Retired workflow is still advertised for installation')

    owner = root / 'extensions/program-kit-governance'
    for relative in ('scripts/product_intake.py', 'scripts/specification_intake.py',
                     'scripts/architecture_map.py', 'scripts/c4_view.py', 'scripts/governance_state.py',
                     'references/product-founding.md', 'references/intake-artifacts.md',
                     'references/intake-method.md', 'references/functional-discovery.md'):
        source_file(owner, relative)
    for filename in ('architecture-map.schema.json', 'architecture-map-v2.schema.json'):
        schema = json.loads(source_file(owner, 'references/' + filename).read_text(encoding='utf-8'))
        require(schema.get('$schema') == 'https://json-schema.org/draft/2020-12/schema',
                'Founding schema dialect changed: ' + filename)
    minimal = json.loads((owner / 'references/architecture-map-minimal.json').read_text(encoding='utf-8'))
    require(minimal.get('schema_version') == '2.0' and minimal.get('elements'),
            'Small language-neutral architecture example is missing')
    viewer = json.loads((owner / 'references/c4-viewer-tool.json').read_text(encoding='utf-8'))['selected']
    require(viewer.get('docker_image') == 'structurizr/structurizr:' + viewer.get('version', '')
            and re.fullmatch(r'sha256:[0-9a-f]{64}', viewer.get('docker_digest', '')),
            'C4 viewer lacks its immutable version/image selection')
    require(viewer.get('default_port') == 8081, 'C4 viewing port conflicts with local identity')
    require(not (root / 'extensions/program-kit-dotnet/references/orbyss-building-blocks.json').exists(),
            'A second dependency catalog authority remains in .NET')
    print('Native components, lifecycle contributions and skill-led founding distribution validate.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
