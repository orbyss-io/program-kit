"""Bounded checks and explicit archive-preserving fixture pickup before dependent effects."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def plan(root, pins, contract=None):
    targets = (contract or {}).get('dependencyTargets', [])
    tools = set(pins.get('requiredTools', []))
    if any(Path(path).suffix == '.csproj' for path in targets):
        tools.add('dotnet')
    if any(Path(path).name == 'package.json' for path in targets):
        tools.update(('node', 'npm'))
    images = sorted({pins[key] for key in ('hostImage', 'identityImage', 'image') if pins.get(key)})
    browsers = sorted(set(pins.get('requiredBrowsers', [])))
    if pins.get('identityImage'):
        browsers = sorted(set(browsers) | {'chromium'})
        tools.update(('node', 'npm', 'dotnet'))
    if pins.get('hostImage') or pins.get('profile') == 'ef-postgresql':
        tools.add('dotnet')
    if any(not isinstance(image, str) or not re.fullmatch(r'[^\s@]+@sha256:[a-f0-9]{64}', image) for image in images):
        raise ValueError('PKP604 fixture images require exact immutable digests; repair the accepted recipe')
    if set(browsers) - {'chromium', 'firefox', 'webkit'} or tools - {'dotnet', 'node', 'npm'}:
        raise ValueError('PKP600 unsupported fixture requirements; declare a bounded preparation adapter')
    return {'schemaVersion': 1, 'tools': sorted(tools), 'images': images, 'browsers': browsers,
            'deviceInstallations': 'user-terminal-only', 'effects': 'read-only prerequisites; browser launch/close only'}


def check(root, pins, contract=None, runner=None, environment=None):
    runner = runner or subprocess.run
    root = Path(root).resolve()
    requirements = plan(root, pins, contract)
    record = root / 'artifacts/program-kit/toolchain.json'
    tools = json.loads(record.read_text(encoding='utf-8')) if record.is_file() else {}
    observed = {'python': {'executable': sys.executable, 'version': '.'.join(map(str, sys.version_info[:3]))},
                'tools': {}, 'images': [], 'browsers': []}
    if sys.version_info < (3, 11):
        raise ValueError('PKP600 fixture Python >=3.11 is required; select the recorded installed runtime')
    def run(command):
        try:
            return runner(command, cwd=root, env=environment, capture_output=True, text=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError('PKP600 prerequisite command is unavailable/timed out: ' + str(command[0])) from error
    for name in requirements['tools']:
        command = tools.get('commands', {}).get(name)
        required = tools.get('required', {}).get(name)
        if not isinstance(command, list) or not command or not isinstance(command[0], str) or not Path(command[0]).is_absolute() or not Path(command[0]).is_file() or not required:
            raise ValueError('PKP600 missing/stale recorded ' + name + ' executable; repair device selection and rerun supported toolchain readiness in the user terminal')
        result = run([*command, '--version'])
        actual = (result.stdout or '').strip().removeprefix('v')
        if result.returncode or actual != required:
            raise ValueError('PKP600 current ' + name + ' version differs from the exact recipe toolchain; repair selection and rerun readiness before this fixture')
        observed['tools'][name] = {'command': command, 'version': actual}
    # Start/close only the required empty browser before Docker can create anything.
    # Public Playwright launch checks the actual headless executable and support
    # libraries, rather than mistaking the full-browser executablePath for readiness.
    for browser in requirements['browsers']:
        command = tools.get('commands', {}).get('node')
        if not command:
            raise ValueError('PKP600 browser preparation needs the exact recorded Node command')
        probe = "(async()=>{const b=await require('playwright')." + browser + ".launch({headless:true});await b.close();process.stdout.write('ready')})().catch(()=>{process.exitCode=1})"
        result = run([*command, '-e', probe])
        if result.returncode or result.stdout.strip() != 'ready':
            raise ValueError('PKP605 required ' + browser + ' browser/headless binaries or support libraries are unavailable before container creation. In the user terminal run the exact-runtime npm exec -- playwright install ' + browser + ', then rerun this readiness check. This does not complete a product browser journey.')
        observed['browsers'].append(browser)
    if requirements['images']:
        docker = shutil.which('docker')
        if not docker or not Path(docker).is_file():
            raise ValueError('PKP601 Docker client is missing; complete device installation in the user terminal and rerun readiness')
        engine = run([docker, 'info', '--format', '{{json .}}'])
        if engine.returncode:
            detail = (engine.stderr or '').lower()
            if any(text in detail for text in ('permission denied', 'access is denied', 'access denied')):
                raise ValueError('PKP602 Docker engine/socket access denied; repair user access or authorize the exact fixture process boundary')
            raise ValueError('PKP601 Docker engine is unavailable; start the selected Linux engine in the user terminal')
        try:
            info = json.loads(engine.stdout)
        except (TypeError, ValueError) as error:
            raise ValueError('PKP601 Docker engine returned invalid readiness metadata') from error
        if info.get('OSType') != 'linux':
            raise ValueError('PKP601 fixture requires a Docker Linux engine; select it in the user terminal')
        observed['docker'] = {'executable': docker, 'version': info.get('ServerVersion'), 'os': 'linux'}
        for image in requirements['images']:
            inspection = run([docker, 'image', 'inspect', image, '--format', '{{json .}}'])
            if inspection.returncode:
                tag = image.split('@')[0]
                tagged = run([docker, 'image', 'inspect', tag, '--format', '{{json .}}'])
                if tagged.returncode == 0:
                    raise ValueError('PKP604 local image tag has a different digest; acquire the exact accepted reference: ' + image)
                raise ValueError('PKP603 exact fixture image is absent; provision before behavior with docker pull ' + image)
            value = json.loads(inspection.stdout)
            expected = image.split('@', 1)[1]
            if value.get('Os') != 'linux' or not any(reference.endswith('@' + expected) for reference in value.get('RepoDigests', [])):
                raise ValueError('PKP604 inspected image does not establish the exact accepted Linux digest: ' + image)
            observed['images'].append({'reference': image, 'id': value.get('Id')})
    return {'requirements': requirements, 'observed': observed, 'ready': True}


# Explicit fixture pickup shares the preparation module and preserves history.
"""Preview and explicitly materialize current fixture pins without rewriting history."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

