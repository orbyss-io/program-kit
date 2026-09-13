"""Manually queue and observe required synthetic PR policies within the shared run budget."""
import argparse
import json
from pathlib import Path
import sys
import uuid

from execution_setup import ROOT, PROJECT, REPOS
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import write
import azure_execution_evidence as evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', choices=['api', 'client'], required=True)
    parser.add_argument('--queue', action='store_true')
    parser.add_argument('--attempt', type=int, default=1)
    parser.add_argument('--iteration', choices=['initial', 'repair'], default='initial')
    args = parser.parse_args()
    output = ROOT / 'artifacts/delivery-phase4/pr-checks'
    output.mkdir(parents=True, exist_ok=True)
    api = AzureTransport('Unfussiness')
    profile = authority.read(output.parent / 'profile.json')
    provider = AzureProvider(api, profile)
    exercise = authority.read(output.parent / ('exercise-repair/journal.json' if args.iteration == 'repair' else 'exercise/journal.json'))
    pr_id = exercise['pr-' + args.repository]['value']['pullRequestId']
    pr = api.call('GET', f'/{PROJECT}/_apis/git/repositories/{REPOS[args.repository]}/pullrequests/{pr_id}')
    evaluations = api.list(f'/{PROJECT}/_apis/policy/evaluations', query={'artifactId': f'vstfs:///CodeReview/CodeReviewId/{PROJECT}/{pr_id}'}, version='7.1-preview.1')
    definition = 56 if args.repository == 'api' else 55
    applicable = [e for e in evaluations if e['configuration']['type']['id'] == evidence.BUILD_POLICY
                  and e['configuration']['settings']['buildDefinitionId'] == definition]
    if len(applicable) != 1 or pr['status'] != 'active' or pr['mergeStatus'] != 'succeeded':
        raise ValueError('Current synthetic PR or required build policy is not ready')
    evaluation = applicable[0]
    write(output / f'pr-{pr_id}.json', pr)
    write(output / f'evaluation-{pr_id}.json', evaluation)
    path = output.parent / 'pipelines/journal.json'
    journal = authority.read(path)
    existing = next((r for r in journal['runs'] if r.get('pullRequestId') == pr_id and r.get('attempt') == args.attempt), None)
    if args.queue and not existing:
        if len(journal['runs']) >= 12 or any(r['state'] != 'confirmed' for r in journal['runs']):
            raise ValueError('Pipeline budget exhausted or a dispatch remains uncertain')
        if evaluation.get('context', {}).get('buildId') and evaluation['status'] in ('queued', 'running'):
            raise ValueError('An existing build must finish before an explicit new attempt')
        existing = {'id': str(uuid.uuid4()), 'state': 'dispatched', 'pipelineId': definition, 'pullRequestId': pr_id,
            'attempt': args.attempt, 'evaluationId': evaluation['evaluationId'], 'priorBuildId': evaluation.get('context', {}).get('buildId'),
            'sourceCommit': pr['lastMergeSourceCommit']['commitId'], 'testedCommit': pr['lastMergeCommit']['commitId']}
        journal['runs'].append(existing)
        write(path, journal)
        evaluation = api.call('PATCH', f'/{PROJECT}/_apis/policy/evaluations/{evaluation["evaluationId"]}',
            {'status': 'queued'}, version='7.1-preview.1')
        write(output / f'queue-response-{pr_id}-{args.attempt}.json', evaluation)
    if existing:
        evaluation = api.call('GET', f'/{PROJECT}/_apis/policy/evaluations/{existing["evaluationId"]}', version='7.1-preview.1')
        write(output / f'evaluation-{pr_id}.json', evaluation)
        build_id = evaluation.get('context', {}).get('buildId')
        if build_id and build_id != existing.get('priorBuildId'):
            build = api.call('GET', f'/{PROJECT}/_apis/build/builds/{build_id}')
            if build['definition']['id'] != definition or build['sourceVersion'] != existing['testedCommit']:
                raise ValueError('Policy build differs from the dispatched exact candidate')
            existing.update(state='confirmed', buildId=build_id)
            write(path, journal)
            timeline = api.call('GET', f'/{PROJECT}/_apis/build/builds/{build_id}/timeline')
            write(output / f'build-{build_id}.json', build)
            write(output / f'timeline-{build_id}.json', timeline)
            if build['status'] == 'completed':
                for record in timeline['records']:
                    if record.get('log') and (record.get('result') == 'failed' or record['name'] == 'Verify current delivery authority and read-only job permissions'):
                        data = evidence.download(provider, record['log']['url'], accept='text/plain')
                        (output / f'build-{build_id}-log-{record["log"]["id"]}.txt').write_bytes(data)
            print(json.dumps({'buildId': build_id, 'status': build['status'], 'result': build.get('result'),
                'policy': evaluation['status'], 'runsUsed': len(journal['runs']), 'limit': 12,
                'issues': [i for r in timeline['records'] for i in r.get('issues', [])]}))
            return
    print(json.dumps({'pullRequestId': pr_id, 'policy': evaluation['status'], 'context': evaluation.get('context'),
                      'dispatchRecorded': existing is not None, 'runsUsed': len(journal['runs'])}))


if __name__ == '__main__':
    main()
