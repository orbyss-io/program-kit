"""Validate and append independent assessment data to an owner's intake queue."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import repair_contract as c
from repair_feedback import write, checkout, now

DISPOSITIONS = ('adopt', 'duplicate', 'defer', 'reject', 'needs-proof')
CAUSES = ('program-kit-defect', 'guidance-gap', 'consumer-choice', 'domain-adaptation', 'mixed', 'unknown')


def validate(value):
    c.fields(value, ('assessmentVersion', 'assessmentId', 'createdAt', 'requests', 'terminologyMapping',
                     'unknownFields', 'evidenceClass', 'expectationSources', 'cause', 'ownership', 'missingProof',
                     'mechanism', 'supportedScope', 'consumerEffects', 'pointOfUseAction', 'relationships',
                     'proposedDisposition', 'rationale', 'correlation'))
    c.require(value['assessmentVersion'] == '1.0' and re.fullmatch(r'assess-[a-z0-9-]+', value['assessmentId']), 'assessment-version-or-id')
    c.require(value['evidenceClass'] in c.CLASSES and value['cause'] in CAUSES and value['proposedDisposition'] in DISPOSITIONS, 'assessment-enums')
    c.require(isinstance(value['requests'], list) and value['requests'], 'assessment-requests')
    for reference in value['requests']:
        c.fields(reference, ('requestId', 'revision', 'requestSha256', 'contractVersion', 'selectedKnowledgeVersion'))
        c.require(re.fullmatch(c.ID, reference['requestId']) and type(reference['revision']) is int and reference['revision'] >= 1
                  and re.fullmatch(c.HEX, reference['requestSha256']), 'assessment-provenance')
    for key in ('createdAt', 'ownership', 'missingProof', 'mechanism', 'supportedScope', 'consumerEffects', 'pointOfUseAction', 'rationale'):
        c.text(value[key])
    for key in ('terminologyMapping', 'unknownFields', 'expectationSources', 'relationships'):
        c.require(isinstance(value[key], list), 'assessment-list')
    for key in ('unknownFields', 'expectationSources'):
        c.require(all(isinstance(x, str) for x in value[key]), 'assessment-string-list')
    for mapping in value['terminologyMapping']:
        c.fields(mapping, ('original', 'canonical', 'reason'))
        c.text(mapping['original']); c.text(mapping['reason'])
        c.require(mapping['canonical'] is None or isinstance(mapping['canonical'], str), 'assessment-canonical-term')
    for relation in value['relationships']:
        c.fields(relation, ('requestId', 'repairId', 'groupId', 'explanation'))
        c.require(any(r['requestId'] == relation['requestId'] for r in value['requests']), 'relationship-provenance')
        c.require(isinstance(relation['repairId'], str) and re.fullmatch(r'repair-[a-z0-9-]+', relation['repairId'])
                  and (relation['groupId'] is None or isinstance(relation['groupId'], str)), 'repair-or-group-identity')
        c.text(relation['explanation'])
    c.require(isinstance(value['correlation'], dict), 'assessment-correlation')
    c.sensitive(c.encoded(value))
    return value


def submit(root, value):
    root = checkout(root)
    validate(value)
    for reference in value['requests']:
        path = c.inside(root, f"artifacts/repair-feedback/intake/{reference['requestId']}/{reference['revision']}/packet/request.json")
        c.require(path.is_file() and c.sha(path.read_bytes()) == reference['requestSha256'], 'assessment-original-missing-or-changed')
        original = json.loads(path.read_bytes())
        c.require(original['contractVersion'] == reference['contractVersion'] and
                  original['evidence']['knowledgeVersion'] == reference['selectedKnowledgeVersion'], 'assessment-original-version-mismatch')
    path = c.inside(root, 'artifacts/repair-feedback/assessments/' + value['assessmentId'] + '.json')
    write(path, value, immutable=True)
    return {'queuedAssessment': str(path), 'assessmentSha256': c.sha(path.read_bytes()), 'retrievedAt': now(),
            'meaning': 'independent assessment queued; implementation owner disposition required'}


def preserve_original(root, source):
    """Import explicitly selected historical JSON bytes without normalizing answers."""
    root, source = checkout(root), Path(source)
    c.require(source.is_file() and source.stat().st_size <= c.MAX_FILE and not source.is_symlink(), 'historical-original-file')
    raw = source.read_bytes()
    value = json.loads(raw)
    c.require(isinstance(value, dict) and isinstance(value.get('requestId'), str) and re.fullmatch(c.ID, value['requestId'])
              and type(value.get('revision')) is int and value['revision'] > 0 and isinstance(value.get('contractVersion'), str)
              and isinstance(value.get('evidence'), dict) and isinstance(value['evidence'].get('knowledgeVersion'), str), 'historical-provenance-required-do-not-invent')
    directory = c.inside(root, f"artifacts/repair-feedback/intake/{value['requestId']}/{value['revision']}")
    original = c.inside(directory, 'packet/request.json')
    original.parent.mkdir(parents=True, exist_ok=True)
    if original.exists(): c.require(original.read_bytes() == raw, 'historical-original-conflict')
    else:
        with original.open('xb') as stream: stream.write(raw)
    imported = {'requestSha256': c.sha(raw), 'contractVersion': value['contractVersion'],
                'selectedKnowledgeVersion': value['evidence']['knowledgeVersion'],
                'source': str(source.resolve()), 'meaning': 'preserved historical account; not normalized or current-contract qualified'}
    write(directory / 'historical-import.json', imported, immutable=True)
    return imported


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--assessment', type=Path)
    action.add_argument('--preserve-original', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(preserve_original(args.root, args.preserve_original) if args.preserve_original else
                         submit(args.root, json.loads(args.assessment.read_bytes())), indent=2))
    except (ValueError, OSError, KeyError):
        print('PKRF assessment-invalid-or-queue-unavailable; original records preserved', file=sys.stderr)
        raise SystemExit(1)