def contained(repository, relative):
    path = (repository / relative).resolve()
    if not path.is_relative_to(repository.resolve()):
        raise ValueError('FIXTURE_PICKUP: path escapes repository: ' + relative)
    return path


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def xml_identity(payload):
    tree = ET.fromstring(payload)
    for node in tree.iter():
        if node.text is not None and not node.text.strip():
            node.text = None
        node.tail = None
    return ET.tostring(tree)


def native_pins(root):
    pins, sources, visited = {}, {}, set()
    def read(path):
        path = path.resolve()
        if path in visited:
            return
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('FIXTURE_PICKUP: native pin input is missing/external; repair normal sync first')
        visited.add(path)
        sources[path.relative_to(root).as_posix()] = sha(path.read_bytes())
        for node in ET.parse(path).getroot().iter():
            kind = node.tag.rsplit('}', 1)[-1]
            if kind == 'Import':
                relative = node.get('Project', '')
                if not relative or any(c in relative for c in '$@%*?;'):
                    raise ValueError('FIXTURE_PICKUP: dynamic native pins need an evaluated preparation adapter')
                child = (path.parent / relative.replace('\\', '/')).resolve()
                condition = node.get('Condition', '').strip()
                optional = condition in {"Exists('" + relative + "')", 'Exists("' + relative + '")'}
                if condition and not optional:
                    raise ValueError('FIXTURE_PICKUP: conditional native pins need an evaluated preparation adapter')
                if optional and not child.exists():
                    continue
                read(child)
            if kind != 'PackageVersion':
                continue
            identity = node.get('Include')
            version = node.get('Version') or node.findtext('Version')
            if not identity or not version or any(c in identity + version for c in '$@%*?;') or node.get('Condition'):
                raise ValueError('FIXTURE_PICKUP: native package pins need explicit literal or evaluated authority')
            if identity in pins and pins[identity] != version:
                raise ValueError('FIXTURE_PICKUP: conflicting native package pin: ' + identity)
            pins[identity] = version
    if (root / 'Directory.Packages.props').is_file():
        read(root / 'Directory.Packages.props')
    return pins, sources


