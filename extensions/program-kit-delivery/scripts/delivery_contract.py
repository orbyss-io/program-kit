"""Version 1 delivery contracts; no provider I/O or activation writer."""
from pathlib import Path
import hashlib
import json
import sys

CORE = Path(__file__).resolve().parents[2] / 'program-kit-governance/scripts'
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))
import delivery_authority as authority
import json_schema

SCHEMA = Path(__file__).resolve().parents[1] / 'references/delivery.schema.json'


def require(condition, message):
    if not condition:
        raise ValueError('PKD_CONTRACT_INVALID ' + message)


def validate(value, kind):
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    schema['$ref'] = '#/$defs/' + kind
    result = json_schema.validate_value(value, schema, SCHEMA)
    require(result['valid'], f'{kind} does not satisfy the versioned contract: {result.get("errors", [])[:3]}')


def validate_profile(profile):
    validate(profile, 'profile')
    require(profile['edition'] == {'azure': 'azure-devops-services', 'github': 'github.com'}[profile['provider']], 'provider/edition mismatch')
    for key in ('outcome', 'acceptance', 'priority', 'assignment', 'dependencies', 'milestone', 'deliveryState'):
        require(key in profile['fields'] and profile['fields'][key]['authority'] == 'platform', key + ' must retain platform authority')
    require(profile['fields'].get('technicalPlan', {}).get('authority') == 'git', 'technical plan belongs to Git')
    for role, people in profile['roles'].items():
        require(bool(people), role + ' requires a role binding')
    return profile


def validate_configuration(root, binding, history):
    validate(binding, 'binding')
    validate(history, 'history')
    records = history['records']
    ids = set()
    prior = None
    connected = False
    for record in records:
        require(record['id'] not in ids, 'duplicate history identity')
        ids.add(record['id'])
        require(record['previousDigest'] == (authority.digest(prior) if prior else None), 'broken history chain')
        if record['action'] == 'activate':
            require(not connected, 'already activated')
            connected = True
        elif record['action'] == 'profile-change':
            require(connected, 'profile change requires activation')
        else:
            require(connected, 'disconnect requires activation')
            connected = False
        prior = record
    if binding['state'] == 'prepared':
        require(not records and binding['activationId'] is None, 'preparation cannot replace activation history')
    elif binding['state'] == 'enabled':
        require(connected and prior is not None, 'enabled binding requires accepted activation history')
    else:
        require(not connected, 'enabled delivery requires an explicit disconnect')
    if records:
        require(binding['activationId'] == prior['id'] and authority.digest(binding) == prior['bindingDigest'], 'binding changed since accepted decision')
        require(prior['profileDigest'] == binding['profile']['sha256'], 'history/profile digest mismatch')
    elif binding['activationId'] is not None:
        raise ValueError('PKD_CONTRACT_INVALID unknown activation identity')
    profile_path = authority.inside(root, binding['profile']['snapshot'])
    require(profile_path.is_file(), 'pinned profile snapshot is missing')
    require(hashlib.sha256(profile_path.read_bytes()).hexdigest() == binding['profile']['sha256'], 'profile snapshot digest mismatch')
    profile = validate_profile(authority.read(profile_path))
    require(profile['provider'] == binding['provider'] and profile['space'] == binding['space'], 'binding/profile authority mismatch')
    for entry, link in binding['workBindings'].items():
        require(bool(entry.strip()), 'empty local work identity')
        if link['executionMode'] == 'delegated':
            require(link['taskId'] is not None, 'delegated execution requires one meaningful Task')
        else:
            require(link['taskId'] is None, 'direct Requirement execution cannot also claim a Task')
    return profile


def validate_work(work, stage):
    work = normalize_work(work)
    validate(work, 'work')
    require(stage in ('draft', 'refinement', 'implementation'), 'unknown validation stage')
    required = ['title', 'outcome', 'businessOwnerId']
    if stage != 'draft':
        required += ['scope', 'nonGoals', 'architecturePrerequisites']
        require(bool(work['acceptanceCriteria']), 'refinement needs observable acceptance criteria')
    if stage == 'implementation':
        required += ['accountableExecutorId', 'verificationPlan', 'dependencyAssessment', 'coordinationAssessment']
        require(bool(work['technicalArtifacts']), 'implementation needs accepted technical artifacts')
        basis = work['acceptedBasis']
        require(basis is not None and basis['businessDigest'] == business_digest(work), 'accepted basis is absent or stale')
        require(basis['artifactDigest'] == authority.digest(work['technicalArtifacts']), 'technical artifact basis changed')
        require(not work['openDecisions'], 'resolve material decisions before implementation')
    for key in required:
        require(isinstance(work.get(key), str) and bool(work[key].strip()), f'{stage} requires {key}')
    ids = [item['id'] for item in work['acceptanceCriteria']]
    require(len(ids) == len(set(ids)), 'acceptance IDs must be unique')
    if work['kind'] == 'task':
        require(bool(work['parentRequirementId']) and bool(work['contribution']), 'Task needs a parent Requirement and meaningful contribution')
    if work['executionMode'] == 'delegated':
        require(work['kind'] == 'requirement' and bool(work['taskIds']), 'delegated Requirement needs explicit contributions')
    else:
        require(not work['taskIds'], 'direct execution cannot include delegated claims')
    return {'valid': True, 'stage': stage, 'scope': 'content-contract-only',
            'deliveryAdmission': False, 'note': 'Content validation does not approve prose, verify artifacts or authorize execution.'}


def business_digest(work):
    work = normalize_work(work)
    return authority.digest({key: work[key] for key in ('title', 'outcome', 'scope', 'nonGoals', 'architecturePrerequisites', 'acceptanceCriteria', 'businessOwnerId', 'parentRequirementId', 'contribution', 'executionMode', 'taskIds')})


def normalize_work(work):
    require(isinstance(work, dict), 'work must be an object')
    return {'scope': '', 'nonGoals': '', 'architecturePrerequisites': '', 'acceptanceCriteria': [],
            'accountableExecutorId': None, 'verificationPlan': None, 'dependencyAssessment': None,
            'coordinationAssessment': None, 'technicalArtifacts': [], 'acceptedBasis': None,
            'openDecisions': [], 'parentRequirementId': None, 'contribution': None,
            'executionMode': 'direct', 'taskIds': [], **work}
