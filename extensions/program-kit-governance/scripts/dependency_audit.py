"""Recognize existing, verified dependency evidence without hiding consumer targets."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'dependency evidence escapes repository: {relative}')
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_inputs(root):
    """Classify immutable executed scratch inputs; this grants no current readiness."""
    result = set()
    ledger = read(root / 'docs/architecture/bootstrap-prerequisites.json', {})
    proofs = [e for item in ledger.get('prerequisites', []) if item.get('status') == 'closed'
              for e in item.get('evidence', []) if e.get('kind') == 'compatibility']
    if proofs:
        from bootstrap_lifecycle import proof_tooling
        from phase_obligations import test_results
        current = set(proof_tooling())
        legacy = current - {
            'program-kit-governance/scripts/managed_provider_probes.py',
            'program-kit-governance/scripts/bootstrap_provider_context.py',
            'program-kit-governance/scripts/compatibility_scope.py',
            'program-kit-building-blocks/scripts/building_blocks.py',
            'program-kit-dotnet/scripts/dependency_profile.py',
            'program-kit-dotnet/templates/dotnet/files/eng/toolchain.py',
            'program-kit-dotnet/templates/dotnet/files/eng/js_toolchain.py',
        }
        for item in ledger['prerequisites']:
            if item.get('status') != 'closed': continue
            for evidence in item.get('evidence', []):
                if evidence.get('kind') != 'compatibility': continue
                receipt = inside(root, evidence['path'])
                if sha(receipt) != evidence['sha256']:
                    raise ValueError('Retained compatibility receipt is missing or changed')
                proof = read(receipt)
                schema = proof.get('schema_version')
                tooling = proof.get('tooling_sources', {})
                allowed = (legacy, current) if schema == '1.1' else (set(proof_tooling(True)),)
                if (schema not in {'1.1', '1.2'} or proof.get('prerequisite') != item['id'] or proof.get('exit_code') != 0
                        or not proof.get('command') or not proof.get('inputs') or len(proof.get('streams', [])) != 2
                        or set(tooling) not in allowed or any(not re.fullmatch('[a-f0-9]{64}', str(value)) for value in tooling.values())):
                    raise ValueError('Retained compatibility input needs immutable executed proof provenance')
                design = proof.get('design_sources', {})
                if ('docs/architecture/bootstrap-decisions.json' not in design
                        or set(design) - {'docs/architecture/bootstrap-decisions.json', 'docs/architecture/building-block-selection.json'}
                        or any(not re.fullmatch('[a-f0-9]{64}', str(value)) for value in design.values())):
                    raise ValueError('Retained compatibility proof lacks its historical selected-design provenance')
                test = proof.get('test_result')
                if not test or not proof.get('checks'):
                    raise ValueError('Retained compatibility proof lacks executed named checks')
                for entry in proof['inputs'] + proof['streams'] + [test]:
                    if sha(inside(root, entry['path'])) != entry['sha256']:
                        raise ValueError('Retained compatibility inputs/streams changed')
                cases = test_results(inside(root, test['path']), 'junit')
                if not all(cases.values()) or not all(cases.get(name) is True for name in proof['checks']):
                    raise ValueError('Retained compatibility proof lacks passing required checks')
                result.update(inside(root, entry['path']) for entry in proof['inputs'])
        # Tooling/design drift still invalidates current closure in
        # bootstrap_lifecycle.validate_prerequisites. It cannot turn an unchanged
        # historical scratch project into an application dependency. The caller
        # rejects any active project, import or solution reference to these inputs.
    graph = read(root / 'artifacts/program-kit/npm-graph.json', {})
    if graph:
        from sync_readiness import graph_errors
        errors = graph_errors(root, {})
        if errors:
            raise ValueError('; '.join(errors))
        candidate = inside(root, graph['packageJson'])
        # A strict graph can also be run on a real application. Only an isolated
        # planning input under a feature qualifies, never an arbitrary app manifest.
        if candidate.is_relative_to((root / 'specs').resolve()):
            result.add(candidate)
    return result


def reject_active_references(root, evidence, lock):
    if not evidence:
        return
    selected = read(root / 'docs/architecture/building-block-selection.json', {})
    for target in selected.get('targets', []) + lock.get('targets', []):
        if inside(root, target['path']) in evidence:
            raise ValueError(f'active dependency target is also retained evidence: {target["path"]}')
    for ownership in (root / 'specs').glob('*/artifact-ownership.json'):
        for project in read(ownership).get('runtimeComposition', {}).get('projects', []):
            if inside(root, project['path']) in evidence:
                raise ValueError(f'active runtime project is also retained evidence: {project["path"]}')
    ignored = {'.git', '.specify', 'artifacts', 'node_modules', 'bin', 'obj'}
    for path in root.rglob('*'):
        if not path.is_file() or set(path.relative_to(root).parts) & ignored or path.resolve() in evidence:
            continue
        if path.suffix in {'.csproj', '.props', '.targets'}:
            for node in ET.parse(path).iter():
                attribute = {'ProjectReference': 'Include', 'Import': 'Project'}.get(node.tag.rsplit('}', 1)[-1])
                value = node.get(attribute, '') if attribute else ''
                for reference in value.split(';'):
                    if reference and (path.parent / reference.replace('\\', '/')).resolve() in evidence:
                        raise ValueError(f'active MSBuild reference to retained evidence: {path}: {reference}')
        elif path.suffix == '.sln':
            for reference in re.findall(r'^Project\([^\n]+?=\s*"[^"]*",\s*"([^"]+)"', path.read_text(encoding='utf-8-sig'), re.MULTILINE):
                if (path.parent / reference.replace('\\', '/')).resolve() in evidence:
                    raise ValueError(f'active solution includes retained evidence: {path}: {reference}')
        elif path.suffix == '.slnx':
            for node in ET.parse(path).iter('Project'):
                if (path.parent / node.get('Path', '').replace('\\', '/')).resolve() in evidence:
                    raise ValueError(f'active solution includes retained evidence: {path}')
        elif path.name == 'package.json':
            manifest = read(path)
            for section in ('dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies'):
                for value in manifest.get(section, {}).values():
                    if isinstance(value, str) and value.startswith(('file:', 'link:')):
                        target = (path.parent / value.split(':', 1)[1]).resolve()
                        if target in evidence or target / 'package.json' in evidence:
                            raise ValueError(f'active npm reference to retained evidence: {path}: {value}')
            workspaces = manifest.get('workspaces', [])
            if isinstance(workspaces, dict):
                workspaces = workspaces.get('packages', [])
            for pattern in workspaces:
                if any((directory / 'package.json').resolve() in evidence for directory in path.parent.glob(pattern)):
                    raise ValueError(f'active npm workspace includes retained evidence: {path}: {pattern}')


def engineering_outputs(root):
    """Require both the installed template and reconciler's exact ownership receipt."""
    state = read(root / '.program-kit/managed.json', {})
    installed = root / '.specify/extensions/program-kit-dotnet'
    # Upgrade admission checks the currently installed ownership before replacing
    # components. A candidate's changed template cannot validate the old bytes.
    template = (installed / 'templates/dotnet/files' if installed.is_dir()
                else Path(__file__).resolve().parents[2] / 'program-kit-dotnet/templates/dotnet/files')
    result = set()
    for relative in ('eng/ProgramKit.Packages.props', 'eng/.config/dotnet-tools.json'):
        path = root / relative
        if not path.is_file():
            continue
        entry = state.get('files', {}).get(relative, {})
        source = template / relative
        if not source.is_file() or entry.get('ownership') != 'managed' or entry.get('sourceIdentity') != 'files/' + relative:
            raise ValueError(f'engineering dependency output has no installed ownership: {relative}')
        expected = source.read_bytes()
        from repository_sync import provider
        profiles = provider('program-kit-dotnet/scripts/dependency_profile.py')
        expected = profiles.render(root, relative, expected)
        if path.name == 'dotnet-tools.json':
            from repository_sync import provider
            persistence = provider('program-kit-dotnet/scripts/persistence_selection.py')
            selection = persistence.resolve(root)
            pins = persistence.pins(persistence.effective(selection), template)
            if 'Microsoft.EntityFrameworkCore.Design' in pins:
                value = json.loads(expected)
                value['tools']['dotnet-ef'] = {'version': pins['Microsoft.EntityFrameworkCore.Design'], 'commands': ['dotnet-ef']}
                expected = (json.dumps(value, indent=2) + '\n').encode('utf-8')
        digest = hashlib.sha256(expected).hexdigest()
        if sha(path) != digest or entry.get('lastWrittenHash') != digest or entry.get('templateHash') != digest:
            raise ValueError(f'engineering dependency output or ownership hash changed: {relative}')
        result.add(path.resolve())
    return result