def current_files(root, contract):
    from compatibility_scope import catalog
    from runtime_fixture import retarget_project
    blocks, selected, _ = catalog(root)
    effective = blocks.effective_dependency_context(root)
    native, sources = native_pins(root)
    sources.update({Path(path).relative_to(root).as_posix(): digest for path, digest in effective['sources'].items()})
    for identity, version in native.items():
        key = 'nuget:' + identity
        if key in selected['packages'] and selected['packages'][key]['version'] != version:
            raise ValueError('FIXTURE_PICKUP: managed/native pins disagree; settle selection and sync before fixture pickup: ' + identity)
    files = {}
    for relative, source in contract.get('fixtures', {}).items():
        path = contained(root, source)
        if not path.is_file():
            raise ValueError('FIXTURE_PICKUP: missing original fixture: ' + source)
        payload = path.read_bytes()
        sources[source] = sha(payload)
        if Path(relative).suffix == '.csproj':
            original = payload
            tree = ET.fromstring(payload)
            changed = False
            for reference in tree.iter('PackageReference'):
                identity = reference.get('Include')
                version = native.get(identity)
                if version and reference.get('Version') != version:
                    reference.set('Version', version)
                    changed = True
            if changed:
                payload = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
            references = {reference.get('Include') for reference in tree.iter('PackageReference')}
            if any('nuget:' + identity in selected['packages'] or identity in effective['sharedAbi']['pins'] for identity in references if identity):
                payload = retarget_project(payload, selected, effective['sharedAbi'])
            tree = ET.fromstring(payload)
            if any(item.get('Version') or item.findtext('Version') for item in tree.iter('PackageReference')):
                central = list(tree.iter('ManagePackageVersionsCentrally'))
                if not central:
                    central = [ET.SubElement(ET.SubElement(tree, 'PropertyGroup'), 'ManagePackageVersionsCentrally')]
                for setting in central:
                    if setting.get('Condition'):
                        raise ValueError('FIXTURE_PICKUP: fixture package-management mode must be unconditional')
                    setting.text = 'false'
            payload = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
            if xml_identity(original) == xml_identity(payload):
                payload = original
        if relative == 'runtime-inputs.json':
            parameters = json.loads(payload)
            original_parameters = dict(parameters)
            if any(key in parameters for key in ('dependencyProfile', 'catalogResolutionSha256', 'foundationRelease', 'sharedAbi')):
                authority_changed = (parameters.get('dependencyProfile') != effective['profile'] or
                                     parameters.get('catalogResolutionSha256') != effective['resolutionSha256'] or
                                     parameters.get('foundationRelease') != selected['families']['foundation']['releaseVersion'] or
                                     parameters.get('sharedAbi') != effective['sharedAbi'])
                parameters.update(dependencyProfile=effective['profile'], catalogResolutionSha256=effective['resolutionSha256'],
                                  foundationRelease=selected['families']['foundation']['releaseVersion'], sharedAbi=effective['sharedAbi'])
                if authority_changed and parameters.get('hostImage') and effective['profile']:
                    registry = root / '.specify/extensions/program-kit-building-blocks/references/dependency-profiles'
                    if not registry.is_dir():
                        raise ValueError('FIXTURE_PICKUP: install the exact publisher profile registry before recipe renewal')
                    index = blocks.load_json(registry / 'index.json')
                    knowledge_path = registry / index['profiles'][effective['profile']]['knowledge']['path']
                    knowledge = blocks.load_json(knowledge_path)
                    image = knowledge.get('hostImage')
                    if not isinstance(image, str) or not re.fullmatch(r'[^\s@]+@sha256:[a-f0-9]{64}', image):
                        raise ValueError('FIXTURE_PICKUP: selected publisher knowledge lacks an exact qualified Host image')
                    parameters['hostImage'] = image
                    sources[knowledge_path.relative_to(root).as_posix()] = sha(knowledge_path.read_bytes())
                if parameters.get('identityImage'):
                    from bootstrap_provider_context import project
                    decisions = blocks.load_json(root / 'docs/architecture/bootstrap-decisions.json')
                    parameters['identityImage'] = project(root, decisions)['identity_runtime']['image']
                    parameters.update(requiredTools=['dotnet', 'node', 'npm'], requiredBrowsers=['chromium'])
                else:
                    parameters.update(requiredTools=['dotnet'], requiredBrowsers=[])
                if parameters != original_parameters:
                    payload = (json.dumps(parameters, indent=2) + '\n').encode('utf-8')
        if Path(relative).name == 'package.json':
            package = json.loads(payload)
            changed = False
            for section in ('dependencies', 'devDependencies', 'optionalDependencies'):
                for identity in package.get(section, {}):
                    registered = selected['packages'].get('npm:' + identity)
                    if registered and package[section][identity] != registered['version']:
                        package[section][identity] = registered['version']
                        changed = True
            if changed:
                payload = (json.dumps(package, indent=2) + '\n').encode('utf-8')
        files[relative] = payload
    def maintained_support(relative):
        paths = [contained(root, prefix + relative) for prefix in ('.specify/extensions/', 'extensions/')]
        selected_path = next((path for path in paths if path.is_file()), None)
        if selected_path is None:
            raise ValueError('FIXTURE_PICKUP: install the maintained support before runtime fixture renewal: ' + relative)
        return selected_path
    if 'runtime_fixture.py' in files and 'fixture_readiness.py' not in files:
        readiness = maintained_support('program-kit-governance/scripts/fixture_readiness.py')
        files['fixture_readiness.py'] = readiness.read_bytes()
        sources[readiness.relative_to(root).as_posix()] = sha(files['fixture_readiness.py'])
    if 'runtime_probe.py' in files and 'owned_scratch.py' not in files:
        helper = maintained_support('program-kit-dotnet/templates/dotnet/files/eng/owned_scratch.py')
        files['owned_scratch.py'] = helper.read_bytes()
        sources[helper.relative_to(root).as_posix()] = sha(files['owned_scratch.py'])
    return files, sources


