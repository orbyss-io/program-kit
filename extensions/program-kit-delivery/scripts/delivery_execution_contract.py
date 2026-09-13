"""Execution policy and plans: explicit inputs, no provider calls or implied approvals."""
from copy import deepcopy
from datetime import date
from pathlib import PurePosixPath
import re

from delivery_contract import authority
from azure_provider import require

ACTIVITIES = ('implementation', 'integration', 'review', 'publish', 'delivery', 'acceptance')
CONDITIONS = ('contract', 'integration', 'delivery', 'acceptance')
SHA = re.compile(r'^[0-9a-f]{40}$')
HASH = re.compile(r'^[0-9a-f]{64}$')


def keys(value, required, optional=()):
    require(isinstance(value, dict) and set(required).issubset(value)
            and set(value).issubset(set(required) | set(optional)), 'execution object has missing or unknown fields')


def strings(value, *, nonempty=False):
    require(isinstance(value, list) and (value or not nonempty)
            and all(isinstance(v, str) and v.strip() for v in value)
            and len(set(value)) == len(value), 'expected unique nonempty strings')


def path(value):
    require(isinstance(value, str) and value and not value.startswith('/') and '\\' not in value
            and ':' not in value and all(p not in ('', '.', '..') for p in value.split('/')),
            'paths must be bounded repository-relative paths')
    return value


def policy(profile):
    result = profile.get('execution')
    keys(result, ('schemaVersion', 'teams', 'pipelines', 'tagCategories'), ('ciReaders',))
    if 'ciReaders' in result:
        strings(result['ciReaders'])
    require(result['schemaVersion'] == 1 and isinstance(result['teams'], dict) and result['teams'], 'execution policy is not configured')
    for team, value in result['teams'].items():
        require(team.strip(), 'team identity required')
        keys(value, ('repositories', 'executors', 'workInProgressWarning'))
        strings(value['repositories'], nonempty=True)
        strings(value['executors'], nonempty=True)
        require(set(value['executors']).issubset(profile['roles']['technical']), 'executors need configured technical authority')
        require(value['workInProgressWarning'] is None or type(value['workInProgressWarning']) is int
                and value['workInProgressWarning'] > 0, 'workload warning must be a positive threshold or null')
    require(isinstance(result['pipelines'], dict) and isinstance(result['tagCategories'], dict), 'pipeline and category mappings required')
    for name, rule in result['pipelines'].items():
        keys(rule, ('projectId', 'definitionId', 'repositoryId', 'finalYamlSha256', 'repositoryAliases',
                    'requiredJobs', 'artifactName', 'manifestPath', 'targetBranches'), ('toolRepositories',))
        require(name.strip() and type(rule['definitionId']) is int and rule['definitionId'] > 0
                and HASH.fullmatch(rule['finalYamlSha256']), 'pipeline must identify a reviewed definition and resolved YAML hash')
        require(rule['projectId'] == profile['azure']['projectId'], 'initial pipeline evidence must be in the configured project')
        require(isinstance(rule['repositoryAliases'], dict) and rule['repositoryAliases'].get('self') == rule['repositoryId'],
                'pipeline repository aliases must identify the triggering repository')
        require(isinstance(rule['targetBranches'], dict) and set(rule['targetBranches']) == set(rule['repositoryAliases'].values())
                and all(isinstance(branch, str) and re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*', branch)
                        for branch in rule['targetBranches'].values()), 'pipeline needs explicit target branches for all consumed repositories')
        require(isinstance(rule.get('toolRepositories', {}), dict)
                and not set(rule.get('toolRepositories', {})) & set(rule['repositoryAliases']), 'tool and subject aliases must be distinct')
        for tool in rule.get('toolRepositories', {}).values():
            keys(tool, ('repositoryId', 'commit'))
            require(isinstance(tool['repositoryId'], str) and tool['repositoryId'] and SHA.fullmatch(tool['commit']),
                    'CI tooling needs an immutable repository/commit binding')
        strings(rule['requiredJobs'], nonempty=True)
        path(rule['manifestPath'])
        require(isinstance(rule['artifactName'], str) and rule['artifactName'].strip(), 'artifact identity required')
    for category, tag in result['tagCategories'].items():
        require(category.strip() and isinstance(tag, str) and tag.startswith(profile['tagNamespace'] + ':')
                and ';' not in tag and len(tag) <= 100, 'generated tag must use the configured namespace')
    return result


def footprint(value):
    keys(value, ('writePaths', 'resources', 'categories', 'generatedSources'))
    strings(value['writePaths'], nonempty=True)
    for p in value['writePaths']:
        path(p)
        require(p not in ('*', '**', '**/*'), 'whole-repository wildcard is not a bounded footprint')
    strings(value['categories'])
    require(isinstance(value['resources'], list) and isinstance(value['generatedSources'], dict), 'resource and generated-source declarations required')
    seen = set()
    for resource in value['resources']:
        keys(resource, ('id', 'mode', 'contractRevision'))
        require(isinstance(resource['id'], str) and resource['id'].strip() and resource['id'] not in seen
                and resource['mode'] in ('read', 'change', 'exclusive')
                and isinstance(resource['contractRevision'], str) and resource['contractRevision'].strip(), 'invalid or duplicate resource declaration')
        seen.add(resource['id'])
    for generated, source in value['generatedSources'].items():
        path(generated)
        path(source)
    return value


