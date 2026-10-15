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


class OwnershipError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise OwnershipError('PKU135 ' + message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


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


def source_guard(repository, release, name, metadata, manifest, sources, kind='extensions'):
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
        require(path.is_file(), 'missing native source: ' + name + ' / ' + relative)
        payloads[relative] = path.read_bytes(); hashes[relative] = digest(payloads[relative])
    if name.startswith('program-kit-'):
        verified, closest = False, set(sources)
        for witness, directory in witnesses:
            unmatched = set()
            for relative, payload in payloads.items():
                if isinstance(directory, dict):
                    matches = directory.get(relative) == hashes[relative]
                elif directory is not None:
                    publisher = directory / relative
                    matches = publisher.is_file() and publisher.read_bytes() == payload
                else:
                    result = subprocess.run(['git', '-C', str(release), 'show', witness.removeprefix('git:') + ':' + kind + '/' + name + '/' + relative],
                                            capture_output=True, timeout=15)
                    matches = result.returncode == 0 and result.stdout == payload
                if not matches:
                    unmatched.add(relative)
            if len(unmatched) < len(closest):
                closest = unmatched
            if not unmatched:
                verified = True; break
        require(verified, 'unresolved or customized installed Program Kit source: ' + name + ' / ' + ', '.join(sorted(closest))
                + '; native manifest_hash covers only the manifest; preserve the complete source component and reconcile against one authenticated original')
    return hashes


def installed_source_files(installed):
    """Machine sources; versioned package facts keep their separate immutable authority."""
    excluded = {'__pycache__', '.dev-cache', '.composed', '.git', 'bin', 'obj', 'node_modules'}
    return {path.relative_to(installed).as_posix() for path in installed.rglob('*')
            if path.is_file() and (path.relative_to(installed).parts[0] in {'commands', 'scripts', 'templates', 'config', 'references', 'docs'}
                                  or path.name in {'extension.yml', 'preset.yml', 'README.md'})
            and not (path.relative_to(installed).parts[0] == 'references'
                     and (path.relative_to(installed).parts[1:2] in {('dependency-profiles',), ('release-guidance',)}
                          or path.name in {'release-guidance.json', 'native-phase-source-baselines.json'}))
            and not excluded & set(path.relative_to(installed).parts)
            and path.suffix not in {'.pyc', '.pyo'} and path.name != '.keep-config'
            and not (path.parent == installed and (path.name.endswith('-config.yml') or path.name.endswith('-config.local.yml')))}


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


def rendered_outputs(repository, agent, manifest, installed, options):
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


def _preflight(repository, release=None, integration_keys=None):
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
    checked, generated_guidance = [], None
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
            sources.update(installed_source_files(installed))
        sources = sorted(sources)
        hashes = source_guard(repository, release, name, metadata, manifest, sources)
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
            expected = rendered_outputs(repository, agent, manifest, installed, options)
            for destination, native_bytes in expected.items():
                relative = destination.relative_to(repository).as_posix()
                target = contained(repository, relative, 'registered native phase output')
                if not target.exists():
                    continue  # An absent owned output is repaired, never a customization.
                require(target.is_file(), 'non-file native phase output: ' + relative)
                require(target.read_bytes() in native_bytes, 'consumer customization in native phase output: ' + name + ' / ' + agent + ' / ' + relative
                        + '; preserve it and reconcile the owner before refresh')
                if target.name == 'SKILL.md':
                    extra = [p.relative_to(repository).as_posix() for p in target.parent.rglob('*') if p.is_file() and p != target]
                    require(not extra, 'consumer files in regenerable skill directory: ' + relative + '; ' + ', '.join(extra))
                checked.append({'extension': name, 'integration': agent, 'path': relative,
                                'sha256': digest(target.read_bytes()), 'sourceSha256': hashes})
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
            sources.update(installed_source_files(installed))
            preset_sources[name] = source_guard(repository, release, name, metadata, manifest, sorted(sources), 'presets')
    return {'schemaVersion': 1, 'outputs': checked, 'presetSourceSha256': preset_sources,
            'generatedReleaseGuidance': generated_guidance, 'readOnly': True,
            'sourceScope': 'Exact installed manifests and authenticated Program Kit phase sources/references/docs; generated release guides, native retained config, consumer extension sources and selected versioned package evidence retain separate authority.'}


def preflight(repository, release=None, integration_keys=None):
    try:
        return _preflight(repository, release, integration_keys)
    except OwnershipError:
        raise
    except (ImportError, AttributeError, OSError, ValueError, TypeError, KeyError) as error:
        raise OwnershipError('PKU135 unsupported or unreadable native phase ownership binding ('
                             + type(error).__name__ + '); preserve installed sources/outputs and repair the scoped native registry/API') from error