def stale_inputs(root, contract):
    files, _ = current_files(root, contract)
    stale = [source for relative, source in contract.get('fixtures', {}).items()
            if Path(relative).suffix == '.csproj' or Path(relative).name == 'package.json' or relative == 'runtime-inputs.json'
            if files[relative] != contained(root, source).read_bytes()]
    return stale + [relative + ' (required maintained support missing)' for relative in files if relative not in contract.get('fixtures', {})]


def preview(root, contract_path, identity):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', identity):
        raise ValueError('FIXTURE_PICKUP: use a new bounded lowercase recipe identity')
    source_contract = contained(root, contract_path)
    contract = json.loads(source_contract.read_text(encoding='utf-8'))
    recipe = source_contract.with_name(source_contract.name.removesuffix('.contract.json') + '.py')
    if not recipe.is_file():
        raise ValueError('FIXTURE_PICKUP: original recipe is missing')
    files, sources = current_files(root, contract)
    sources[contract_path] = sha(source_contract.read_bytes())
    sources[recipe.relative_to(root).as_posix()] = sha(recipe.read_bytes())
    directory = source_contract.parent
    fixtures = {relative: (directory / (identity + '.fixtures') / relative).relative_to(root).as_posix() for relative in files}
    new_contract = dict(contract, fixtures=fixtures)
    outputs = {fixtures[relative]: payload for relative, payload in files.items()}
    new_recipe = directory / (identity + '.py')
    outputs[new_recipe.relative_to(root).as_posix()] = recipe.read_bytes()
    outputs[new_recipe.with_suffix('.contract.json').relative_to(root).as_posix()] = (json.dumps(new_contract, indent=2) + '\n').encode('utf-8')
    value = {'schemaVersion': 1, 'identity': identity, 'sourceContract': contract_path,
             'newRecipe': new_recipe.relative_to(root).as_posix(), 'currentInputs': sources,
             'outputs': {path: sha(payload) for path, payload in outputs.items()},
             'staleInputs': stale_inputs(root, contract),
             'boundary': 'Draft fixture pickup only. No proof, provider call, authorization, ledger closure or pin adoption is established.'}
    value['planDigest'] = sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
    return value, outputs


def apply(root, contract_path, identity, digest):
    plan, outputs = preview(root, contract_path, identity)
    if plan['planDigest'] != digest:
        raise ValueError('FIXTURE_PICKUP: reviewed preview is stale; no inputs were changed')
    record_path = root / '.program-kit/fixture-pickup' / (identity + '.json')
    if record_path.exists() or any(contained(root, relative).exists() for relative in outputs):
        raise ValueError('FIXTURE_PICKUP: preserve existing pickup outcomes and choose a new identity; no automatic retry/reset')
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(plan, status='incomplete', archives={}, written=[])
    def save():
        record_path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    save()
    for source, expected in plan['currentInputs'].items():
        payload = contained(root, source).read_bytes()
        if sha(payload) != expected:
            raise ValueError('FIXTURE_PICKUP: source changed; original/incomplete record retained')
        archive = root / '.program-kit/installation/fixture-inputs' / (expected + '.original')
        archive.parent.mkdir(parents=True, exist_ok=True)
        if archive.exists() and archive.read_bytes() != payload:
            raise ValueError('FIXTURE_PICKUP: original archive changed; stop without rewriting history')
        if not archive.exists():
            archive.write_bytes(payload)
        record['archives'][source] = archive.relative_to(root).as_posix()
        save()
    for relative, payload in outputs.items():
        destination = contained(root, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(payload)
        record['written'].append(relative)
        save()
    record['status'] = 'materialized-draft'
    save()
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--contract', required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--plan-digest')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        value = apply(root, args.contract, args.identity, args.plan_digest) if args.apply else preview(root, args.contract, args.identity)[0]
        print(json.dumps(value, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