def schedule(value):
    keys(value, ('plannedStart', 'targetFinish', 'committedDeadline'))
    for timestamp in value.values():
        require(timestamp is None or isinstance(timestamp, str), 'schedule values must be ISO dates or null')
        if timestamp is not None:
            require(date.fromisoformat(timestamp).isoformat() == timestamp, 'schedule date must be YYYY-MM-DD')
    if value['plannedStart'] and value['targetFinish']:
        require(value['plannedStart'] <= value['targetFinish'], 'target finish precedes planned start')


def plan(value, profile):
    keys(value, ('workId', 'repositoryId', 'teamId', 'executorId', 'targetBranch', 'baseCommit',
                 'technicalArtifacts', 'footprint', 'checks', 'dependencies', 'schedule', 'priority', 'milestones'))
    settings = policy(profile)
    team = settings['teams'].get(value['teamId'], {})
    require(value['executorId'] in team.get('executors', []) and value['repositoryId'] in team.get('repositories', []),
            'executor is not eligible for the selected team and repository')
    require(isinstance(value['workId'], str) and value['workId'].strip() and SHA.fullmatch(value['baseCommit']), 'work identity and immutable base required')
    require(re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*', value['targetBranch'])
            and '..' not in value['targetBranch'], 'invalid target branch')
    require(isinstance(value['technicalArtifacts'], list) and value['technicalArtifacts'], 'current accepted technical artifacts required')
    footprint(value['footprint'])
    require(set(value['footprint']['categories']).issubset(settings['tagCategories']), 'category has no reviewed native tag mapping')
    schedule(value['schedule'])
    require(value['priority'] is None or type(value['priority']) is int and 1 <= value['priority'] <= 4,
            'explicit priority must be 1 through 4 or null for inheritance')
    strings(value['milestones'])
    require(isinstance(value['checks'], list) and value['checks'], 'execution needs acceptance checks')
    seen = set()
    for check in value['checks']:
        keys(check, ('id', 'kind', 'acceptanceIds', 'pipeline', 'description'))
        require(isinstance(check['id'], str) and check['id'].strip() and check['id'] not in seen
                and check['kind'] in ('pipeline', 'manual') and check['description'].strip(), 'invalid acceptance check')
        seen.add(check['id'])
        strings(check['acceptanceIds'], nonempty=True)
        require(check['pipeline'] in settings['pipelines'] if check['kind'] == 'pipeline' else check['pipeline'] is None,
                'pipeline checks need a configured producer; manual criteria must be explicit')
    require(isinstance(value['dependencies'], list), 'dependencies must be explicit')
    seen = set()
    for edge in value['dependencies']:
        keys(edge, ('id', 'predecessor', 'blockedActivity', 'condition', 'checkIds', 'reason', 'externalReference'))
        require(edge['id'] not in seen and edge['id'].strip() and edge['predecessor'] != value['workId']
                and edge['blockedActivity'] in ACTIVITIES and edge['condition'] in CONDITIONS and edge['reason'].strip(),
                'invalid activity dependency')
        seen.add(edge['id'])
        strings(edge['checkIds'])
        require(edge['condition'] != 'integration' or edge['checkIds'], 'integration dependency needs receiving check identities')
        require(edge['externalReference'] is None or isinstance(edge['externalReference'], str)
                and edge['externalReference'].startswith('https://'), 'external reference must be HTTPS or null')
    return deepcopy(value)


def matches(filename, pattern):
    # Directory declarations include descendants. Glob matching remains advisory, never a lock.
    return filename == pattern or filename.startswith(pattern.rstrip('/') + '/') or PurePosixPath(filename).match(pattern)


def compare(left, right):
    """Conservative possible path overlap; declared semantic incompatibility is a hard conflict."""
    hard, possible = [], []
    a, b = left['footprint'], right['footprint']
    for x in a['resources']:
        for y in b['resources']:
            if x['id'] == y['id'] and ('exclusive' in (x['mode'], y['mode']) or
                    'change' in (x['mode'], y['mode']) and x['contractRevision'] != y['contractRevision']):
                hard.append(x['id'])
    if left['repositoryId'] == right['repositoryId']:
        for x in a['writePaths']:
            for y in b['writePaths']:
                if matches(x, y) or matches(y, x) or any(c in x + y for c in '*?['):
                    possible.append([x, y])
    return {'incompatibleResources': sorted(set(hard)), 'possiblePaths': possible,
            'assessment': 'coordinate' if hard else 'advisory' if possible else 'no-known-conflict'}
