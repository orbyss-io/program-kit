"""Read-only admission for native extension phase outputs before regeneration.

Re-render exact installed sources through maintained Spec Kit APIs into disposable
directories. Unknown ownership is unresolved; generated consumer edits are never
admitted merely because a registry names their destination.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from unittest.mock import patch
from contextlib import nullcontext


class OwnershipError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise OwnershipError('PKU135 ' + message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def asset_reader(release):
    """Only the verified release supplies code; installed packs are bounded data."""
    if release is None:return None
    source=Path(release)/'extensions/program-kit-governance/scripts/asset_sources.py'
    if not source.is_file():return None
    import importlib.util
    specification=importlib.util.spec_from_file_location('native_owned_asset_sources',source)
    module=importlib.util.module_from_spec(specification);specification.loader.exec_module(module)
    return module


def contained(root, relative, label):
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts, 'unsafe ' + label + ': ' + str(relative))
    target = root / path
    require(target.resolve().is_relative_to(root.resolve()), label + ' escapes consumer: ' + str(relative))
    require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                    for p in (target, *[p for p in target.parents if p != root and p.is_relative_to(root)])),
            'symlinked ' + label + ' requires explicit owner reconciliation: ' + str(relative))
    return target


def native_source_baselines(release, kind, name, metadata, manifest_hash):
    """Authenticate overwritten Program Kit sources where exact publisher bytes exist.

    Native registry manifest_hash authenticates the manifest only. It cannot
    authenticate independently edited command/template bytes. Current accepted
    release and immutable Git trees are bounded additional source witnesses.
    """
    if release is None:
        return []
    directory = Path(release) / kind / name
    filename = 'extension.yml' if kind == 'extensions' else 'preset.yml'
    result = []
    if (directory / filename).is_file() and digest((directory / filename).read_bytes()) == manifest_hash:
        result.append(('accepted-release', directory))
    catalog = Path(release) / 'extensions/program-kit-governance/references/native-phase-source-baselines.json'
    if not catalog.is_file():
        catalog = Path(release) / 'releases/native-phase-source-baselines.json'
    if catalog.is_file():
        table = json.loads(catalog.read_text(encoding='utf-8'))
        require(table.get('schemaVersion') == 1 and isinstance(table.get('components'), list)
                and all(isinstance(row, dict) for row in table['components']),
                'malformed immutable native phase source catalog')
        for row in table['components']:
            if (row.get('kind'), row.get('id'), str(row.get('version')), row.get('manifestSha256')) != (
                    kind, name, str(metadata.get('version')), manifest_hash):
                continue
            require(isinstance(row.get('files'), dict) and row['files']
                    and isinstance(row.get('sourceCommit'), str) and re.fullmatch(r'[0-9a-f]{40}', row['sourceCommit'])
                    and all(isinstance(path, str) and isinstance(sha, str) and re.fullmatch(r'[0-9a-f]{64}', sha)
                            for path, sha in row['files'].items()), 'invalid exact native phase source witness: ' + name)
            result.append(('immutable-source-catalog', row['files']))
    for reference in ('HEAD', 'v' + str(metadata.get('version', '')), str(metadata.get('version', ''))):
        if not reference or reference == 'v' or not re.fullmatch(r'[A-Za-z0-9_.-]+', reference):
            continue
        try:
            observed = subprocess.run(['git', '-C', str(release), 'show', reference + ':' + kind + '/' + name + '/' + filename],
                                      capture_output=True, timeout=15)
        except (OSError, subprocess.SubprocessError):
            continue
        if observed.returncode == 0 and digest(observed.stdout) == manifest_hash:
            result.append(('git:' + reference, None))
    return result


def source_guard(repository, release, name, metadata, manifest, sources, kind='extensions', deviations=None):
    reader=asset_reader(release)
    expected = metadata.get('manifest_hash')
    require(isinstance(expected, str) and re.fullmatch(r'(?:sha256:)?[0-9a-f]{64}', expected),
            'unresolved installed native manifest integrity: ' + name)
    expected = expected.removeprefix('sha256:')
    require(manifest.get_hash().removeprefix('sha256:') == expected,
            'installed native manifest has consumer edits: ' + name + '; preserve and reconcile its owner')
    witnesses = native_source_baselines(release, kind, name, metadata, expected) if name.startswith('program-kit-') else []
    hashes, payloads = {}, {}
    for relative in sources:
        path = contained(repository, '.specify/' + kind + '/' + name + '/' + relative, 'installed native source')
        require(path.is_file() or reader is not None and reader.owner(path) is not None,
                'missing native source: ' + name + ' / ' + relative)
        payloads[relative] = reader.read(path) if reader else path.read_bytes()
        hashes[relative] = digest(payloads[relative])
    if name.startswith('program-kit-'):
        prefix = '.specify/' + kind + '/' + name + '/'
        repairs = {path[len(prefix):]: row for path, row in (deviations or {}).items() if path.startswith(prefix)}
        verified, closest = False, None
        for witness, directory in witnesses:
            if isinstance(directory, dict):
                expected_names = {relative for relative in directory if machine_source_path(relative)}
            elif directory is not None:
                expected_names = installed_source_files(directory, release)
            else:
                tree = subprocess.run(['git', '-C', str(release), 'ls-tree', '-r', '--name-only', '-z',
                    witness.removeprefix('git:') + ':' + kind + '/' + name], capture_output=True, timeout=15)
                if tree.returncode != 0: continue
                expected_names = {relative for relative in tree.stdout.decode('utf-8').split('\0')
                                  if relative and machine_source_path(relative)}
            # Declared native command/script paths outside the ordinary source
            # roots still receive exact byte comparison below. Missing ordinary
            # helpers cannot disappear merely because current discovery omits them.
            expected_names.update(relative for relative in sources if not machine_source_path(relative))
            expected_names.update(relative for relative, row in repairs.items() if row['beforeSha256'] is None)
            unmatched = expected_names.symmetric_difference(set(sources))
            for relative, payload in payloads.items():
                if isinstance(directory, dict):
                    original_hash = directory.get(relative)
                elif directory is not None:
                    publisher = directory / relative
                    try:original=reader.read(publisher) if reader else publisher.read_bytes()
                    except FileNotFoundError:original=None
                    original_hash = digest(original) if original is not None else None
                else:
                    result = subprocess.run(['git', '-C', str(release), 'show', witness.removeprefix('git:') + ':' + kind + '/' + name + '/' + relative],
                                            capture_output=True, timeout=15)
                    original_hash = digest(result.stdout) if result.returncode == 0 else None
                repair = repairs.get(relative)
                matches = original_hash == hashes[relative] if repair is None else (
                    original_hash == repair['beforeSha256'] and hashes[relative] == repair['afterSha256'])
                if not matches:
                    unmatched.add(relative)
            if closest is None or len(unmatched) < len(closest):
                closest = unmatched
            if not unmatched:
                verified = True; break
        require(verified, 'unresolved or customized installed Program Kit source: ' + name + ' / ' + ', '.join(sorted(closest or set(sources)))
                + '; native manifest_hash covers only the manifest; preserve the complete source component and reconcile against one authenticated original')
    return hashes


def machine_source_path(relative):
    parts = Path(relative).parts
    excluded = {'__pycache__', '.dev-cache', '.composed', '.git', 'bin', 'obj', 'node_modules'}
    return bool(parts) and (parts[0] in {'commands', 'scripts', 'templates', 'config', 'references', 'docs', 'examples'}
            or Path(relative).name in {'extension.yml', 'preset.yml', 'README.md'}) \
        and not (parts[0] == 'references' and (parts[1:2] in {('dependency-profiles',), ('release-guidance',)}
                 or Path(relative).name in {'release-guidance.json', 'native-phase-source-baselines.json'})) \
        and not excluded & set(parts) and Path(relative).suffix not in {'.pyc', '.pyo'} \
        and Path(relative).name != '.keep-config' \
        and not (len(parts) == 1 and (Path(relative).name.endswith('-config.yml') or Path(relative).name.endswith('-config.local.yml')))


def installed_source_files(installed, release=None):
    """Machine sources; versioned package facts keep their separate immutable authority."""
    reader = asset_reader(release)
    paths = {path.relative_to(installed).as_posix() for path in installed.rglob('*') if path.is_file()}
    if reader: paths.update(reader.packed(installed))
    return {relative for relative in paths if machine_source_path(relative)}


def generated_guidance_guard(repository, release, metadata):
    """Generated packaged guides retain their existing checksum/index authority."""
    directory = contained(repository, '.specify/extensions/program-kit-governance/references/release-guidance', 'generated release guidance')
    if not directory.exists():
        return None
    import importlib.util
    source = Path(release) / 'extensions/program-kit-governance/scripts/release_guidance.py' if release else None
    require(source is not None and source.is_file(), 'generated release guidance has no supported candidate validator')
    spec = importlib.util.spec_from_file_location('native_phase_generated_guidance_guard', source)
    validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
    require(callable(getattr(validator, 'load_index', None)), 'unsupported generated release guidance validator API')
    try:
        validator.load_index(directory, metadata['version'])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise OwnershipError('PKU135 generated release guidance failed its existing index/checksum authority: '
                             + directory.relative_to(repository).as_posix()) from error
    return {'owner': 'existing-release-guidance-index-validator', 'version': metadata['version'],
            'indexSha256': digest((directory / 'migration-index.json').read_bytes())}


def rendered_outputs(repository, agent, manifest, installed, options, interpreter=None):
    from specify_cli.integrations.base import IntegrationBase
    with (patch.object(IntegrationBase,'resolve_python_interpreter',return_value=interpreter)
          if interpreter is not None else nullcontext()):
        return _rendered_outputs(repository,agent,manifest,installed,options)


def _rendered_outputs(repository, agent, manifest, installed, options):
    from specify_cli.agents import CommandRegistrar
    from specify_cli.extensions import ExtensionManager
    registrar = CommandRegistrar(repository)
    require(agent in registrar.AGENT_CONFIGS, 'unsupported native output binding: ' + agent)
    config = registrar.AGENT_CONFIGS[agent]
    actual = registrar._resolve_agent_dir(agent, config, repository)
    require(actual.resolve().is_relative_to(repository.resolve()), 'native output binding is outside consumer: ' + agent)
    expected = {}
    with tempfile.TemporaryDirectory(prefix='program-kit-native-output-') as name:
        temporary = Path(name)
        command_dir = temporary / 'commands'
        prompt_dir = temporary / '.github/prompts'
        def prompt(_root, command):
            CommandRegistrar.write_copilot_prompt(temporary, command)
        # Public maintained registrar; redirect every generated destination.
        with patch.object(registrar, 'write_copilot_prompt', side_effect=prompt):
            registered = registrar.register_commands(agent, manifest.commands, manifest.id, installed, repository,
                context_note=f'\n<!-- Extension: {manifest.id} -->\n<!-- Config: .specify/extensions/{manifest.id}/ -->\n',
                _resolved_dir=command_dir, extension_id=manifest.id, author=manifest.data['extension'].get('author'))
        declared = {command['name'] for command in manifest.commands}
        declared.update(alias for command in manifest.commands for alias in command.get('aliases', []))
        require(set(registered) == declared, 'incomplete native command rendering: ' + manifest.id + ' / ' + agent)
        for file in command_dir.rglob('*'):
            if file.is_file():
                destination = actual / file.relative_to(command_dir)
                expected.setdefault(destination, set()).add(file.read_bytes())
        for file in prompt_dir.glob('*'):
            if file.is_file():
                expected.setdefault(repository / '.github/prompts' / file.name, set()).add(file.read_bytes())
        # The maintained extension skill renderer also owns historical skill
        # headings that differ from register_commands' native skill form.
        manager = ExtensionManager(repository)
        skills = temporary / 'skills'
        with patch.object(manager, '_get_skills_dir', return_value=skills), patch('specify_cli.load_init_options', return_value=options):
            manager._register_extension_skills(manifest, installed)
        from specify_cli import _get_skills_dir
        skills_actual = actual if config.get('extension') == '/SKILL.md' else _get_skills_dir(repository, agent)
        require(skills_actual.resolve().is_relative_to(repository.resolve()), 'native skill binding is outside consumer: ' + agent)
        for file in skills.rglob('*'):
            if file.is_file():
                destination = skills_actual / file.relative_to(skills)
                expected.setdefault(destination, set()).add(file.read_bytes())
    return expected


def _preflight(repository, release=None, integration_keys=None, deviations=None):
    repository = Path(repository).resolve()
    from specify_cli import load_init_options
    from specify_cli.extensions import ExtensionManager, ExtensionManifest
    from specify_cli.integrations import get_integration
    from specify_cli.integrations._helpers import _resolve_integration_options
    registry_path = contained(repository, '.specify/extensions/.registry', 'native extension registry')
    require(registry_path.is_file(), 'missing native extension registry')
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    require(isinstance(registry, dict) and isinstance(registry.get('extensions'), dict), 'malformed native extension registry')
    state_path = contained(repository, '.specify/integration.json', 'native integration settings')
    state = json.loads(state_path.read_text(encoding='utf-8'))
    require(isinstance(state, dict), 'malformed native integration settings')
    keys = integration_keys or state.get('installed_integrations', [state.get('default_integration') or state.get('integration')])
    require(isinstance(keys, list) and keys and all(isinstance(k, str) for k in keys), 'unresolved installed integration bindings')
    base_options = load_init_options(repository)
    require(isinstance(base_options, dict), 'unresolved native initialization options')
    checked, generated_guidance, extension_sources = [], None, {}
    import importlib.util
    profile_source=Path(release)/'extensions/program-kit-governance/scripts/render_profile.py' if release else None
    require(profile_source is not None and profile_source.is_file(),'native generation profile reader is unavailable')
    profile_spec=importlib.util.spec_from_file_location('phase_native_render_profile',profile_source)
    profile=importlib.util.module_from_spec(profile_spec);profile_spec.loader.exec_module(profile)
    render_reader=profile.Reader(repository)
    for name, metadata in registry['extensions'].items():
        require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_-]+', name) and isinstance(metadata, dict), 'invalid native extension ownership')
        if not metadata.get('enabled', True) and not name.startswith('program-kit-'):
            continue
        installed = contained(repository, '.specify/extensions/' + name, 'native extension')
        manifest_path = contained(repository, '.specify/extensions/' + name + '/extension.yml', 'installed extension manifest')
        manifest = ExtensionManifest(manifest_path)
        registered = metadata.get('registered_commands', {})
        skill_names = metadata.get('registered_skills', [])
        require(isinstance(registered, dict) and all(isinstance(k, str) and isinstance(v, list) and all(isinstance(n, str) for n in v)
                for k, v in registered.items()) and isinstance(skill_names, list) and all(isinstance(n, str) for n in skill_names),
                'unresolved native extension registrations: ' + name)
        sources = {command['file'] for command in manifest.commands}
        sources.update(script['file'] for script in manifest.scripts)
        if name.startswith('program-kit-'):
            sources.update(installed_source_files(installed,release))
        sources = sorted(sources)
        hashes = source_guard(repository, release, name, metadata, manifest, sources, deviations=deviations)
        extension_sources[name] = hashes
        if name == 'program-kit-governance':
            generated_guidance = generated_guidance_guard(repository, release, metadata)
        if not metadata.get('enabled', True):
            continue  # Disabled publisher sources may still be replaced by component installation.
        declared_commands = {command['name'] for command in manifest.commands}
        declared_commands.update(alias for command in manifest.commands for alias in command.get('aliases', []))
        declared_skills = {command.replace('speckit.', 'speckit-').replace('.', '-') for command in declared_commands}
        require(all(set(names) <= declared_commands for names in registered.values()) and set(skill_names) <= declared_skills,
                'registered extension output has no exact current source binding: ' + name)
        # Registration can outlive an integration's active status. Refresh/removal
        # may touch those recorded outputs too, so inspect every recorded agent.
        for agent in sorted(set(keys) | set(registered)):
            integration = get_integration(agent)
            require(integration is not None, 'unsupported registered integration: ' + agent + ' / ' + name)
            _, parsed = _resolve_integration_options(integration, state, agent, None)
            options = {**base_options, 'ai': agent, 'integration': agent}
            if integration.is_skills_mode(parsed, project_root=repository):
                options['ai_skills'] = True
            else:
                options.pop('ai_skills', None)
            # Enumerate destinations through the native renderer without probing
            # today's PATH. Each actual comparison uses its own original profile.
            destinations = rendered_outputs(repository, agent, manifest, installed, options,interpreter='python')
            variants={}
            for destination in destinations:
                relative = destination.relative_to(repository).as_posix()
                target = contained(repository, relative, 'registered native phase output')
                if not target.exists():
                    continue  # An absent owned output is repaired, never a customization.
                require(target.is_file(), 'non-file native phase output: ' + relative)
                generation=render_reader.profile(relative)
                choice=generation['interpreter'] if generation else None
                if choice not in variants:variants[choice]=rendered_outputs(repository,agent,manifest,installed,options,interpreter=choice)
                native_bytes=variants[choice][destination]
                if generation:
                    require(generation['sha256'] in {digest(value) for value in native_bytes},
                            'original generation inputs no longer reproduce their output: '+relative)
                require(target.read_bytes() in native_bytes, 'consumer customization in native phase output: ' + name + ' / ' + agent + ' / ' + relative
                        + ('; preserve it and reconcile the owner before refresh' if generation else
                           '; original generation profile is missing; current PATH reproduction supplies no historical alias provenance'))
                if target.name == 'SKILL.md':
                    extra = [p.relative_to(repository).as_posix() for p in target.parent.rglob('*') if p.is_file() and p != target]
                    require(not extra, 'consumer files in regenerable skill directory: ' + relative + '; ' + ', '.join(extra))
                checked.append({'extension': name, 'integration': agent, 'path': relative,
                                'sha256': digest(target.read_bytes()), 'sourceSha256': hashes,
                                'renderProvenance':'original-native-generation' if generation else 'current-render-only; historical-profile-unavailable'})
    preset_sources = {}
    preset_registry = contained(repository, '.specify/presets/.registry', 'native preset registry')
    if preset_registry.is_file():
        from specify_cli.presets import PresetManifest
        presets = json.loads(preset_registry.read_text(encoding='utf-8'))
        require(isinstance(presets, dict) and isinstance(presets.get('presets'), dict), 'malformed native preset registry')
        for name, metadata in presets['presets'].items():
            require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_-]+', name) and isinstance(metadata, dict), 'invalid native preset ownership')
            if not name.startswith('program-kit-'):
                continue
            installed = contained(repository, '.specify/presets/' + name, 'installed native preset')
            manifest_path = contained(repository, '.specify/presets/' + name + '/preset.yml', 'installed preset manifest')
            manifest = PresetManifest(manifest_path)
            sources = {row['file'] for row in manifest.templates}
            sources.update(installed_source_files(installed,release))
            preset_sources[name] = source_guard(repository, release, name, metadata, manifest, sorted(sources), 'presets', deviations)
    return {'schemaVersion': 1, 'outputs': checked, 'presetSourceSha256': preset_sources,
            'extensionSourceSha256': extension_sources,
            'generatedReleaseGuidance': generated_guidance, 'readOnly': True,
            'sourceScope': 'Exact installed manifests and authenticated Program Kit phase sources/references/docs; generated release guides, native retained config, consumer extension sources and selected versioned package evidence retain separate authority.'}


def preflight(repository, release=None, integration_keys=None, deviations=None):
    try:
        return _preflight(repository, release, integration_keys, deviations)
    except OwnershipError:
        raise
    except (ImportError, AttributeError, OSError, ValueError, TypeError, KeyError) as error:
        raise OwnershipError('PKU135 unsupported or unreadable native phase ownership binding ('
                             + type(error).__name__ + '); preserve installed sources/outputs and repair the scoped native registry/API') from error


def tested_deviations(repository, release, declaration, expected, prior_inputs=None):
    """Fresh execution of reviewed current cases, with original publisher comparison.

    The explicit declaration is a local review input. Its hash is not publisher
    authentication or proof that the selected cases cover the repair's semantics.
    The normal guard authenticates every original against one complete component.
    """
    runner = Path(release) / 'extensions/program-kit-governance/scripts/case_inventory.py'
    import importlib.util
    spec = importlib.util.spec_from_file_location('upgrade_current_case_inventory', runner)
    cases = importlib.util.module_from_spec(spec); spec.loader.exec_module(cases)
    require(isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected), 'original reviewed local repair declaration SHA-256 is required')
    path = cases.inside(repository, declaration)
    require(path.is_file() and path.stat().st_size <= 2_097_152, 'local repair declaration missing or oversized')
    raw = path.read_bytes(); require(digest(raw) == expected, 'local repair declaration differs from its review anchor')
    value = json.loads(raw, object_pairs_hook=cases.unique)
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'contract', 'contractSha256', 'repairs'}
            and value['schemaVersion'] == 1 and isinstance(value['repairs'], list) and 0 < len(value['repairs']) <= 128,
            'local repairs need a finite exact declaration and current case contract')
    definitions, inputs = cases.contract(repository, value['contract'], value['contractSha256'])
    all_cases = {case: platforms for row in definitions.values() for case, platforms in row['cases'].items()}
    import platform
    repairs, active = {}, {}
    for row in value['repairs']:
        require(isinstance(row, dict) and set(row) == {'path', 'beforeSha256', 'afterSha256', 'requiredCases', 'rationale'},
                'each local repair needs exact before/after sources, required cases and review rationale')
        relative = row['path']; target = cases.inside(repository, relative); parts = Path(relative).parts
        require(len(parts) >= 5 and parts[0] == '.specify' and parts[1] in {'extensions', 'presets'}
                and parts[2].startswith('program-kit-') and machine_source_path('/'.join(parts[3:]))
                and relative not in repairs and relative.casefold() not in {name.casefold() for name in repairs},
                'local repair must name one exact installed Program Kit machine source')
        require((row['beforeSha256'] is None or isinstance(row['beforeSha256'], str) and re.fullmatch('[a-f0-9]{64}', row['beforeSha256']))
                and isinstance(row['afterSha256'], str) and re.fullmatch('[a-f0-9]{64}', row['afterSha256'])
                and row['beforeSha256'] != row['afterSha256'], 'local repair must change an exact original source; deletions need separate owner reconciliation')
        require(isinstance(row['rationale'], str) and 0 < len(row['rationale'].strip()) <= 4096
                and isinstance(row['requiredCases'], list) and row['requiredCases']
                and len(set(row['requiredCases'])) == len(row['requiredCases'])
                and all(case in all_cases and platform.system() in all_cases[case] for case in row['requiredCases']),
                'local repair requires nonempty exact current-platform regression identities and reviewed coverage rationale')
        require(relative in inputs and target.is_file(), 'local repaired source must be an actual required case input')
        if prior_inputs is not None:
            require(prior_inputs.get('files', {}).get(relative) == row['afterSha256'],
                    'retry local repair differs from the canonical original attempt inventory')
        elif digest(target.read_bytes()) != row['afterSha256']:
            raise OwnershipError('PKU135 local repaired source differs from its reviewed after hash: ' + relative)
        repairs[relative] = row
        if digest(target.read_bytes()) == row['afterSha256']: active[relative] = row
    # Before executing any selected current test, establish complete authentic
    # originals. No supplied execution report can bypass this read-only admission.
    admitted = preflight(repository, release, deviations=active)
    authenticated = {'.specify/' + kind + '/' + component + '/' + relative
        for kind, key in (('extensions', 'extensionSourceSha256'), ('presets', 'presetSourceSha256'))
        for component, files in admitted[key].items() for relative in files}
    require(set(repairs) <= authenticated, 'spurious local repair lacks an authenticated registered source owner')
    def inventory():
        result = {}
        for kind in ('extensions', 'presets'):
            for component in sorted((repository / '.specify' / kind).glob('program-kit-*')):
                for relative in installed_source_files(component, release):
                    target = component / relative
                    reader = asset_reader(release)
                    result[target.relative_to(repository).as_posix()] = digest(reader.read(target) if reader else target.read_bytes())
        return result
    before = inventory()
    require(set(repairs) <= set(before), 'spurious local repair has no installed source owner')
    modules = sorted({case.split('.')[0] for row in repairs.values() for case in row['requiredCases']})
    result = cases.execute(repository, value['contract'], value['contractSha256'], modules)
    for relative, row in repairs.items():
        require(result['inputSha256'].get(relative) == before[relative]
                and all(result['executedCases'].get(case) == 'passed' for case in row['requiredCases']),
                'local repair lacks actual successful required-case/source execution: ' + relative)
    require(inventory() == before and path.read_bytes() == raw, 'installed source set or local repair declaration changed during execution')
    return active, {'schemaVersion': 1, 'declaration': declaration, 'declarationSha256': expected,
        'contract': value['contract'], 'contractSha256': value['contractSha256'], 'repairs': value['repairs'],
        'execution': result, 'installedSourceSha256': before,
        'claim': 'Current executed local repair evidence; original publisher, generated outputs and historical receipts retain separate authority.',
        'productAcceptanceEstablished': False, 'publisherAuthenticityEstablished': False}
