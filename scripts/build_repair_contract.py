"""Generate published repair vocabulary/questions/schema from executable v1 constants."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import repair_contract as c
import repair_evaluator as evaluator

QUESTIONS = {
    'context': 'Which consumer, Program Kit/profile/knowledge versions, phase, task and triggering command? What source and dirty-state limits were observed?',
    'expectation': 'What was expected and which exact requirement, guidance, task or tool contract supports it? Explicitly identify unsupported expectations.',
    'observation': 'What happened, under which triggers, with which observable consequences and available reproduction or counterexample?',
    'resources': 'Which knowledge, tools and skills were available, and which were actually consulted according to retained evidence? Availability is not use.',
    'decision': 'What recorded decision explanation, constraints and considered alternatives explain the reported local choice? Mark later explanations retrospective; absent explanations unknown.',
    'remedy': 'What local change or workaround was made, what did it preserve or bypass, and what was its scope?',
    'results': 'What results, failures, uncertainty and remaining blockade are evidenced? Distinguish reported tests, inspected tests and independently executed proof.',
    'lesson': 'What upstream lesson is proposed, if any? Do not present a hypothesis, local remedy or domain adaptation as an established defect or accepted architecture.'}


def obj(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


def array(items):
    return {'type': 'array', 'items': items}


def build():
    string = {'type': 'string', 'minLength': 1, 'maxLength': 16000}
    strings = array({'type': 'string'})
    identity = {'type': 'string', 'pattern': '^' + c.ID + '$'}
    hash_schema = {'type': 'string', 'pattern': '^' + c.HEX + '$'}
    section = obj({'answer': string, 'evidenceClass': {'enum': list(c.CLASSES)},
                   'explanationKind': {'enum': list(c.EXPLANATIONS)}, 'references': strings})
    member = obj({'path': {'type': 'string', 'minLength': 1, 'maxLength': 200, 'pattern': '^[a-zA-Z0-9.][a-zA-Z0-9_./-]*$'},
                  'purpose': string, 'provenance': string, 'bytes': {'type': 'integer', 'minimum': 0, 'maximum': c.MAX_FILE},
                  'sha256': hash_schema, 'transformations': strings, 'qualification': string})
    schema = obj({'contractVersion': {'const': c.VERSION}, 'requestId': identity,
                  'revision': {'type': 'integer', 'minimum': 1}, 'supersedes': {'oneOf': [{'type': 'null'}, hash_schema]},
                  'projectId': {'type': 'string', 'pattern': '^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$'}, 'createdAt': string, 'component': {'enum': list(c.COMPONENTS)},
                  'title': {'type': 'string', 'minLength': 1, 'maxLength': 160}, 'originalAccount': string,
                  'diagnostics': obj({key: section for key in c.SECTIONS}), 'unclassified': strings,
                  'evidence': obj({key: string for key in ('programKitVersion', 'profileVersion', 'knowledgeVersion', 'sourceCommit', 'dirtyState')} |
                                  {'members': array(member)}), 'omissions': strings})
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    schema['$id'] = 'https://program-kit.orbyss.io/contracts/repair-request/1.0'
    schema['allOf'] = [{'if': {'properties': {'revision': {'const': 1}}},
                        'then': {'properties': {'supersedes': {'type': 'null'}}},
                        'else': {'properties': {'supersedes': hash_schema}}}]
    assessment = obj({'assessmentVersion': {'const': '1.0'}, 'assessmentId': {'type': 'string', 'pattern': '^assess-[a-z0-9-]+$'},
        'createdAt': string, 'requests': array(obj({'requestId': identity, 'revision': {'type': 'integer', 'minimum': 1},
            'requestSha256': hash_schema, 'contractVersion': string, 'selectedKnowledgeVersion': string})),
        'terminologyMapping': array(obj({'original': string, 'canonical': {'type': ['string', 'null']}, 'reason': string})),
        'unknownFields': strings, 'evidenceClass': {'enum': list(c.CLASSES)}, 'expectationSources': strings,
        'cause': {'enum': list(evaluator.CAUSES)}, 'ownership': string, 'missingProof': string, 'mechanism': string,
        'supportedScope': string, 'consumerEffects': string, 'pointOfUseAction': string,
        'relationships': array(obj({'requestId': identity, 'repairId': {'type': 'string', 'pattern': '^repair-[a-z0-9-]+$'},
                                    'groupId': {'type': ['string', 'null']}, 'explanation': string})),
        'proposedDisposition': {'enum': list(evaluator.DISPOSITIONS)}, 'rationale': string, 'correlation': {'type': 'object'}})
    assessment['properties']['requests']['minItems'] = 1
    assessment['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    historical_assessment = deepcopy(assessment)
    assessment['properties']['assessmentVersion'] = {'const': '1.1'}
    assessment['properties']['relationships']['items']['properties']['repairId']['pattern'] = '^' + evaluator.intake.REPAIR + '$'
    assessment['properties']['ownerRoute'] = obj({'routeVersion': {'const': 1},
        'ownerId': {'type': 'string', 'pattern': '^' + evaluator.intake.OWNER + '$'},
        'ledger': {'type': 'string', 'minLength': 1}, 'adapter': {'const': 'items-v1'}, 'routeSha256': hash_schema})
    assessment['required'].append('ownerRoute')
    contract = {'contractVersion': c.VERSION, 'schema': 'request.schema.json', 'assessmentSchema': '#/assessmentSchemas/1.1', 'questions': QUESTIONS,
        'vocabulary': {'request': 'Stable consumer observation identity; distinct from repair/finding identity.',
            'revision': 'Immutable evidence account superseding an exact earlier request hash.',
            'repair': 'Owner-selected shared change; several consumer requests may support one repair.',
            'assessment': 'Independent versioned evaluation; never a rewrite of the consumer account.',
            'unclassified': 'Original wording retained without forcing unknown concepts into canonical categories.',
            'reported': 'A source says an action/result happened; evaluator has not inspected its proof.',
            'inspected': 'Retained evidence was directly inspected; this is not independent execution.',
            'independently-reproduced': 'The attributed result was independently executed under stated conditions.',
            'recorded': 'Decision explanation retained from the original work.',
            'retrospective': 'Later explanation; not an original reasoning trace.',
            'unknown': 'Evidence does not establish this fact; do not fabricate it.'},
        'enums': {'component': list(c.COMPONENTS), 'evidenceClass': list(c.CLASSES), 'explanationKind': list(c.EXPLANATIONS),
                  'lifecycleFacts': list(c.LIFECYCLE), 'assessmentCause': list(evaluator.CAUSES),
                  'proposedDisposition': list(evaluator.DISPOSITIONS)},
        'budgets': {'files': c.MAX_FILES, 'perFileBytes': c.MAX_FILE, 'totalBytes': c.MAX_TOTAL,
                    'allowedExtensions': sorted(c.TYPES), 'qualifiedBinaryExtensions': sorted(c.BINARY)},
        'compatibility': 'Unknown contract versions are preserved and explicitly mapped in separate assessments; never silently upgraded.',
        'guardian': {'version': c.GUARDIAN, 'meaning': 'Contract validity only; maintainer acceptance required. No submitted code execution.',
                     'sensitiveChecks': ['GitHub token patterns', 'AWS access key IDs', 'private key headers', 'Bearer headers', 'credential assignments'],
                     'limitations': 'No assertion of truth, authenticated publisher, arbitrary personal/business safety or consumer acceptance.'}}
    contract['assessmentVersion'] = '1.1'
    # Consumers and evaluators share the same schemas without spending two
    # additional entries in Spec Kit's bounded composite bundle. Repository
    # copies remain available for standalone tools and historical byte identity.
    contract['historicalAssessmentSchema'] = '#/assessmentSchemas/1.0'
    contract['assessmentSchemas'] = {'1.0': historical_assessment, '1.1': assessment}
    return {'contract.json': contract, 'request.schema.json': schema, 'assessment.schema.json': assessment,
            'assessment-1.0.schema.json': historical_assessment}


def published_path(name):
    directory = ROOT / ('docs/contracts/repair-feedback' if name.startswith('assessment') else
                        'extensions/program-kit-governance/references/repair-feedback')
    return directory / name


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for name, value in build().items():
        path = published_path(name)
        if args.check:
            if not path.is_file() or path.read_bytes() != c.encoded(value):
                raise SystemExit('PKRF published-contract-stale: run scripts/build_repair_contract.py')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(c.encoded(value))