def audit_exemptions(root, lock):
    evidence = evidence_inputs(root)
    reject_active_references(root, evidence, lock)
    return evidence | engineering_outputs(root)


def planned_selection_errors(root, projects):
    """Detect missing catalog target bindings while the graph is still a plan."""
    selection = root / 'docs/architecture/building-block-selection.json'
    if not selection.is_file():
        return []
    from repository_sync import provider
    blocks = provider('program-kit-building-blocks/scripts/building_blocks.py')
    catalog_path = blocks.default_catalog(Path(blocks.__file__))
    catalog = blocks.load_json(catalog_path)
    lock = blocks.resolve(root, selection, catalog_path, blocks.find_program_kit_version(Path(blocks.__file__)))
    catalog_ids = {item['packageId'].casefold() for item in catalog['packages'].values() if item['ecosystem'] == 'nuget'}
    by_path = {target['path']: {item['packageId'].casefold() for item in target['packages']
                              if item['materializationKind'] == 'nuget-project'} for target in lock['targets']}
    errors = []
    for project in projects:
        planned = {name.casefold() for name in project['packageReferences']} & catalog_ids
        missing = planned - by_path.get(project['path'], set())
        if missing:
            errors.append(f'PKA016 planned direct catalog references lack selection target bindings: {project["path"]}: '
                          + ', '.join(sorted(missing)) + '. Inherited engineering analyzers are not direct project references; '
                          'bind functional/test dependencies through reviewed selection authority before skeleton creation.')
    return errors
