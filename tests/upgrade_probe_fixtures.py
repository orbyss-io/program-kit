"""Render the two real bootstrap probe types in disposable upgrade consumers."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _render_registered_probes(root):
    governance = root / '.specify/extensions/program-kit-governance'
    source = ROOT / 'extensions/program-kit-governance'
    for relative in ('scripts/managed_compatibility.py', 'scripts/managed_provider_probes.py',
                     'scripts/compatibility_process.py', 'examples/bootstrap-postgresql/Program.cs',
                     'examples/bootstrap-postgresql/postgresql_probe.py'):
        destination = governance / relative
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, destination)
    sys.path.insert(0, str(source / 'scripts'))
    try:
        managed = load(governance / 'scripts/managed_compatibility.py', 'upgrade_fixture_managed')
        providers = load(governance / 'scripts/managed_provider_probes.py', 'upgrade_fixture_provider')
        template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
        pins = {node.attrib['Include']: node.attrib['Version'] for node in
                ET.parse(template / '.program-kit/eng/profiles/persistence/ProgramKit.Persistence.EfPostgreSql.props').iter('PackageVersion')}
        dotnet = managed.render(root, 'dotnet-runtime', 'managed-dotnet-runtime')
        provider = providers.render_postgresql(root, 'relational-mechanism', {
            'persistence_runtimes': [{'profile': 'ef-postgresql', 'packages': pins}]})
    finally:
        sys.path.pop(0)
    plan = root / 'docs/architecture/bootstrap-proof-plan.json'
    value = json.loads(plan.read_text()) if plan.exists() else {'schemaVersion': 1, 'probes': []}
    value['probes'].extend([dotnet, provider])
    plan.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return [root / item['recipe'] for item in (dotnet, provider)]


def render_registered_probes(root):
    # Generate in an independent fixture root: adding runtime inputs must not
    # change the disposable consumer's existing bootstrap/authority declarations.
    with tempfile.TemporaryDirectory(prefix='upgrade-probe-generator-') as value:
        stage = Path(value)
        decisions = stage / 'docs/architecture/bootstrap-decisions.json'
        decisions.parent.mkdir(parents=True)
        template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
        sdk = json.loads((template / 'global.json').read_text())['sdk']['version']
        decisions.write_text(json.dumps({'toolchain': {'pins': {'dotnet-sdk': sdk}}}))
        _render_registered_probes(stage)
        plan_relative = Path('docs/architecture/bootstrap-proof-plan.json')
        generated_plan = json.loads((stage / plan_relative).read_text())
        caller_plan = root / plan_relative
        plan = json.loads(caller_plan.read_text()) if caller_plan.exists() else {'schemaVersion': 1, 'probes': []}
        plan['probes'].extend(generated_plan['probes'])
        for path in stage.rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            relative = path.relative_to(stage)
            if relative in (decisions.relative_to(stage), plan_relative):
                continue
            destination = root / relative
            if destination.exists():
                if relative.parts[0] == '.specify':
                    continue
                raise ValueError('Preserve existing reviewed probe: ' + str(relative))
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
        caller_plan.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
        return [root / item['recipe'] for item in generated_plan['probes']]
