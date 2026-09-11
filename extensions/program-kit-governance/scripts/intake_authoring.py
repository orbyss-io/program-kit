"""Build validated draft intake artifacts from one semantic source; never confirm or bootstrap."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile

import architecture_map as architecture
import bootstrap_intake as intake_contract
from contract_shapes import describe, errors, schema_for


def encode(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def file_record(path: Path, relative: Path) -> dict:
    return {'path': relative.as_posix(), 'sha256': intake_contract.sha256_file(path), 'bytes': path.stat().st_size}


def defaults(model: dict) -> None:
    model.setdefault('schema_version', '1.1')
    for key in ('decisions', 'documentation', 'constraints', 'extensions'):
        model.setdefault(key, [])
    model.setdefault('configuration', {'styles': [], 'themes': [], 'terminology': {}, 'branding': {}, 'properties': {}})
    for key in ('elements', 'relationships', 'views'):
        for item in model.get(key, []) if isinstance(model.get(key, []), list) else []:
            if not isinstance(item, dict):
                continue
            for field, value in {'decision_refs': [], 'properties': {}}.items():
                item.setdefault(field, copy.deepcopy(value))
            if key == 'views':
                for field, value in {'description': '', 'filters': [], 'order': [], 'layout': {}, 'animations': []}.items():
                    item.setdefault(field, copy.deepcopy(value))
            else:
                for field, value in {'technology': '', 'tags': [], 'perspectives': [], 'url': ''}.items():
                    item.setdefault(field, copy.deepcopy(value))
                if key == 'elements':
                    item.setdefault('group', '')
                    item.setdefault('archetype', '')
    strategic = model.get('strategic_model')
    if not isinstance(strategic, dict):
        return
    strategic.setdefault('version', '1.0')
    strategic.setdefault('decision_refs', [])
    for key, items in strategic.items():
        if isinstance(items, list) and key not in {'founding_decisions', 'decision_refs'}:
            for item in items:
                if isinstance(item, dict):
                    item.setdefault('decision_refs', [])


def derive_structure(model: dict) -> None:
    strategic = model['strategic_model']
    elements = {item['id']: item for item in model['elements']}
    for module in strategic['modules']:
        element = elements[module['element']]
        if element.get('parent', module['context']) != module['context']:
            raise ValueError(f'Module {module["element"]} has conflicting parent/context; resolve ownership explicitly.')
        element['parent'] = module['context']
    views = {item['key']: item for item in model['views']}
    for journey in strategic['journeys']:
        view = views[journey['view']]
        if view['type'] != 'dynamic':
            raise ValueError(f'Journey {journey["id"]} must identify a dynamic view.')
        ordered = [step['relationship'] for step in journey['steps']]
        view['relationships'] = list(ordered)
        view['order'] = list(ordered)


def project_intake(model: dict, source: dict) -> dict:
    result = copy.deepcopy(source)
    result.setdefault('schema_version', '1.1')
    if result.get('status', 'draft') != 'draft':
        raise ValueError('Authoring source must be draft; this command cannot confirm intake.')
    result['status'] = 'draft'
    strategic = model['strategic_model']
    analysis = result.setdefault('domain_analysis', {'boundary_challenges': []})
    if set(analysis) != {'boundary_challenges'}:
        raise ValueError('Author only domain_analysis.boundary_challenges in intake; shared analysis belongs in map.strategic_model.')
    analysis.update(architecture.project_domain_analysis(model))
    bindings = {item['assessment']: item for item in strategic['capability_bindings']}
    assessments = result.get('capability_assessments', [])
    for item in assessments:
        if set(item) != {'id', 'need'}:
            raise ValueError('Author capability assessments as id/need only; shared binding fields belong in the map.')
    needs = {item['id']: item['need'] for item in assessments}
    if len(needs) != len(assessments) or set(needs) != set(bindings):
        raise ValueError('Capability id/need records must match map bindings exactly, without duplicates.')
    result['capability_assessments'] = [
        {'id': identifier, 'need': needs[identifier], **{key: copy.deepcopy(value) for key, value in binding.items()
          if key not in {'assessment', 'module', 'status', 'decision_refs'}}} for identifier, binding in bindings.items()]
    if 'journeys' not in result:
        result['journeys'] = [{'id': item['source_journey'], 'statement': item['actor_or_trigger'] + ' Outcome: ' + item['outcome'],
                              'evidence': item['evidence']} for item in strategic['journeys']]
    if 'candidate_slice_signals' not in result:
        result['candidate_slice_signals'] = [{'id': item['id'], 'statement': item['actor_or_trigger'] + ' Outcome: ' + item['outcome'],
                                             'evidence': item['evidence']} for item in strategic['candidate_slices']]
    return result


def semantic_review(model: dict) -> list[dict]:
    """Review evidence, not a prose-based mutation classifier or an acceptance verdict."""
    strategic = model['strategic_model']
    return [{'relationship': relation['relationship'], 'contract': relation['contract'],
             'atomicity': relation['atomicity'],
             'check': 'Do all described operations fit this contract and atomicity? Separate lookup from management writes; preserve translation, consistency and failure ownership.',
             'journey_steps': [{'journey': journey['id'], 'description': step['description']}
                               for journey in strategic['journeys'] for step in journey['steps']
                               if step['relationship'] == relation['relationship'] or step['contract'] == relation['contract']]}
            for relation in strategic['context_relationships']]


def build(root: Path, source_path: Path) -> dict:
    root = root.resolve()
    source_path = intake_contract._resolve(root, source_path, 'authoring source')
    source = intake_contract.load_object(source_path)
    source_bytes = source_path.read_bytes()
    if set(source) != {'map', 'intake'}:
        raise ValueError('Authoring source must contain exactly map and intake.')
    if not isinstance(source['map'], dict) or not isinstance(source['intake'], dict):
        raise ValueError('Authoring map and intake must both be objects.')
    targets = [intake_contract._resolve(root, path, 'output') for path in (
        intake_contract.CANONICAL_ARTIFACTS['architecture_map'], intake_contract.CANONICAL_ARTIFACTS['c4_projection'],
        intake_contract.CANONICAL_INTAKE)]
    for target, relative in zip(targets, (intake_contract.CANONICAL_ARTIFACTS['architecture_map'],
                                        intake_contract.CANONICAL_ARTIFACTS['c4_projection'], intake_contract.CANONICAL_INTAKE)):
        if target != root / relative:
            raise ValueError('Refusing a redirected canonical output path.')
    if source_path in targets:
        raise ValueError('Authoring source must not be a generated output.')
    if targets[-1].exists() and intake_contract.load_object(targets[-1]).get('status') != 'draft':
        raise ValueError('Refusing to replace a confirmed intake; stage re-analysis separately.')
    before = {path: path.read_bytes() if path.exists() else None for path in targets}
    model = copy.deepcopy(source['map'])
    defaults(model)
    intent_relative = intake_contract.CANONICAL_ARTIFACTS['project_intent']
    intent = intake_contract._resolve(root, intent_relative, 'project intent')
    if not intent.is_file():
        raise ValueError('Write docs/architecture/project-intent.md before building the draft.')
    if 'sources' not in model:
        model['sources'] = [{'id': 'project-intent', 'path': intent_relative.as_posix(),
                             'sha256': intake_contract.sha256_file(intent), 'format': 'markdown',
                             'importer': {'id': 'program-kit-intake', 'version': '1.1'}}]
    for collection in ('sources', 'documentation'):
        records = model[collection]
        for record in records if isinstance(records, list) else []:
            if isinstance(record, dict) and record.get('path') == intent_relative.as_posix():
                record['sha256'] = intake_contract.sha256_file(intent)
    structural = errors(model, schema_for('map'), path='$.map')
    if structural:
        raise ValueError('\n'.join(structural))
    derive_structure(model)
    architecture.validate_model(model, root)
    document = project_intake(model, source['intake'])
    # Stage and validate all three outputs before replacing anything. Confirmed consumers are
    # never reset to draft; failures preserve their current documents and source.
    with tempfile.TemporaryDirectory(prefix='.intake-authoring-', dir=root) as temporary:
        staged = Path(temporary)
        for record in model['sources'] + model['documentation']:
            relative = Path(record['path'])
            original = intake_contract._resolve(root, relative, 'source evidence')
            destination = intake_contract._resolve(staged, relative, 'staged evidence')
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, destination)
        intent_copy = staged / intent_relative
        intent_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(intent, intent_copy)
        (staged / intake_contract.CANONICAL_ARTIFACTS['architecture_map']).write_text(encode(model), encoding='utf-8', newline='\n')
        (staged / intake_contract.CANONICAL_ARTIFACTS['c4_projection']).write_text(architecture.StructurizrDslExporter().export(model), encoding='utf-8', newline='\n')
        document['artifacts'] = {key: file_record(staged / relative, relative) for key, relative in intake_contract.CANONICAL_ARTIFACTS.items()}
        structural = errors(document, schema_for('intake'), path='$.intake')
        if structural:
            raise ValueError('\n'.join(structural))
        (staged / intake_contract.CANONICAL_INTAKE).write_text(encode(document), encoding='utf-8', newline='\n')
        intake_contract.validate_intake(staged, allowed_statuses={'draft'})
        for path, content in before.items():
            if (path.read_bytes() if path.exists() else None) != content:
                raise ValueError('Consumer artifacts changed during authoring; refusing replacement.')
        if intent.read_bytes() != intent_copy.read_bytes():
            raise ValueError('Project intent changed during authoring; rebuild from the new evidence.')
        if source_path.read_bytes() != source_bytes:
            raise ValueError('Authoring source changed during build; rebuild the new source.')
        replaced = []
        try:
            for target in targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                (staged / target.relative_to(root)).replace(target)
                replaced.append(target)
        except OSError:
            for target in replaced:
                if before[target] is None:
                    target.unlink()
                else:
                    target.write_bytes(before[target])
            raise
    return {'status': 'valid-draft', 'outputs': [str(path) for path in targets],
            'semanticReview': semantic_review(model),
            'review': ['Check every editing/import journey has a write-capable contract, not merely a read-only lookup.',
                       'Check accepted conditional recommendations have evidence for their conditions.',
                       'Schema validity does not confirm intake or establish interview quality.']}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    describe_parser = commands.add_parser('describe')
    describe_parser.add_argument('--document', choices=('map', 'intake'), required=True)
    describe_parser.add_argument('--section', default='root')
    check_parser = commands.add_parser('check')
    check_parser.add_argument('--document', choices=('map', 'intake'), required=True)
    check_parser.add_argument('--input', type=Path, required=True)
    build_parser = commands.add_parser('build-draft')
    build_parser.add_argument('--source', type=Path, required=True)
    build_parser.add_argument('--project-root', type=Path, default=Path('.'))
    args = parser.parse_args()
    try:
        if args.command == 'describe':
            result = describe(args.document, args.section)
        elif args.command == 'check':
            result = {'structuralErrors': errors(intake_contract.load_object(args.input), schema_for(args.document))}
        else:
            result = build(args.project_root, args.source)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get('structuralErrors') else 0
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, intake_contract.IntakeError, architecture.ArchitectureMapError) as error:
        print(f'Intake authoring failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
