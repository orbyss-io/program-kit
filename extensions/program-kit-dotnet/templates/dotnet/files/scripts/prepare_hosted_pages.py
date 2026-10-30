"""Build and seal selected public frontends with the exact released producer."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import sys
import argparse
import uuid

import composition_model as model
import hosted_bundle
import runtime_closure
import foundation_qualification as qualification

BUILDER_SHA256 = '51b234a0d23ed1fe9e09483bba47e88c58398eb335582908fe9b32a558e5d06b'


def input_snapshot(root, graph, frontend_id):
    frontend = graph['resources'][frontend_id]
    directory = root / frontend['directory']
    result = model.resource_input_files(root, {'inputs': [frontend['directory'], *frontend.get('inputs', [])]})
    result['resource'] = model.digest(frontend)
    for name in ('.nvmrc', '.npm-version'):
        result[name] = runtime_closure.sha256(root / name)
    return result


def receipt_path(root, frontend_id):
    return root / 'artifacts/composition/frontends' / (frontend_id + '.json')


def admission(root, graph, frontend_id, required=True):
    path = receipt_path(root, frontend_id)
    if not path.is_file():
        if not required:
            return None
        raise ValueError('PKC110 selected frontend is unprepared: ' + frontend_id)
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('status') != 'built' or value.get('sourceInputs') != input_snapshot(root, graph, frontend_id):
        raise ValueError('PKC110 frontend inputs changed; build the affected application before run')
    frontend = graph['resources'][frontend_id]
    manifest = root / frontend['directory'] / 'dist/manifest.json'
    if runtime_closure.sha256(manifest) != value['manifestSha256']:
        raise ValueError('PKC110 compiled frontend manifest changed')
    return {'Root': frontend['directory'] + '/dist', 'Manifest': 'manifest.json',
            'ManifestSha256': value['manifestSha256'], 'CurrentRevision': value['revision']}


def build(root, graph, command, restore=False, selected_hosts=None):
    builder = root / 'tools/program-kit/vendor/foundation-0.3.3/create_hosted_manifest.py'
    model.require(builder.is_file() and runtime_closure.sha256(builder) == BUILDER_SHA256,
                  'exact released frontend manifest producer is missing or changed')
    selected_shells = {shell for host in selected_hosts for shell in model.host_shells(graph, host)} if selected_hosts else None
    frontends = {row['frontendRef'] for row in model.bindings(graph, 'frontend')
                 if selected_shells is None or row['shellRef'] in selected_shells}
    for frontend_id in sorted(frontends):
        frontend = graph['resources'][frontend_id]
        directory = root / frontend['directory']
        if restore:
            npm, environment = qualification.npm_command(root, ['ci', '--ignore-scripts'])
            command.run(npm, cwd=directory, environment=environment, timeout=600)
        before = input_snapshot(root, graph, frontend_id)
        previous = receipt_path(root, frontend_id)
        # A failed new build invalidates earlier frontend admission.
        runtime_closure.atomic_write(previous, {'status': 'building', 'sourceInputs': before})
        output = directory / 'dist'
        retained = None
        if (output / 'manifest.json').is_file():
            old = json.loads((output / 'manifest.json').read_text())
            options = {'CShells': {'Shells': {'content': {'Features': {hosted_bundle.FEATURE: {}}, 'Configuration': {'Foundation': {'HostedPages': {
                'Root': frontend['directory'] + '/dist', 'Manifest': 'manifest.json',
                'ManifestSha256': runtime_closure.sha256(output / 'manifest.json'), 'CurrentRevision': old['currentRevision']}}}}}}}
            inventory = hosted_bundle.inventory(root, options)
            retained = root / 'artifacts/composition/frontend-history' / frontend_id / runtime_closure.sha256(output / 'manifest.json')
            retained.mkdir(parents=True, exist_ok=True)
            for item in inventory:
                relative = Path(item['file']).relative_to(frontend['directory'] + '/dist')
                target = retained / relative; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / item['file'], target)
        npm, environment = qualification.npm_command(root, ['run', 'build'])
        command.run(npm, cwd=directory, environment=environment, timeout=600)
        if retained:
            old_manifest = retained / 'manifest.json'
            for file in retained.rglob('*'):
                if not file.is_file() or file == old_manifest:
                    continue
                target = output / file.relative_to(retained)
                if target.exists() and runtime_closure.sha256(target) != runtime_closure.sha256(file):
                    raise ValueError('PKC110 runtime filename is mutable; use the maintained content-hash build recipe')
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    shutil.copyfile(file, target)
            shutil.copyfile(old_manifest, output / 'retained-manifest.json')
        branding = frontend.get('branding', model.default_branding())
        (output / 'branding.json').write_text(json.dumps(branding), encoding='utf-8')
        revision = frontend_id + '-' + hashlib.sha256((output / '.vite/manifest.json').read_bytes() + json.dumps(branding, sort_keys=True).encode()).hexdigest()[:24]
        # An unchanged build retains its existing revision; avoid adding the same revision twice.
        unchanged = retained and json.loads((retained / 'manifest.json').read_text())['currentRevision'] == revision
        if unchanged:
            shutil.copyfile(retained / 'manifest.json', output / 'manifest.json')
        else:
            arguments = [sys.executable, str(builder), '--root', str(output), '--vite', '.vite/manifest.json',
                         '--branding', 'branding.json', '--entry', frontend['entry'], '--revision', revision,
                         '--form-release', frontend_id + '-scaffold']
            if retained:
                arguments += ['--retain', 'retained-manifest.json']
            command.run(arguments, timeout=120)
        model.require(before == input_snapshot(root, graph, frontend_id), 'frontend source changed during build; rebuild before sealing')
        runtime_closure.atomic_write(previous, {'status': 'built', 'sourceInputs': before, 'revision': revision,
                                              'manifestSha256': runtime_closure.sha256(output / 'manifest.json'),
                                              'producerSha256': BUILDER_SHA256})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--restore', action='store_true', help='Explicit locked npm acquisition before building')
    parser.add_argument('--check', action='store_true', help='Read-only frontend freshness admission; never builds or acquires')
    args = parser.parse_args()
    if args.check and args.restore:
        parser.error('--check cannot acquire dependencies')
    root = args.repository.resolve()
    if not (root / model.INPUT).is_file():
        print(json.dumps({'status': 'not-applicable', 'reason': 'No typed frontend composition is selected'}))
        return
    import composition_render
    graph, _ = composition_render.verify_outputs(root, check_frontends=False)
    frontends = sorted({row['frontendRef'] for row in model.bindings(graph, 'frontend')})
    if args.check:
        for name in frontends:
            admission(root, graph, name)
        print(json.dumps({'status': 'verified', 'frontends': frontends, 'applicationAcceptance': False}))
        return
    import composition_run
    directory = root / 'artifacts/frontend-build' / uuid.uuid4().hex
    directory.mkdir(parents=True)
    command = composition_run.Commands(root, directory)
    command.run([sys.executable, 'scripts/toolchain.py', '--repository', '.'])
    build(root, graph, command, restore=args.restore)
    for name in frontends:
        admission(root, graph, name)
    result = {'status': 'built', 'frontends': frontends, 'explicitRestore': args.restore, 'applicationAcceptance': False}
    runtime_closure.atomic_write(directory / 'result.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        print('PKC110 frontend preparation/admission failed: ' + str(error) +
              '. Recover with: python scripts/prepare_hosted_pages.py --repository . --restore', file=sys.stderr)
        raise SystemExit(2)
