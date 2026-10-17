from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
import tempfile
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
import retired_sync_integration
import native_phase_ownership
import copy

from openapi_upgrade_reconciliation import (
    ReconciliationError,
    apply as apply_openapi_reconciliation,
    describe as describe_openapi_reconciliation,
    discover as discover_openapi_reconciliation,
    catalog_transition,
    archive_catalog_transition,
    apply_catalog_transition,
    target_exporter_version,
    validate_exporter_catalog_transition,
)


COMPONENTS = (
    ("bundle", Path("bundle.yml")),
    ("governance extension", Path("extensions/program-kit-governance/extension.yml")),
    ("building-block extension", Path("extensions/program-kit-building-blocks/extension.yml")),
    (".NET extension", Path("extensions/program-kit-dotnet/extension.yml")),
    ("governance preset", Path("presets/program-kit-governance-preset/preset.yml")),
    ("bootstrap workflow", Path("workflows/program-kit-bootstrap/workflow.yml")),
)


class UpgradeError(ValueError):
    pass


@dataclass(frozen=True)
class UpgradeRetryContext:
    """Verified attempt inputs; admits only the specific original/target transition."""
    repository: Path
    target_version: str
    original_version: str
    release_fingerprint: str
    attempt_path: Path
    originals: dict

    def original_bytes(self, name: str) -> bytes | None:
        record = self.originals.get(name)
        if not record:
            return None
        archived = (self.repository / record['path']).resolve()
        if not archived.is_relative_to(self.repository) or not archived.is_file():
            raise UpgradeError('PKU121 original retry input is missing or changed: ' + name)
        payload = archived.read_bytes()
        if hashlib.sha256(payload).hexdigest() != record['sha256']:
            raise UpgradeError('PKU121 original retry input is missing or changed: ' + name)
        return payload

    def original_matches(self, name: str, current: Path) -> bool:
        original = self.original_bytes(name)
        return original is not None and current.is_file() and current.read_bytes() == original

    def selection_matches(self, current: Path, release: Path, resolver) -> bool:
        if self.original_matches('selection', current):
            return True
        if not {'selection', 'catalog'} <= self.originals.keys():
            return False
        original = json.loads(self.original_bytes('selection'))
        old = json.loads(self.original_bytes('catalog'))
        new = resolver.load_json(release / 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.json')
        try:
            validate_exporter_catalog_transition(resolver, old, new, release)
        except ReconciliationError:
            return False
        expected = copy.deepcopy(original)
        expected['status'] = 'Accepted'
        expected['revision'] += 1
        expected['catalog'] = resolver.catalog_binding(new)
        expected.pop('draftSuggestions', None)
        return resolver.load_json(current) == expected

    def architecture_matches(self, selection_path: Path, resolver) -> bool:
        selection = resolver.load_json(selection_path)
        current = resolver.repository_path(self.repository, selection['authority']['architectureMap'])
        if self.original_matches('architecture', current):
            return True
        original = self.original_bytes('architecture')
        if original is None:
            return False
        expected = resolver.registered_selection(self.repository, selection_path, selection, json.loads(original))
        return resolver.load_json(current) == expected


def upgrade_retry_context(target: Path, release: Path, version: str, repair_of: str | None = None):
    prior, fingerprint, _ = prior_attempt(target, release, version, repair_of)
    if not prior:
        return None
    return UpgradeRetryContext(target.resolve(), version, prior[1]['previousInstalledVersion'],
                               fingerprint, prior[0], dict(prior[1]['originals']))


def configure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


def manifest_version(path: Path, label: str) -> str:
    if not path.is_file():
        raise UpgradeError(f"PKU101 {label} is missing: {path}")
    match = re.search(
        r"^\s{2}version:\s*[\"']?([^\"'#\s]+)",
        path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        raise UpgradeError(f"PKU101 {label} has no version: {path}")
    return match.group(1)


def validate_release(release: Path) -> str:
    version_path = release / "VERSION"
    if not version_path.is_file():
        raise UpgradeError(f"PKU101 release VERSION is missing: {version_path}")
    expected = version_path.read_text(encoding="utf-8").strip()
    if not expected:
        raise UpgradeError("PKU101 release VERSION is empty")
    versions = {
        label: manifest_version(release / relative, label)
        for label, relative in COMPONENTS
    }
    mismatches = {label: version for label, version in versions.items() if version != expected}
    if mismatches:
        details = ", ".join(f"{label}={version}" for label, version in mismatches.items())
        raise UpgradeError(
            f"PKU102 release source is version-incoherent; VERSION={expected}, {details}"
        )
    return expected


def load_managed_profile(target: Path) -> tuple[str, str] | None:
    path = target / ".program-kit/managed.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UpgradeError(f"PKU103 cannot read managed baseline state {path}: {error}") from error
    web = value.get("webProfile")
    persistence = value.get("persistenceProfile")
    if web not in {"none", "bff-cookie", "spa-pkce"} or persistence not in {
        "none", "ef-postgresql", "ef-sqlserver", "ef-sqlite", "mixed", "custom",
    }:
        raise UpgradeError(
            "PKU103 existing managed baseline does not record supported web and persistence profiles"
        )
    return str(web), str(persistence)


def selected_integration(target: Path, requested: str) -> str:
    if requested != "auto":
        candidate = requested
    else:
        path = target / ".specify/integration.json"
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise UpgradeError(f"PKU104 cannot resolve integration from {path}: {error}") from error
        candidate = state.get("default_integration") or state.get("integration")
    if not isinstance(candidate, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", candidate):
        raise UpgradeError(f"PKU104 unsupported integration identity: {candidate!r}")
    return candidate


def phase_refresh_plan(target: Path, release: Path, deviations=None) -> dict:
    """Admit native refresh from recorded ownership, never from a directory convention."""
    from specify_cli.integrations import get_integration
    from specify_cli.integrations.manifest import IntegrationManifest
    state = read_destination_state(target / '.specify/integration.json', 'integration')
    default = state.get('default_integration') or state.get('integration')
    keys = state.get('installed_integrations', [default])
    if (not isinstance(keys, list) or not keys or default not in keys
            or any(not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', key) for key in keys)
            or len(keys) != len(set(keys))):
        raise UpgradeError('PKU134 native phase refresh needs unambiguous installed integration ownership')
    flow = load_release_module(release / 'extensions/program-kit-governance/scripts/consumer_upgrade.py',
                               'upgrade_phase_ownership')
    rows = []
    for key in sorted(keys):
        if get_integration(key) is None:
            raise UpgradeError(f'PKU134 native phase refresh does not support installed integration {key}')
        path = target / '.specify/integrations' / (key + '.manifest.json')
        if not path.is_file():
            raise UpgradeError(f'PKU134 native phase refresh has no ownership manifest: {path}')
        try:
            manifest = IntegrationManifest.load(key, target)
        except (ValueError, OSError, KeyError, TypeError) as error:
            raise UpgradeError(f'PKU134 invalid native integration manifest {key}: {error}') from error
        if not manifest.files:
            raise UpgradeError(f'PKU134 native integration {key} has no owned phase outputs')
        inherited, hashes = [], {}
        for relative, expected in manifest.files.items():
            output = repository_relative_path(target, relative, key + ' phase output')
            observed = hashlib.sha256(output.read_bytes()).hexdigest() if output.is_file() else None
            hashes[relative] = observed
            preset = flow.preset_baseline(target, relative, key)
            # A recovered file was observed during install rather than produced.
            # Equality with its recorded hash alone cannot authorize replacement.
            recovered = manifest.is_recovered(relative)
            if recovered or (observed is not None and observed != expected.removeprefix('sha256:')):
                restored = restored_core_baseline(target, relative, key) if preset != observed else None
                if observed is None or (preset != observed and restored != observed):
                    raise UpgradeError(f'PKU134 consumer customization or unresolved native ownership: '
                                       f'{key} {relative}; preserve it and reconcile the owner before refresh')
                inherited.append(relative)
        rows.append({'integration': key, 'before': hashes, 'nativePresetOverrides': inherited})
    native = native_phase_ownership.preflight(target, release, sorted(keys), deviations=deviations)
    return {'schemaVersion': 1, 'defaultIntegration': default, 'integrations': rows,
            'nativePhaseOwnership': native}


def restored_core_baseline(target: Path, relative: str, integration: str) -> str | None:
    """Recognize native preset-removal rendering without trusting its installed cache.

    Spec Kit's core setup and preset-removal renderers have different skill
    headings. Both are maintained producers. Re-render the removal form from
    bundled core into a disposable view to recognize historical native restores.
    """
    path = Path(relative)
    if path.name != 'SKILL.md' or not path.parent.name.startswith('speckit-'):
        return None
    try:
        from specify_cli.presets import PresetManager
        with tempfile.TemporaryDirectory(prefix='program-kit-core-ownership-') as name:
            view = Path(name)
            for source_name in ('init-options.json', 'integration.json'):
                source = repository_relative_path(target, '.specify/' + source_name, 'native core inputs')
                if source.is_file():
                    destination = view / '.specify' / source_name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(source.read_bytes())
            skills = view / 'skills'
            (skills / path.parent.name).mkdir(parents=True)
            (skills / path.parent.name / 'SKILL.md').write_text('Native restore target\n', encoding='utf-8')
            profile=load_release_module(Path(__file__).resolve().parents[1]/'extensions/program-kit-governance/scripts/render_profile.py',
                                        'upgrade_core_render_profile')
            with profile.rendering(target,relative) as generation:
                PresetManager(view)._unregister_skills_in_dir([path.parent.name], skills, integration,
                                                         restore_from_bundled_core=True)
            generated = skills / path.parent.name / 'SKILL.md'
            observed=hashlib.sha256(generated.read_bytes()).hexdigest() if generated.is_file() else None
            return observed if not generation or generation['sha256']==observed else None
    except (ImportError, AttributeError, ValueError, OSError, KeyError, TypeError):
        return None


def refresh_phase_integrations(target: Path, release: Path, specify: list[str], plan: dict,
                               directory: Path, number: int, total: int) -> int:
    """Native core setup and native extension/preset composition for every installed integration."""
    from specify_cli.integrations.manifest import IntegrationManifest
    flow = load_release_module(release / 'extensions/program-kit-governance/scripts/consumer_upgrade.py',
                               'upgrade_phase_ownership_after_components')
    results = []
    original = plan['defaultIntegration']
    try:
        for row in plan['integrations']:
            key = row['integration']
            manifest = IntegrationManifest.load(key, target)
            # Native preset registration may legitimately predate the core manifest
            # hash. Rebind only bytes recomposed from declared native preset inputs.
            # This does not authorize --force or recovered/user-authored outputs.
            changed = False
            for relative in manifest.check_modified():
                output = repository_relative_path(target, relative, key + ' phase output')
                expected = flow.preset_baseline(target, relative, key)
                observed = hashlib.sha256(output.read_bytes()).hexdigest() if output.is_file() else None
                restored = restored_core_baseline(target, relative, key) if expected != observed else None
                if observed is None or (expected != observed and restored != observed):
                    raise UpgradeError(f'PKU134 phase output changed during installation: {key} {relative}')
                manifest.record_existing(relative)
                changed = True
            if changed:
                manifest.save()
            run_step(specify + ['integration', 'upgrade', key], target,
                     'Refresh native phase machinery: ' + key, number, total, directory)
            number += 1
            # Core upgrades re-register only the active integration. Native use
            # composes every other integration without copying generated outputs.
            run_step(specify + ['integration', 'use', key], target,
                     'Compose installed phase contributions: ' + key, number, total, directory)
            number += 1
            refreshed = IntegrationManifest.load(key, target)
            files = {}
            for relative in refreshed.files:
                output = repository_relative_path(target, relative, key + ' refreshed phase output')
                if not output.is_file():
                    raise UpgradeError(f'PKU134 refreshed native phase output is missing: {key} {relative}')
                observed = hashlib.sha256(output.read_bytes()).hexdigest()
                expected = flow.preset_baseline(target, relative, key)
                if expected is not None and expected != observed:
                    raise UpgradeError(f'PKU134 native preset composition did not converge: {key} {relative}')
                files[relative] = observed
            if refreshed.check_modified():
                # Native use can register the same preset after the core upgrade;
                # reconcile only recomposed native preset bytes on that path too.
                for relative in refreshed.check_modified():
                    if flow.preset_baseline(target, relative, key) != files.get(relative):
                        raise UpgradeError(f'PKU134 native refresh hash mismatch: {key} {relative}')
                    refreshed.record_existing(relative)
                refreshed.save()
            results.append({'integration': key, 'outputs': files,
                            'version': refreshed.version, 'nativeRefresh': True})
    finally:
        if selected_integration(target, 'auto') != original:
            run_step(specify + ['integration', 'use', original], target,
                     'Restore selected integration: ' + original, number, total, directory)
            number += 1
    write_attempt(directory / 'phase-refresh.json', {**plan, 'results': results,
                  'defaultRestored': selected_integration(target, 'auto') == original})
    return number


def require_existing_bundle(target: Path) -> None:
    path = target / ".specify/bundle-records.json"
    try:
        records = json.loads(path.read_text(encoding="utf-8")).get("bundles")
    except (OSError, json.JSONDecodeError) as error:
        raise UpgradeError(f"PKU109 cannot read existing bundle records {path}: {error}") from error
    if not any(
        isinstance(record, dict) and record.get("bundle_id") == "program-kit"
        for record in records or []
    ):
        raise UpgradeError(
            "PKU109 target has no existing Program Kit bundle record; use Initialize-ProgramKit for a fresh install"
        )


def current_version(target: Path) -> str:
    manifest = target / ".specify/extensions/program-kit-governance/extension.yml"
    return manifest_version(manifest, "installed Program Kit Governance extension")


def load_release_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise UpgradeError(f'PKU101 missing release adapter: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Admission reads installed consumer adapters before destination permissions
    # are checked. Even a stale .pyc must remain unchanged during that inspection.
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def persistence_upgrade_preflight(target: Path, release: Path) -> dict:
    """Admission failures precede installation; new package pins are checked after sync."""
    relative = 'extensions/program-kit-dotnet/scripts/persistence_selection.py'
    module = load_release_module(release / relative, 'upgrade_persistence')
    selection = module.upgrade_scope(target, module.resolve(target, ''))
    problems = list(selection['blockers'])
    installed = target / '.specify/extensions/program-kit-dotnet'
    # Existing applied assignments must be coherent with the currently installed provider,
    # not with the candidate's possibly renewed package pins.
    if (installed / 'scripts/persistence_selection.py').is_file():
        previous = load_release_module(installed / 'scripts/persistence_selection.py', 'upgrade_previous_persistence')
        old = module.upgrade_scope(target, previous.resolve(target, ''))
        problems.extend(previous.coherence(target, old, installed / 'templates/dotnet/files', materialized=True))
    if problems:
        raise UpgradeError('PKU118 persistence upgrade admission failed before component mutation: '
                           + '; '.join(dict.fromkeys(problems)))
    return selection


def ensure_cli_runtime(command: list[str], release: Path) -> int | None:
    """Load ownership guards in the already-probed CLI environment before importing them."""
    if '--site-packages' in command and str(release / 'scripts/invoke_specify.py') in command:
        site = Path(command[command.index('--site-packages') + 1]).resolve()
        if not (site / 'specify_cli/__init__.py').is_file():
            raise UpgradeError(f'PKU119 Spec Kit bridge package is missing: {site}')
        sys.path.insert(0, str(site))
        return None
    environment = uv_windows_specify_environment(command)
    interpreter = environment[0] if environment else None
    if interpreter is None and len(command) == 1 and os.name != 'nt':
        try:
            first = Path(command[0]).read_text(encoding='utf-8').splitlines()[0]
            candidate = Path(first[2:]) if first.startswith('#!') else None
            if candidate and candidate.is_absolute() and candidate.is_file():
                interpreter = candidate
        except (OSError, UnicodeDecodeError, IndexError):
            pass
    if interpreter and interpreter.resolve() != Path(sys.executable).resolve():
        print(f'PKU119 updater ownership guards require the installed Spec Kit runtime: {interpreter}', flush=True)
        return subprocess.run([str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]],
                              env={**os.environ, 'PYTHONUTF8': '1'}, check=False).returncode
    if importlib.util.find_spec('specify_cli') is not None:
        return None
    raise UpgradeError('PKU119 the updater cannot import the installed Spec Kit ownership guards. '
                       'Run this command with the Python interpreter belonging to the installed Spec Kit CLI; '
                       'no component mutation started.')


def release_fingerprint(release: Path) -> str:
    digest = hashlib.sha256()
    # Match packaging's build/cache exclusions. Running validation must not
    # change the identity of the same shipped candidate via compiled outputs.
    excluded = {'__pycache__', 'bin', 'obj', 'node_modules', 'playwright-report', 'test-results', '.auth'}
    for directory in ('scripts', 'extensions', 'presets', 'workflows', 'releases'):
        for path in sorted((release / directory).rglob('*')):
            if (path.is_file() and not path.is_symlink()
                    and not excluded.intersection(path.relative_to(release).parts)
                    and path.suffix not in {'.pyc', '.pyo'}):
                digest.update(path.relative_to(release).as_posix().encode() + b'\0'
                              + hashlib.sha256(path.read_bytes()).digest())
    for name in ('VERSION', 'bundle.yml'):
        digest.update(name.encode() + b'\0' + hashlib.sha256((release / name).read_bytes()).digest())
    for name in ('README.md', 'LICENSE', 'THIRD-PARTY-NOTICES.md'):
        if (release / name).is_file():
            digest.update(name.encode() + b'\0' + hashlib.sha256((release / name).read_bytes()).digest())
    return digest.hexdigest()


def retry_windows_sharing_lock(operation):
    # Six attempts, at most 0.75s waiting. Never retry ACL/access-denied errors.
    for attempt in range(6):
        try:
            return operation()
        except OSError as error:
            if sys.platform != 'win32' or getattr(error, 'winerror', None) not in (32, 33) or attempt == 5:
                raise
            time.sleep(0.05 * (attempt + 1))


def write_attempt(path: Path, value: dict) -> None:
    # Use ordinary sibling creation to inherit workspace permissions, not protected temp ACLs.
    path.parent.mkdir(parents=True, exist_ok=True)
    sibling = path.with_name(path.name + '.' + uuid.uuid4().hex)
    failure = None
    try:
        with sibling.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        retry_windows_sharing_lock(lambda: sibling.replace(path))
    except BaseException as error:
        failure = error
        raise
    finally:
        try:
            retry_windows_sharing_lock(lambda: sibling.unlink(missing_ok=True))
        except OSError:
            if failure is None:
                raise
            # Leave temporary evidence if still locked; retain the original
            # replacement diagnostic rather than masking it in cleanup.


def prior_attempt(target: Path, release: Path, version: str, repair_of: str | None = None):
    decision = target / 'docs/architecture/bootstrap-decisions.json'
    authority_hash = hashlib.sha256(decision.read_bytes()).hexdigest() if decision.is_file() else None
    fingerprint = release_fingerprint(release)
    directory = target / 'artifacts/program-kit/runs'
    previous = []
    attempts = []
    for path in attempt_paths(target):
        value = json.loads(path.read_text(encoding='utf-8'))
        if value.get('schemaVersion') == 1 and value.get('targetVersion') == version:
            attempts.append((path, value))
        if (value.get('schemaVersion') == 1 and value.get('targetVersion') == version
                and value.get('releaseInputsSha256') == fingerprint
                and value.get('status') in {'running', 'incomplete'}):
            previous.append((path, value))
    latest = max(attempts, key=lambda item: item[1]['startedAt']) if attempts else None
    completed = [value['startedAt'] for _, value in attempts if value.get('status') == 'completed']
    if completed:
        # Failed attempts remain immutable history. Once a later real attempt
        # completes, a new operation must not resume an older failed mutation or
        # inherit that operation's local-repair arguments/original input set.
        boundary = max(completed)
        previous = [item for item in previous if item[1]['startedAt'] > boundary]
    repaired_prior = None
    if latest and latest[1].get('status') in {'running', 'incomplete'} and (
            latest[1].get('releaseInputsSha256') != fingerprint):
        if repair_of != latest[1].get('releaseInputsSha256'):
            raise UpgradeError('PKU121 interrupted upgrade candidate or approved inputs changed; '
                               'preserve the failed attempt and restore its exact reviewed inputs before retrying. '
                               'An explicitly authorized repair can name its exact prior fingerprint with '
                               '--repair-of-release-sha256; original migration provenance is still required.')
        repaired_prior = latest
        previous.append(latest)
    elif repair_of and not any(item[1].get('releaseInputsSha256') == repair_of for item in attempts):
        raise UpgradeError('PKU121 candidate repair fingerprint has no matching preserved attempt')
    prior = repaired_prior or (max(previous, key=lambda item: item[1]['startedAt']) if previous else None)
    if len({item[1]['previousInstalledVersion'] for item in previous}) > 1:
        raise UpgradeError('PKU121 interrupted upgrade contains contradictory original version authority')
    if prior:
        if not prior[1].get('originals'):
            raise UpgradeError('PKU121 interrupted upgrade lacks verified original inputs; preserve evidence and repair recovery before retrying')
        for record in prior[1]['originals'].values():
            path = (target / record['path']).resolve()
            if not path.is_relative_to(target) or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
                raise UpgradeError('PKU121 original upgrade evidence is missing or changed')
        original_version = target / prior[1]['originals']['version']['path']
        if manifest_version(original_version, 'original governance extension') != prior[1]['previousInstalledVersion']:
            raise UpgradeError('PKU121 retry version contradicts archived governance provenance')
    return prior, fingerprint, authority_hash


def previous_installed_version(target: Path, release: Path, version: str, repair_of: str | None = None) -> str:
    prior, _, _ = prior_attempt(target, release, version, repair_of)
    return prior[1]['previousInstalledVersion'] if prior else current_version(target)


def begin_attempt(target: Path, release: Path, version: str, observed: str, repair_of: str | None = None) -> tuple[Path, dict]:
    prior, fingerprint, authority_hash = prior_attempt(target, release, version, repair_of)
    directory = target / 'artifacts/program-kit/runs' / uuid.uuid4().hex
    value = {'schemaVersion': 1, 'id': uuid.uuid4().hex, 'targetVersion': version,
             'observedInstalledVersion': observed,
             'previousInstalledVersion': prior[1]['previousInstalledVersion'] if prior else observed,
             'retryOf': prior[0].relative_to(target).as_posix() if prior else None,
             'releaseInputsSha256': fingerprint, 'bootstrapDecisionsSha256': authority_hash,
             'startedAt': datetime.now(timezone.utc).isoformat(), 'status': 'running',
             'authorization': 'explicit-local-upgrade-command', 'componentMutationStarted': False,
             'originalInputCapturePending': True}
    if prior:
        value['originals'] = prior[1]['originals']
        if prior[1].get('originalInputs'):
            value['originalInputs'] = prior[1]['originalInputs']
            value['originalInputCapturePending'] = False
        elif not (prior[1].get('originalInputCapturePending') is True and prior[1].get('componentMutationStarted') is False):
            value['originalInputCapturePending'] = False  # A legacy partial mutation cannot become a new original.
        if prior[1]['releaseInputsSha256'] != fingerprint:
            value['repairOfReleaseSha256'] = prior[1]['releaseInputsSha256']
    else:
        originals = {}
        selection_path = target / 'docs/architecture/building-block-selection.json'
        architecture_relative = 'docs/architecture/architecture-map.json'
        if selection_path.is_file():
            selected = json.loads(selection_path.read_text(encoding='utf-8'))
            reference = selected.get('authority', {}).get('architectureMap')
            if reference:
                architecture_relative = repository_relative_path(target, reference, 'selection architecture authority').relative_to(target).as_posix()
        for name, relative in {
            'version': '.specify/extensions/program-kit-governance/extension.yml',
            'catalog': '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json',
            'selection': 'docs/architecture/building-block-selection.json',
            'architecture': architecture_relative,
            'lock': 'eng/building-blocks.lock.json',
            'migration': migration_record_path(target).relative_to(target).as_posix(),
        }.items():
            source = target / relative
            if source.is_file():
                destination = target / '.program-kit/installation/originals' / (hashlib.sha256(source.read_bytes()).hexdigest() + '.original')
                destination.parent.mkdir(parents=True, exist_ok=True)
                payload = source.read_bytes()
                if destination.exists() and destination.read_bytes() != payload:
                    raise UpgradeError('PKU121 archived original changed; preserve it and inspect recovery provenance')
                if not destination.exists():
                    destination.write_bytes(payload)
                originals[name] = {'path': destination.relative_to(target).as_posix(),
                                   'sha256': hashlib.sha256(payload).hexdigest()}
        if 'version' not in originals:
            raise UpgradeError('PKU121 installed version provenance is missing')
        value['originals'] = originals
    path = directory / 'upgrade-attempt.json'
    seal_attempt(path, value)
    return path, value


def reuse_completed_preset_removal(target, release, attempt, number, total, directory):
    """An absent preset is reusable only after the exact interrupted native removal."""
    identity = 'program-kit-governance-preset'
    registry = read_destination_state(target / '.specify/presets/.registry', 'native preset retry')
    if not isinstance(registry.get('presets'), dict):
        raise UpgradeError('PKU148 malformed native preset registry; preserve it before retry')
    if identity in registry.get('presets', {}):
        return False
    if not attempt.get('retryOf'):
        return False  # Ordinary native removal owns unknown initial absence.
    installed = repository_relative_path(target, '.specify/presets/' + identity, 'native preset retry')
    if installed.exists():
        raise UpgradeError('PKU148 absent preset registration still has source bytes; preserve and reconcile before retry')
    witness = load_release_module(release / 'extensions/program-kit-governance/scripts/tooling_witness.py', 'upgrade_removed_preset_originals')
    original = witness.verify_attempt_inputs(target, attempt.get('originalInputs'), attempt['originals'])
    manifest = '.specify/presets/' + identity + '/preset.yml'
    if original['files'].get(manifest) is None or original['files'].get('.specify/presets/.registry') is None:
        raise UpgradeError('PKU148 retry lacks its exact original installed preset inventory; never backfill from absent current state')
    prior = attempt['retryOf']; seen = set(); proof = None
    while prior and len(seen) < 128:
        if prior in seen:
            raise UpgradeError('PKU148 cyclic preset-removal retry history')
        seen.add(prior); path = repository_relative_path(target, prior, 'preset-removal attempt')
        value = read_destination_state(path, 'preset-removal attempt')
        if (value.get('status') not in {'running', 'incomplete'}
                or value.get('targetVersion') != attempt['targetVersion'] or value.get('originalInputs') != attempt['originalInputs']
                or value.get('originals') != attempt['originals']):
            raise UpgradeError('PKU148 preset-removal retry differs from its canonical original attempt')
        for step in sorted(path.parent.glob('*-step.json')):
            record = read_destination_state(step, 'native removal step')
            if record.get('step') == 'Remove prior governance preset' and record.get('exitCode') == 0:
                proof = {'path': step.relative_to(target).as_posix(),
                         'sha256': hashlib.sha256(step.read_bytes()).hexdigest()}; break
        if proof: break
        prior = value.get('retryOf')
    if proof is None:
        raise UpgradeError('PKU148 absent preset has no preserved successful native removal in this original attempt chain')
    print(f'[{number}/{total}] Remove prior governance preset: verified prior successful removal; no second native removal executed', flush=True)
    write_attempt(directory / f'{number:02d}-step.json', {'step': 'Remove prior governance preset',
        'mode': 'verified-prior-removal', 'exitCode': None, 'priorSuccessfulStep': proof,
        'originalInputs': attempt['originalInputs'], 'actualSourceAbsent': True})
    return True


def run_step(command: list[str], target: Path, label: str, number: int, total: int, directory: Path | None = None) -> None:
    print(f"[{number}/{total}] {label}", flush=True)
    started = time.perf_counter()
    result = subprocess.run(command, cwd=target, check=False, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=900)
    if directory:
        directory.mkdir(parents=True,exist_ok=True)
        (directory / f'{number:02d}-stdout.log').write_text(result.stdout, encoding='utf-8')
        (directory / f'{number:02d}-stderr.log').write_text(result.stderr, encoding='utf-8')
        write_attempt(directory / f'{number:02d}-step.json', {'step':label, 'exitCode':result.returncode,
            'elapsedSeconds':round(time.perf_counter()-started,3)})
    print(result.stdout, end='')
    print(result.stderr, end='', file=sys.stderr)
    if result.returncode != 0:
        raise UpgradeError(f"PKU105 {label} failed with exit code {result.returncode}; "
                           "partial tooling installation needs the same command retried after this diagnostic is fixed")


def resolve_specify_command(single: str, vector_json: str) -> list[str]:
    if vector_json:
        try:
            vector = json.loads(vector_json)
        except json.JSONDecodeError as error:
            raise UpgradeError(f"PKU108 --specify-command-json is not valid JSON: {error}") from error
        if (
            not isinstance(vector, list)
            or not vector
            or any(not isinstance(item, str) or not item for item in vector)
        ):
            raise UpgradeError("PKU108 --specify-command-json must be a non-empty JSON string array")
        command = list(vector)
    else:
        command = [single]
    executable = shutil.which(command[0])
    if executable is None:
        candidate = Path(command[0])
        executable = str(candidate.resolve()) if candidate.is_file() else None
    if not executable:
        raise UpgradeError(f"PKU108 Spec Kit CLI is unavailable: {command[0]}")
    command[0] = executable
    return command


def run_specify_probe(
    command: list[str], arguments: list[str], target: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command + arguments,
        cwd=target,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


def uv_windows_specify_environment(command: list[str]) -> tuple[Path, Path] | None:
    if os.name != "nt" or len(command) != 1:
        return None
    launcher = Path(command[0])
    if launcher.suffix.lower() != ".exe" or not launcher.is_file():
        return None
    try:
        payload = launcher.read_bytes()
        marker = payload.rfind(b"#!")
        if marker < 0:
            return None
        shebang = payload[marker + 2 :].splitlines()[0].decode("utf-8").strip().strip('"')
        interpreter = Path(shebang)
        environment = interpreter.parent.parent
        configuration = (environment / "pyvenv.cfg").read_text(encoding="utf-8")
        site_packages = environment / "Lib/site-packages"
    except (OSError, UnicodeDecodeError, IndexError):
        return None
    if (
        not interpreter.is_absolute()
        or not interpreter.is_file()
        or not re.search(r"(?m)^uv\s*=\s*\S+\s*$", configuration)
        or not (site_packages / "specify_cli/__init__.py").is_file()
        or b"from specify_cli import main" not in payload[marker:]
    ):
        return None
    return interpreter.resolve(), site_packages.resolve()


def powershell_retry_command() -> str:
    def literal(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    return "& " + " ".join(literal(item) for item in [sys.executable, *sys.argv])


def preflight_specify(command: list[str], target: Path, release: Path) -> list[str]:
    failure: BaseException | subprocess.CompletedProcess[str]
    try:
        result = run_specify_probe(command, ["--version"], target)
        if result.returncode == 0:
            # Observe future actual generation even when the native launcher is
            # healthy. Historical inputs are never inferred from this probe.
            bridge=release/'scripts/invoke_specify.py'
            if len(command)==1 and bridge.is_file():
                adapter=load_release_module(bridge,'upgrade_native_launcher_capture')
                try:site=adapter.launcher_site_packages(Path(command[0]))
                except (OSError,ValueError):pass  # Custom vectors keep their explicit owner; no fabricated provenance.
                else:return [sys.executable,str(bridge),'--site-packages',str(site),'--']
            return command
        failure = result
    except (OSError, subprocess.TimeoutExpired) as error:
        failure = error

    uv_environment = uv_windows_specify_environment(command)
    bridge = release / "scripts/invoke_specify.py"
    if uv_environment and bridge.is_file():
        interpreter, site_packages = uv_environment
        fallback = [
            sys.executable,
            str(bridge.resolve()),
            "--site-packages",
            str(site_packages),
            "--",
        ]
        probes = (
            ["--version"],
            ["bundle", "install", "--help"],
            ["workflow", "add", "--help"],
            ["extension", "add", "--help"],
            ["preset", "remove", "--help"],
            ["preset", "add", "--help"],
        )
        try:
            probe_results = [run_specify_probe(fallback, probe, target) for probe in probes]
        except (OSError, subprocess.TimeoutExpired) as error:
            fallback_failure = str(error)
        else:
            rejected = next((item for item in probe_results if item.returncode != 0), None)
            if rejected is None:
                print(
                    "PKU114 uv-installed Spec Kit launcher cannot execute its managed Python in this "
                    f"context; using the release-owned bridge with the same environment: {site_packages}"
                )
                return fallback
            lines = (rejected.stderr or rejected.stdout).strip().splitlines()
            fallback_failure = lines[-1] if lines else f"exit {rejected.returncode}"
        raise UpgradeError(
            "PKU114 uv-installed Spec Kit launcher crosses an execution boundary that the current "
            f"Windows context cannot use (launcher={command[0]}, interpreter={interpreter}). The "
            f"release-owned bridge also failed before mutation: {fallback_failure}. Rerun from a "
            "normal user-owned PowerShell terminal with: "
            + powershell_retry_command()
        )

    if isinstance(failure, subprocess.CompletedProcess):
        lines = (failure.stderr or failure.stdout).strip().splitlines()
        suffix = f" Detail: {lines[-1]}" if lines else ""
        failure_description = f"exit {failure.returncode}"
    else:
        suffix = f" Detail: {failure}"
        failure_description = "an execution error"
    raise UpgradeError(
        "PKU112 Spec Kit CLI cannot execute before mutation "
        f"({failure_description}). Run the updater from a context that can execute the installed "
        "CLI, or pass an explicitly reviewed command vector with --specify-command-json."
        + suffix
    )


def repository_relative_path(target: Path, value: str, label: str) -> Path:
    """Resolve an installer-owned relative path without permitting an escape."""
    relative = Path(value.replace("\\", "/"))
    if not value or relative.is_absolute() or ".." in relative.parts:
        raise UpgradeError(f"PKU115 unsafe {label} destination: {value!r}")
    lexical = target
    for part in relative.parts:
        lexical = lexical / part
        if lexical.is_symlink() or getattr(lexical, 'is_junction', lambda: False)():
            raise UpgradeError(f"PKU115 linked {label} destination must be reconciled before mutation: {value!r}")
    path = (target / relative).resolve()
    try:
        path.relative_to(target)
    except ValueError as error:
        raise UpgradeError(f"PKU115 {label} destination escapes the repository: {value!r}") from error
    return path


def read_destination_state(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UpgradeError(f"PKU115 cannot inspect {label} destination state {path}: {error}") from error
    if not isinstance(value, dict):
        raise UpgradeError(f"PKU115 {label} destination state is not an object: {path}")
    return value


def common_destination_root(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    common = paths[0].parent
    for path in paths[1:]:
        candidate = path.parent
        while common != candidate and common not in candidate.parents:
            if common == common.parent:
                return None
            common = common.parent
    return common


def managed_mutation_destinations(
    target: Path,
    release: Path,
    integration: str,
    profile: tuple[str, str] | None,
    has_bootstrap_decisions: bool,
    reconciliation: dict | None,
    stale_locks: list[Path],
    exporter_transition: dict | None = None,
) -> tuple[dict[Path, set[str]], set[Path]]:
    """Return all known component roots and existing files touched by an upgrade.

    Spec Kit records the exact files owned by each installed integration. Those
    manifests are the durable source for agent-specific locations; this avoids
    encoding Codex's ``.agents`` layout (or any other integration layout) in the
    Program Kit updater.
    """
    roots: dict[Path, set[str]] = {}
    existing_files: set[Path] = set()

    def add_root(path: Path, reason: str) -> None:
        roots.setdefault(path, set()).add(reason)

    for relative, reason in (
        (".specify", "upgrade lock and Spec Kit registries"),
        (".specify/extensions", "extension installation"),
        (".specify/workflows", "workflow installation"),
        (".specify/presets", "preset installation"),
        (".program-kit/sync", "shared repository setup context and receipts"),
        (".specify/governance", "upgrade history and verified migration completion"),
    ):
        add_root(target / relative, reason)

    integration_state_path = target / ".specify/integration.json"
    integration_state = read_destination_state(integration_state_path, "integration")
    agent_ids = {integration}
    installed = integration_state.get("installed_integrations", [])
    if isinstance(installed, list):
        agent_ids.update(item for item in installed if isinstance(item, str))

    for registry_relative, kind in (
        (".specify/extensions/.registry", "extension"),
        (".specify/presets/.registry", "preset"),
    ):
        registry_path = target / registry_relative
        if not registry_path.is_file():
            continue
        registry = read_destination_state(registry_path, kind)
        records = registry.get(kind + "s", {})
        if not isinstance(records, dict):
            raise UpgradeError(f"PKU115 {kind} destination registry is malformed: {registry_path}")
        for record in records.values():
            commands = record.get("registered_commands", {}) if isinstance(record, dict) else {}
            if isinstance(commands, dict):
                agent_ids.update(item for item in commands if isinstance(item, str))

    for agent_id in sorted(agent_ids):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", agent_id):
            raise UpgradeError(f"PKU115 unsafe installed integration identity: {agent_id!r}")
        manifest_path = target / ".specify/integrations" / f"{agent_id}.manifest.json"
        if not manifest_path.is_file():
            raise UpgradeError(
                f"PKU115 cannot determine the managed destination for integration {agent_id!r}; "
                f"its installation manifest is missing: {manifest_path}"
            )
        manifest = read_destination_state(manifest_path, f"{agent_id} integration")
        files = manifest.get("files")
        if not isinstance(files, dict) or not files:
            raise UpgradeError(
                f"PKU115 integration {agent_id!r} has no managed file destinations in {manifest_path}"
            )
        paths = [
            repository_relative_path(target, value, f"{agent_id} integration")
            for value in files
            if isinstance(value, str)
        ]
        if len(paths) != len(files):
            raise UpgradeError(f"PKU115 integration {agent_id!r} has malformed file destinations")
        command_paths = [
            path
            for path in paths
            if any(part.casefold().startswith("speckit") for part in path.relative_to(target).parts)
        ]
        root = common_destination_root(command_paths or paths)
        if root is None:
            raise UpgradeError(f"PKU115 cannot determine a common destination for integration {agent_id!r}")
        add_root(root, f"{agent_id} integration command registration")
        if root.is_dir():
            for path in root.rglob("*"):
                if not (path.is_file() or path.is_symlink()):
                    continue
                if any(
                    part.startswith("speckit-program-kit-")
                    or part.startswith("speckit.program-kit.")
                    for part in path.relative_to(root).parts
                ):
                    existing_files.add(path)

    if profile:
        managed_path = target / ".program-kit/managed.json"
        managed = read_destination_state(managed_path, "managed profile")
        files = managed.get("files")
        if not isinstance(files, dict):
            raise UpgradeError(f"PKU115 managed profile has no file destination map: {managed_path}")
        add_root(target / ".program-kit", "managed profile state")
        for value, record in files.items():
            if not isinstance(value, str):
                raise UpgradeError(f"PKU115 managed profile has a malformed file destination: {value!r}")
            path = repository_relative_path(target, value, "managed profile")
            add_root(path.parent, "managed profile synchronization")
            if (
                isinstance(record, dict)
                and record.get("ownership") == "managed"
                and (path.is_file() or path.is_symlink())
            ):
                existing_files.add(path)

        web, _ = profile
        desired_manifests = [
            release / "extensions/program-kit-dotnet/templates/dotnet/managed-files.json"
        ]
        if web != "none":
            desired_manifests.append(
                release
                / "extensions/program-kit-dotnet/templates/dotnet/web-profiles"
                / web
                / "managed-files.json"
            )
        for manifest_path in desired_manifests:
            manifest = read_destination_state(manifest_path, "release managed profile")
            entries = manifest.get("files")
            obsolete = manifest.get("obsoleteFiles", [])
            if not isinstance(entries, list) or not isinstance(obsolete, list):
                raise UpgradeError(f"PKU115 release managed profile manifest is malformed: {manifest_path}")
            desired_entries = [entry for entry in entries if isinstance(entry, dict)]
            desired = [entry.get("path") for entry in desired_entries] + obsolete
            if len(desired) != len(entries) + len(obsolete) or any(
                not isinstance(value, str) for value in desired
            ):
                raise UpgradeError(f"PKU115 release managed profile destinations are malformed: {manifest_path}")
            managed_desired = {
                entry.get("path")
                for entry in desired_entries
                if entry.get("ownership") == "managed"
            } | set(obsolete)
            for value in desired:
                path = repository_relative_path(target, value, "release managed profile")
                add_root(path.parent, "managed profile synchronization")
                if value in managed_desired and (path.is_file() or path.is_symlink()):
                    existing_files.add(path)

    if has_bootstrap_decisions:
        add_root(target / ".specify/governance", "governed upgrade record")

    if stale_locks or (target / "artifacts/program-kit/dotnet-lock-renewal.json").exists():
        add_root(target / "artifacts/program-kit", "NuGet lock renewal evidence")

    if reconciliation:
        add_root(target / ".program-kit/selection-history", "preserved OpenAPI producer evidence")
        paths = [entry["path"] for entry in reconciliation["contracts"]]
        paths.extend(reconciliation["planningPaths"])
        for feature_dir in reconciliation["featureDirs"]:
            state_path = target / ".program-kit/lifecycle" / f"{feature_identity(feature_dir)}.json"
            if state_path.is_file():
                paths.append(state_path)
        for path in paths:
            add_root(path.parent, "OpenAPI producer-pin reconciliation")
            if path.is_file() or path.is_symlink():
                existing_files.add(path)

    if exporter_transition:
        add_root(exporter_transition["archive"], "preserved exporter catalog authority")
        for name in ("selection.json", "architecture.json"):
            path = exporter_transition["paths"][name]
            add_root(path.parent, "exporter catalog transition")
            existing_files.add(path)

    if (target / 'docs/architecture/building-block-selection.json').is_file():
        add_root(target / '.program-kit/dependency-profiles', 'retained dependency profiles')
        profile = target / '.program-kit/dependency-profile.json'
        add_root(profile.parent, 'retained dependency profile binding')
        if profile.exists(): existing_files.add(profile)
    return roots, existing_files


def feature_identity(feature_dir: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "-", feature_dir.name)


def nearest_existing_directory(path: Path) -> Path:
    candidate = path if path.is_dir() else path.parent
    while not candidate.exists():
        if candidate == candidate.parent:
            raise OSError(f"no existing parent directory for {path}")
        candidate = candidate.parent
    if not candidate.is_dir():
        raise OSError(f"destination parent is not a directory: {candidate}")
    return candidate


def probe_mutation_directory(path: Path) -> None:
    directory = nearest_existing_directory(path)
    nonce = uuid.uuid4().hex
    first = directory / f".program-kit-write-probe-{nonce}.tmp"
    second = directory / f".program-kit-write-probe-{nonce}.renamed.tmp"
    descriptor: int | None = None
    try:
        descriptor = os.open(first, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(descriptor, b"Program Kit destination capability probe\n")
        os.close(descriptor)
        descriptor = None
        os.replace(first, second)
        second.unlink()
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for sentinel in (first, second):
            try:
                sentinel.unlink()
            except FileNotFoundError:
                pass


def preflight_mutation_destinations(
    target: Path,
    release: Path,
    integration: str,
    profile: tuple[str, str] | None,
    has_bootstrap_decisions: bool,
    reconciliation: dict | None,
    stale_locks: list[Path],
    exporter_transition: dict | None = None,
) -> None:
    roots, existing_files = managed_mutation_destinations(
        target,
        release,
        integration,
        profile,
        has_bootstrap_decisions,
        reconciliation,
        stale_locks,
        exporter_transition,
    )
    try:
        for path in sorted(roots, key=lambda item: str(item).casefold()):
            probe_mutation_directory(path)
        for path in sorted(existing_files, key=lambda item: str(item).casefold()):
            if path.is_symlink():
                continue
            with path.open("r+b"):
                pass
    except OSError as error:
        blocked = path
        reason = ", ".join(sorted(roots.get(path, {"managed installer file replacement"})))
        raise UpgradeError(
            "PKU115 Program Kit cannot mutate every installer-owned destination in the current "
            f"execution context; no component mutation started. Blocked destination: {blocked} "
            f"({reason}; {error}). Rerun from a user-owned PowerShell outside this sandbox "
            "(elevate only if OS ACLs require it) with: "
            + powershell_retry_command()
        ) from error


def canonical_attempt_input_paths(target, release, phase_plan, mutation_arguments, profile):
    """One finite source of actual installer-owned originals, not directory counts."""
    _, files = managed_mutation_destinations(target, release, *mutation_arguments)
    names = {path.relative_to(target).as_posix() for path in files}
    names.update({'.specify/integration.json', '.specify/init-options.json', '.specify/extensions/.registry',
                  '.specify/presets/.registry', '.specify/workflows/workflow-registry.json', '.specify/bundle-records.json',
                  '.program-kit/managed.json', '.program-kit/dependency-profile.json',
                  '.program-kit/sync/context.json', '.program-kit/sync/receipt.json',
                  '.program-kit/sync/dependencies.json', '.program-kit/installation/migration.json',
                  'eng/building-blocks.lock.json', 'docs/architecture/building-block-selection.json'})
    for integration in phase_plan['integrations']:
        names.update(integration['before'])
        names.add('.specify/integrations/' + integration['integration'] + '.manifest.json')
    names.update(row['path'] for row in phase_plan['nativePhaseOwnership']['outputs'])
    # Include each actual target source file as an original presence/absence,
    # including additions absent from an older installed component.
    for relative in ('extensions/program-kit-governance', 'extensions/program-kit-building-blocks',
                     'extensions/program-kit-dotnet', 'presets/program-kit-governance-preset',
                     'workflows/program-kit-bootstrap'):
        source = release / relative
        for path in source.rglob('*') if source.is_dir() else []:
            if {'__pycache__', '.dev-cache', '.composed', 'bin', 'obj', 'node_modules'} & set(path.relative_to(source).parts): continue
            if path.is_file() and path.suffix not in {'.pyc', '.pyo'}:
                names.add('.specify/' + relative + '/' + path.relative_to(source).as_posix())
    for relative in ('.specify/extensions/program-kit-governance', '.specify/extensions/program-kit-building-blocks',
                     '.specify/extensions/program-kit-dotnet', '.specify/presets/program-kit-governance-preset',
                     '.specify/workflows/program-kit-bootstrap', '.specify/program-kit/render-profiles',
                     '.specify/governance', '.program-kit/sync', '.program-kit/dependency-profiles'):
        directory = repository_relative_path(target, relative, 'canonical original source')
        for path in directory.rglob('*') if directory.is_dir() else []:
            if {'__pycache__', '.dev-cache', '.composed', 'bin', 'obj', 'node_modules'} & set(path.relative_to(directory).parts): continue
            if path.is_file() and path.suffix not in {'.pyc', '.pyo'}:
                names.add(path.relative_to(target).as_posix())
    if profile:
        manifests = [release / 'extensions/program-kit-dotnet/templates/dotnet/managed-files.json']
        if profile[0] != 'none': manifests.append(release / 'extensions/program-kit-dotnet/templates/dotnet/web-profiles' / profile[0] / 'managed-files.json')
        for manifest in manifests:
            value = read_destination_state(manifest, 'canonical original managed destinations')
            names.update(entry['path'] for entry in value['files'])
            names.update(value.get('obsoleteFiles', []))
    for name in names: repository_relative_path(target, name, 'canonical original input')
    return sorted(names)


def building_block_versions(release: Path, target: Path) -> dict[str, str]:
    path = release / "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json"
    try:
        renderer = load_release_module(release / 'extensions/program-kit-dotnet/scripts/dependency_profile.py', 'upgrade_dependency_pin_renderer')
        selected = renderer.retained_catalog(target)
        value = selected if selected is not None else json.loads(path.read_text(encoding="utf-8"))
        versions = {
            package["packageId"]: package["version"]
            for package in value["packages"].values()
            if package.get("ecosystem") == "nuget"
        }
        if selected is None:
            versions['Orbyss.Foundation.OpenApi.Exporter'] = target_exporter_version(release)
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise UpgradeError(f"PKU101 release building-block manifest is invalid: {path}: {error}") from error
    if not versions or any(not package.startswith("Orbyss.") or not version for package, version in versions.items()):
        raise UpgradeError("PKU101 release building-block package pins are empty or invalid")
    return versions


def software_update_offer() -> dict:
    """A read-only invitation; dependency adoption keeps its existing authority."""
    return {
        'optional': True,
        'choices': ['Keep current versions', 'Review qualified dependency profiles', 'Review all repository software'],
        'profileListCommand': 'python .specify/extensions/program-kit-building-blocks/scripts/dependency_profiles.py list',
        'reviewCommand': 'speckit.program-kit-governance.upgrade',
        'reviewRequest': 'Review repository software versions, including dependency profiles, packages, toolchains, CI actions and container images.',
        'nextAction': 'Compare current and proposed stable versions, compatibility, security and migration work; choose what to adopt before changing pins or native locks.',
        'networkLookupPerformed': False,
    }


def building_block_upgrade_state(target: Path, release: Path, exporter_transition: dict | None = None, repair_of: str | None = None,
                                 retry_context: UpgradeRetryContext | None = None) -> str | None:
    """Validate authority and distinguish an accepted plan from applied dependencies.

    A missing lock alone is never evidence of an unmaterialized selection. That
    state also requires complete planned placement, absent targets and outputs,
    and no pending transaction or unmanaged building-block dependency.
    """
    selection_path = target / "docs/architecture/building-block-selection.json"
    lock_path = target / "eng/building-blocks.lock.json"
    if not selection_path.is_file():
        if lock_path.exists():
            raise UpgradeError("PKU116 building-block lock exists without its selection; repair selection state before upgrading")
        return None
    catalog_path = release / "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json"
    resolver_path = release / "extensions/program-kit-building-blocks/scripts/building_blocks.py"
    spec = importlib.util.spec_from_file_location("program_kit_upgrade_building_blocks", resolver_path)
    if spec is None or spec.loader is None:
        raise UpgradeError(f"PKU101 cannot load release building-block resolver: {resolver_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if selection.get("status") != "Accepted":
        raise UpgradeError("PKU116 building-block selection must be Accepted before Program Kit upgrade")
    module.validate_selection(selection)
    accepted_hash = selection.get("catalog", {}).get("resolutionSha256")
    release_hash = module.catalog_resolution_sha256(catalog)
    if accepted_hash != release_hash:
        if exporter_transition is None:
            installed = target / '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
            try:
                catalog_path = module.consumer_catalog(target, selection, installed)
                retained = module.load_json(catalog_path)
                module.verify_catalog_binding(selection, retained)
            except module.ResolverError as error:
                raise UpgradeError('PKU116 retained accepted dependency profile is invalid: ' + str(error)) from error
        else:
            exporter_transition.update(catalog_transition(target, release, module, selection))
            exporter_transition["resolver"] = module
            catalog_path = exporter_transition["oldCatalog"]
        catalog = module.load_json(catalog_path)
    try:
        desired = module.resolve(target, selection_path, catalog_path, (release / "VERSION").read_text().strip())
        transactions = module.transaction_root(target)
        if transactions.exists() and (not transactions.is_dir() or any(transactions.iterdir())):
            raise UpgradeError("PKU116 unfinished building-block transaction; run supported building-block recovery before upgrading")
        if lock_path.exists():
            # Verify the old applied state before installation can replace any of
            # its inputs. Only generator/catalog provenance may change afterward.
            installed_catalog = (exporter_transition["oldCatalog"] if exporter_transition else catalog_path)
            previous_version = (exporter_transition['previousInstalledVersion'] if exporter_transition
                                else previous_installed_version(target, release, (release / 'VERSION').read_text().strip(), repair_of))
            previous = module.resolve(target, selection_path, installed_catalog, previous_version)
            actual = module.load_json(lock_path)
            if actual.get("materializationScope") == "existing-compositions":
                previous = module.materialized_plan(target, previous)
            if actual != previous:
                target_state = module.materialized_plan(target, desired) if actual.get('materializationScope') == 'existing-compositions' else desired
                if (retry_context is None or retry_context.target_version != (release / 'VERSION').read_text().strip()
                        or current_version(target) != retry_context.target_version
                        or (actual != target_state and not retry_context.original_matches('lock', lock_path))):
                    raise UpgradeError("PKU116 generated building-block lock is stale or corrupt; repair materialized state before upgrading")
                if not retry_context.selection_matches(selection_path, release, module):
                    raise UpgradeError('PKU116 retry selection differs from the verified original or exact supported catalog transition; review a new upgrade plan')
                if not retry_context.architecture_matches(selection_path, module):
                    raise UpgradeError('PKU116 retry architecture authority changed outside the supported selection registration; review a new upgrade plan')
            if hasattr(module, 'effective_dependency_context'):
                module.check_materialization(target, actual, catalog_path=installed_catalog)
            else:
                module.check_materialization(target, actual)
            module.audit_unmanaged_dependencies(target, catalog, actual)
            return "materialized"
        module.validate_placements(target, selection, require_all=True)
        if any(item["placement"]["state"] != "planned" for item in selection["targets"]):
            raise UpgradeError("PKU116 missing building-block lock for observed placement; repair materialized state before upgrading")
        paths = {item["path"] for item in selection["targets"] + desired["managedOutputs"]}
        existing = sorted(path for path in paths if module.repository_path(target, path).exists())
        if existing:
            raise UpgradeError("PKU116 missing building-block lock with existing targets or managed outputs: " + ", ".join(existing))
        module.audit_unmanaged_dependencies(target, catalog, None)
        return "planned"
    except module.ResolverError as error:
        raise UpgradeError(f"PKU116 building-block upgrade preflight failed: {error}") from error


def resynchronize_building_block_provenance(target: Path) -> None:
    resolver = target / ".specify/extensions/program-kit-building-blocks/scripts/building_blocks.py"
    plan = subprocess.run(
        [sys.executable, str(resolver), "plan", "--target", str(target)],
        cwd=target,
        check=False,
        capture_output=True,
        text=True,
    )
    if plan.returncode != 0:
        raise UpgradeError(f"PKU116 building-block upgrade plan failed: {plan.stderr.strip()}")
    try:
        digest = json.loads(plan.stdout)["planDigest"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise UpgradeError("PKU116 building-block upgrade plan did not return a plan digest") from error
    apply = subprocess.run(
        [
            sys.executable,
            str(resolver),
            "apply",
            "--target",
            str(target),
            "--plan-digest",
            digest,
        ],
        cwd=target,
        check=False,
        capture_output=True,
        text=True,
    )
    if apply.returncode != 0:
        raise UpgradeError(f"PKU116 compatible building-block provenance update failed: {apply.stderr.strip()}")


def stale_program_kit_locks(target: Path, component_versions: dict[str, str], verifier=None) -> list[Path]:
    ignored = {".git", ".specify", "artifacts", "node_modules"}
    retired = set()
    archives = []
    if (target / 'eng/retained-inputs.json').is_file():
        reader = target / 'eng/retained_inputs.py'
        if not reader.is_file():
            raise UpgradeError('PKU113 retained ownership index requires the supported .NET reader; synchronize engineering before lock classification')
        observed = subprocess.run([sys.executable, '-E', '-s', str(reader), 'verify', '--repository', str(target)],
                                  cwd=target, capture_output=True, text=True, timeout=120)
        if observed.returncode != 0:
            raise UpgradeError('PKU113 original retained ownership/inactivity verification failed: ' + observed.stdout.strip() + observed.stderr.strip())
        ownership = json.loads(observed.stdout)
        retired = set(ownership.get('retiredLocks', {}))
        archives = [row['root'] for row in ownership.get('retainedArchives', [])]
    stale: list[Path] = []
    paths = set(target.rglob('packages.lock.json'))
    evaluated = {}
    if (target/'eng/restore-graph.json').is_file():
        if verifier is None:
            raise UpgradeError('PKU113 custom/evaluated native lock classification requires the selected release restore adapter')
        try:
            inventory = verifier.nuget_active_inventory(target, set())
            closure = verifier.nuget_restore_closure(target, inventory)
            for project, outputs in closure['outputs'].items():
                path = target/outputs['lock']
                paths.add(path)
                evaluated.setdefault(path, []).append(project)
        except (OSError, ValueError, RuntimeError) as error:
            raise UpgradeError('PKU113 native lock ownership failed: '+str(error)) from error
    for path in sorted(paths):
        relative = path.relative_to(target)
        if any(part in ignored for part in relative.parts) or relative.parts[:2] == (".program-kit", "cache"):
            continue
        if relative.as_posix() in retired:
            continue
        if any(relative.as_posix().startswith(archive + '/') for archive in archives):
            continue
        if not path.is_file():
            raise UpgradeError('PKU113 active native lock is missing; run its reviewed renew/locked restore: '+relative.as_posix())
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise UpgradeError(f"PKU113 cannot inspect NuGet lock file {path}: {error}") from error
        frameworks = value.get("dependencies", {})
        if not isinstance(frameworks, dict):
            continue
        entries = [
            (package_id, dependency)
            for dependencies in frameworks.values()
            if isinstance(dependencies, dict)
            for package_id, dependency in dependencies.items()
            if isinstance(package_id, str) and isinstance(dependency, dict)
        ]
        if any(
            package_id.startswith("ProgramKit.")
            or (
                package_id in component_versions
                and str(dependency.get("resolved", "")) != component_versions[package_id]
            )
            for package_id, dependency in entries
        ):
            owners = evaluated.get(path) or [owner for owner in path.parent.iterdir() if owner.is_file()
                      and owner.suffix.casefold() in {'.csproj', '.fsproj', '.vbproj'}]
            if not owners:
                raise UpgradeError('PKU113 unexplained stale NuGet lock has no active native owner or original authenticated retirement: '
                                   + relative.as_posix() + '; restore the current owner or declare original reset-bound ownership; absence is not retirement')
            stale.append(path)
    return sorted(stale)


def lock_renewal_commands(target: Path, locks: list[Path]) -> list[str]:
    coordinator = "python .specify/extensions/program-kit-governance/scripts/repository_sync.py"
    executor = "python .specify/extensions/program-kit-building-blocks/scripts/restore_dependencies.py"
    context = ".program-kit/sync/dependencies.json"
    request = "artifacts/program-kit/building-block-restore-request.json"
    return [
        f"{coordinator} request-renew --phase upgrade",
        f"{executor} renew --approved --lock {context} --request {request}",
        f"{coordinator} request-locked --phase upgrade",
        f"{executor} locked --approved --lock {context} --request {request}",
    ]


def write_lock_renewal(target: Path, component_versions: dict[str, str], locks: list[Path]) -> list[str]:
    commands = lock_renewal_commands(target, locks)
    path = target / "artifacts/program-kit/dotnet-lock-renewal.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "targetPackageVersions": dict(sorted(component_versions.items())),
                "affectedLocks": [item.relative_to(target).as_posix() for item in locks],
                "renewalCommands": commands,
                "reason": "orbyss-building-block-pin-upgrade",
                "satisfied": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return commands


def satisfy_lock_renewal(target: Path, component_versions: dict[str, str], pending: list[str], verifier) -> bool:
    path = target / "artifacts/program-kit/dotnet-lock-renewal.json"
    if not path.is_file():
        return not pending
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UpgradeError(f"PKU113 cannot verify NuGet lock renewal evidence {path}: {error}") from error
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise UpgradeError(f"PKU113 NuGet lock renewal evidence is malformed: {path}")
    pending = list(pending)
    # Previously affected native locks must belong to actual restored projects.
    # A hand-edited orphan lock is not executable dependency verification.
    if not pending and value.get('affectedLocks'):
        try:
            plan = json.loads((target / '.program-kit/sync/dependencies.json').read_text(encoding='utf-8'))
            evidence = json.loads((target / 'artifacts/program-kit/building-block-restore.json').read_text(encoding='utf-8'))
            verifier.verify_evidence(target, plan, evidence)
            project_locks = {outputs['lock'] for outputs in verifier.nuget_plan_closure(target, plan)['outputs'].values()}
            if not set(value['affectedLocks']) <= project_locks:
                raise ValueError('Affected NuGet lock has no restored project owner')
        except (OSError, ValueError, KeyError, RuntimeError) as error:
            pending.append('Renewal needs current shared restore proof for every affected native lock: ' + str(error))
    value["targetPackageVersions"] = dict(sorted(component_versions.items()))
    value.pop("targetRuntimeVersion", None)
    value["reason"] = "shared-dependency-verification-pending" if pending else "shared-dependencies-verified"
    value["satisfied"] = not pending
    value["pendingPackageVerification"] = pending
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return not pending


def acquire_lock(target: Path) -> tuple[int, Path]:
    legacy = target / '.specify/program-kit-upgrade.lock'
    if legacy.exists():
        raise UpgradeError('PKU106 legacy upgrade lock is present; establish that its old operation ended before removing it: ' + str(legacy))
    path = target / '.specify/program-kit-upgrade-v2.lock'
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b'1')
        os.lseek(descriptor, 0, os.SEEK_SET)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        os.close(descriptor)
        raise UpgradeError('PKU106 another upgrade is active; retry after it completes') from error
    return descriptor, path


def pending_upgrade_transactions(target: Path) -> bool:
    return any(any((target / relative).glob('*/journal.json'))
               for relative in ('.program-kit/transactions', '.program-kit/building-block-transactions'))


def recover_upgrade_transactions(target: Path, release: Path) -> list[str]:
    # Called only under the OS upgrade lock. Maintained recovery recipes preserve
    # externally edited application paths rather than overwriting them.
    for relative in ('.program-kit/transactions', '.program-kit/building-block-transactions'):
        path = target / relative
        if path.is_symlink() or not path.resolve().is_relative_to(target.resolve()):
            raise UpgradeError('PKU121 transaction path escapes the consumer; inspect ' + relative)
    engineering = load_release_module(release / 'extensions/program-kit-dotnet/scripts/reconciliation.py', 'upgrade_reconciliation')
    blocks = load_release_module(release / 'extensions/program-kit-building-blocks/scripts/building_blocks.py', 'upgrade_recovery_blocks')
    restored = engineering.recover_transactions(target) + blocks.recover_materialization(target)
    if restored:
        print('Recovered deterministic maintenance transactions: ' + ', '.join(restored))
    return restored


def completed_attempt_origin(target: Path, installed: str) -> str | None:
    origins = set()
    for path in attempt_paths(target):
        attempt = json.loads(path.read_text(encoding='utf-8'))
        if (attempt.get('status') != 'completed' or attempt.get('targetVersion') != installed
                or attempt.get('previousInstalledVersion') == installed):
            continue
        original = attempt.get('originals', {}).get('version')
        if (not isinstance(original, dict) or not isinstance(original.get('path'), str)
                or not isinstance(original.get('sha256'), str)):
            raise UpgradeError('PKU132 completed migration lacks archived version provenance')
        version_path = (target / original['path']).resolve()
        if (not version_path.is_relative_to(target.resolve()) or not version_path.is_file()
                or hashlib.sha256(version_path.read_bytes()).hexdigest() != original['sha256']
                or manifest_version(version_path, 'migration original governance extension') != attempt['previousInstalledVersion']):
            raise UpgradeError('PKU132 completed migration version provenance changed')
        origins.add(attempt['previousInstalledVersion'])
    if len(origins) > 1:
        raise UpgradeError('PKU132 completed migration has contradictory original versions')
    return next(iter(origins)) if origins else None


def migration_record_path(target: Path) -> Path:
    current = target / '.program-kit/installation/migration.json'
    return current if current.is_file() else target / '.specify/governance/migration-completion.json'


def preserve_migration_completion(target: Path, attempt_path: Path) -> None:
    # Prior results are immutable history in the owned execution run, never a new
    # approval input. Legacy history stays at its original location unchanged.
    source = migration_record_path(target)
    if source.is_file():
        (attempt_path.parent / 'previous-migration.json').write_bytes(source.read_bytes())


def attempt_paths(target: Path):
    return list((target / '.specify/governance/program-kit-upgrade-attempts').glob('*.json')) + list(
        (target / 'artifacts/program-kit/runs').glob('*/upgrade-attempt.json'))


def seal_attempt(path: Path, value: dict) -> None:
    write_attempt(path, value)
    marker = {'owner': 'program-kit', 'schemaVersion': 1, 'operation': 'upgrade',
              'status': 'failed' if value['status'] == 'incomplete' else value['status'],
              'startedAtUtc': value['startedAt'],
              'finishedAtUtc': datetime.now(timezone.utc).isoformat()}
    write_attempt(path.parent / 'run.json', marker)
    history = load_release_module(Path(__file__).resolve().parents[1] /
        'extensions/program-kit-governance/scripts/execution_history.py', 'upgrade_execution_history')
    history.cleanup(path.parents[4])


def migration_origin(target: Path, installed: str, fallback: str | None = None, target_version: str | None = None,
                     retry_context: UpgradeRetryContext | None = None) -> str:
    path = migration_record_path(target)
    if not path.is_file(): return fallback or installed
    record = json.loads(path.read_text(encoding='utf-8'))
    canonical = load_release_module(Path(__file__).resolve().parents[1] /
        'extensions/program-kit-governance/scripts/release_guidance.py', 'upgrade_canonical_completion')
    try:
        canonical.validate_completion(record)
    except ValueError as error:
        raise UpgradeError(str(error)) from error
    if record.get('status') not in {'pending', 'completed'}:
        raise UpgradeError('PKU132 migration provenance has unsupported status')
    plan = record.get('plan', {})
    digest = hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if (record.get('schemaVersion') != 1 or record.get('planSha256') != digest
            or plan.get('fromVersion') != record.get('fromVersion') or plan.get('toVersion') != record.get('toVersion')):
        raise UpgradeError('PKU132 migration provenance is missing or changed')
    prior_completed = (retry_context is not None and record['status'] == 'completed'
                       and installed == target_version == retry_context.target_version
                       and record['toVersion'] == retry_context.original_version
                       and retry_context.original_matches('migration', path))
    if record['toVersion'] != installed and not prior_completed:
        raise UpgradeError('PKU132 pending migration differs from installed version; review recovery provenance')
    if record['status'] == 'completed':
        required = sorted({check for entry in plan.get('migrations', []) for check in entry.get('verificationChecks', []) if check not in record.get('retiredChecks', [])})
        if (record.get('migrationCompletionEstablished') is not True or record.get('pendingChecks')
                or record.get('requiredChecks') != required
                or any(record.get('checks', {}).get(check) is not True for check in required)):
            raise UpgradeError('PKU132 completed migration lacks required verification provenance')
        if prior_completed:
            return retry_context.original_version
        if target_version is not None and target_version != installed:
            return fallback or installed
    if record['status'] == 'completed' and record['fromVersion'] == installed:
        # Older updater retries replaced the full migration with a same-version
        # no-op. Recover only from sealed original version evidence; the rebuilt
        # cumulative plan still must satisfy its existing review and every gate.
        return completed_attempt_origin(target, installed) or record['fromVersion']
    return record['fromVersion']


def migration_plan(release: Path, installed: str, version: str):
    module = load_release_module(release / 'extensions/program-kit-governance/scripts/release_guidance.py', 'upgrade_release_guidance')
    directory = release / 'extensions/program-kit-governance/references/release-guidance'
    if directory.is_dir():
        return module, module.plan(directory, installed, version)
    builder = load_release_module(release / 'scripts/build_release_guidance.py', 'upgrade_guidance_builder')
    with tempfile.TemporaryDirectory(prefix='program-kit-migration-plan-') as name:
        return module, module.plan(builder.build(release, Path(name), version), installed, version)


def main() -> int:
    configure_utf8()
    parser = argparse.ArgumentParser(
        description="Upgrade every Program Kit component sequentially from one local release."
    )
    parser.add_argument("--release-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--target", default=".")
    parser.add_argument("--integration", default="auto")
    parser.add_argument(
        "--accept-openapi-producer-pin-reconciliation",
        action="store_true",
        help="Explicitly update registered Program Kit exporter pins and invalidate affected analysis readiness.",
    )
    parser.add_argument('--offline', action='store_true', help='Install offline and report required dependency verification without network restores')
    parser.add_argument('--plan', action='store_true', help='Read verified migration guidance without mutation')
    parser.add_argument('--repair-of-release-sha256', help='Explicitly resume a corrected candidate from this exact preserved failed release fingerprint')
    parser.add_argument('--local-repairs', help='Exact consumer-relative reviewed local repair declaration; executes its current required cases before replacement')
    parser.add_argument('--local-repairs-sha256', help='Original reviewed SHA-256 of --local-repairs; both arguments are required together')
    parser.add_argument("--specify-command", default="specify", help=argparse.SUPPRESS)
    parser.add_argument("--specify-command-json", default="", help=argparse.SUPPRESS)
    args = parser.parse_args()
    descriptor: int | None = None
    lock_path: Path | None = None
    attempt_path: Path | None = None
    attempt: dict | None = None
    try:
        release = Path(args.release_root).resolve()
        target = Path(args.target).resolve()
        if bool(args.local_repairs) != bool(args.local_repairs_sha256):
            raise UpgradeError('PKU147 local repair reconciliation requires both the exact declaration and its original reviewed SHA-256')
        effective_root = os.environ.get('SPECIFY_INIT_DIR')
        if not args.plan and effective_root and Path(effective_root).resolve() != target:
            raise UpgradeError('PKU133 inherited SPECIFY_INIT_DIR targets another project; no mutation started. '
                               'Use consumer_upgrade_workspace.py, which binds this variable only in its intended child processes, '
                               'or explicitly scope the variable to the selected target in your own shell.')
        if release.is_relative_to(target):
            raise UpgradeError('PKU120 stage the verified release outside the consumer workspace before upgrading. '
                               'Release examples and templates must not enter consumer dependency audits. '
                               'No component mutation started.')
        version = validate_release(release)
        retry_context = upgrade_retry_context(target, release, version, args.repair_of_release_sha256)
        if args.plan:
            observed = previous_installed_version(target, release, version, args.repair_of_release_sha256)
            _, plan = migration_plan(release, migration_origin(target, current_version(target), observed, version, retry_context), version)
            plan['installationActions'] = ['install bundle/workflow/extensions/preset sequentially',
                'refresh every installed native integration and compose all registered phase contributions; preserve customizations',
                'synchronize engineering configuration transactionally', 'validate installation coherence',
                'restore and verify affected native dependencies' if not args.offline else 'report native dependency verification pending']
            if args.local_repairs:
                plan['phaseRefreshPlan'] = {'unresolved': 'Explicit local repair reconciliation requires fresh current-case execution during apply; preview supplies no tested-source admission.',
                    'declaration': args.local_repairs, 'declarationSha256': args.local_repairs_sha256}
            elif importlib.util.find_spec('specify_cli') is not None:
                plan['phaseRefreshPlan'] = phase_refresh_plan(target, release)
            else:
                plan['phaseRefreshPlan'] = {'unresolved': 'Native ownership preview requires the installed Spec Kit Python runtime; installation runs this admission before component writes.'}
            profile = load_managed_profile(target)
            if profile:
                result = subprocess.run([sys.executable, str(release / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                    '--target', str(target), '--profile-selected', '--web-profile', profile[0],
                    '--upgrade-existing', '--check', '--json'], cwd=target, capture_output=True, text=True, encoding='utf-8', timeout=90)
                if result.returncode not in (0,1,2) or not result.stdout.strip().startswith('{'):
                    raise UpgradeError('PKU116 cannot preview engineering migration: ' + result.stderr)
                plan['engineeringPlan'] = json.loads(result.stdout)
            plan['applicationChecksPerformed'] = False
            plan['releaseReadinessEstablished'] = False
            plan['optionalSoftwareReview'] = software_update_offer()
            print(json.dumps(plan, indent=2))
            return 0
        component_versions = building_block_versions(release, target)
        policy_source = release / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/device_toolchain.py'
        if policy_source.is_file():
            # Read-only before any consumer mutation. Keep historical releases and the
            # existing reviewed CLI bridge/ownership recovery paths intact.
            policy = load_release_module(policy_source, 'upgrade_device_policy')
            policy.contributor(target, python_only=True)
        if not (target / ".specify").is_dir():
            raise UpgradeError(f"PKU107 target is not an initialized Spec Kit project: {target}")
        require_existing_bundle(target)
        previous_version = previous_installed_version(target, release, version, args.repair_of_release_sha256)
        guidance, guidance_plan = migration_plan(release, migration_origin(target, current_version(target), previous_version, version, retry_context), version)
        guidance.require_review(target, guidance_plan)
        integration = selected_integration(target, args.integration)
        specify = resolve_specify_command(args.specify_command, args.specify_command_json)
        specify = preflight_specify(specify, target, release)
        delegated = ensure_cli_runtime(specify, release)
        if delegated is not None:
            return delegated
        deviations, local_repairs = None, None
        prior, _, _ = prior_attempt(target, release, version, args.repair_of_release_sha256)
        if args.local_repairs:
            original_inputs = None
            if prior and prior[1].get('localRepairs'):
                if (prior[1]['localRepairs'].get('declarationSha256') != args.local_repairs_sha256
                        or prior[1]['localRepairs'].get('declaration') != args.local_repairs):
                    raise UpgradeError('PKU147 retry must preserve its original reviewed local repair declaration')
                witness = load_release_module(release / 'extensions/program-kit-governance/scripts/tooling_witness.py', 'upgrade_original_repair_inputs')
                original_inputs = witness.verify_attempt_inputs(target, prior[1]['originalInputs'], prior[1]['originals'])
            deviations, local_repairs = native_phase_ownership.tested_deviations(
                target, release, args.local_repairs, args.local_repairs_sha256, original_inputs)
        elif prior and prior[1].get('localRepairs'):
            raise UpgradeError('PKU147 interrupted local repair reconciliation requires its original --local-repairs and --local-repairs-sha256 arguments')
        phase_plan = phase_refresh_plan(target, release, deviations)
        if pending_upgrade_transactions(target):
            descriptor, lock_path = acquire_lock(target)
            recover_upgrade_transactions(target, release)
        exporter_transition = {} if args.accept_openapi_producer_pin_reconciliation else None
        building_block_state = building_block_upgrade_state(target, release, exporter_transition, args.repair_of_release_sha256, retry_context)
        retained_exporter = None
        if building_block_state and not args.accept_openapi_producer_pin_reconciliation:
            blocks = load_release_module(release / 'extensions/program-kit-building-blocks/scripts/building_blocks.py', 'upgrade_profile_preflight')
            selection = blocks.load_json(target / 'docs/architecture/building-block-selection.json')
            installed = target / '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
            catalog = blocks.load_json(blocks.consumer_catalog(target, selection, installed))
            component_versions = {p['packageId']: p['version'] for p in catalog['packages'].values() if p['ecosystem'] == 'nuget'}
            retained_exporter = component_versions.get('Orbyss.Foundation.OpenApi.Exporter')
        persistence_upgrade_preflight(target, release)
        profile = load_managed_profile(target)
        has_bootstrap_decisions = False  # Completed bootstrap history is immutable; installation owns its version record.
        reconciliation = discover_openapi_reconciliation(target, release, retained_exporter)
        retired_sync_integration.preflight(target)
        native_lock_adapter = load_release_module(release/'extensions/program-kit-building-blocks/scripts/restore_dependencies.py', 'upgrade_native_lock_adapter') if (target/'eng/restore-graph.json').is_file() else None
        stale_locks = stale_program_kit_locks(target, component_versions, native_lock_adapter)
        preflight_mutation_destinations(
            target,
            release,
            integration,
            profile,
            has_bootstrap_decisions,
            reconciliation,
            stale_locks,
            exporter_transition,
        )
        if descriptor is None:
            descriptor, lock_path = acquire_lock(target)
        # Load the release-owned guard, never code from a possibly edited consumer copy.
        runtime_source = release / 'extensions/program-kit-governance/scripts/schema_runtime.py'
        runtime_spec = importlib.util.spec_from_file_location('upgrade_schema_runtime', runtime_source)
        runtime = importlib.util.module_from_spec(runtime_spec)
        runtime_spec.loader.exec_module(runtime)
        try:
            runtime.check_copy(target)
        except RuntimeError as error:
            raise UpgradeError(str(error)) from error
        if not (runtime.runtime_path(target) / '.ready').is_file():
            if args.offline:
                raise UpgradeError('SCHEMA_RUNTIME_MISSING: offline upgrade needs its dependency runtime prepared: '
                                   f'python "{runtime_source}" setup --project-root "{target}"; then retry the same command')
            runtime.setup(target)
        attempt_path, attempt = begin_attempt(target, release, version, previous_version, args.repair_of_release_sha256)
        witness = load_release_module(release / 'extensions/program-kit-governance/scripts/tooling_witness.py', 'upgrade_tooling_witness')
        attempt['toolingWitness'] = witness.retain(target, release, attempt['releaseInputsSha256'])
        if local_repairs is not None:
            attempt['localRepairs'] = local_repairs
        checked = {}
        if local_repairs is not None:
            executed = local_repairs['execution']
            checked = dict(executed['inputSha256'])
            checked.update(executed['moduleSourceSha256'])
            checked[local_repairs['declaration']] = local_repairs['declarationSha256']
            checked[local_repairs['contract']] = local_repairs['contractSha256']
            for relative, expected in checked.items():
                source = repository_relative_path(target, relative, 'executed local repair source')
                if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                    raise UpgradeError('PKU147 local repair execution inputs changed before original capture: ' + relative)
        if attempt.get('originalInputs'):
            witness.verify_attempt_inputs(target, attempt['originalInputs'], attempt['originals'])
        else:
            if not attempt['originalInputCapturePending']:
                raise UpgradeError('PKU146 legacy interrupted mutation lacks its original canonical input inventory; preserve its history and authenticate original inputs, never backfill from partial current state')
            inputs = canonical_attempt_input_paths(target, release, phase_plan,
                (integration, profile, has_bootstrap_decisions, reconciliation, stale_locks, exporter_transition), profile)
            inputs = sorted(set(inputs) | set(checked))
            attempt['originalInputs'] = witness.retain_attempt_inputs(target, inputs, attempt)
        attempt.update(originalInputCapturePending=False, componentMutationStarted=True)
        seal_attempt(attempt_path, attempt)
        previous_version = attempt['previousInstalledVersion']
        audit = load_release_module(release / 'extensions/program-kit-governance/scripts/dependency_audit.py', 'upgrade_historical_input_archive')
        audit.archive_toolkit_proof_inputs(target)
        if exporter_transition:
            archive_catalog_transition(exporter_transition)
        elif building_block_state:
            blocks = load_release_module(release / 'extensions/program-kit-building-blocks/scripts/building_blocks.py', 'upgrade_retained_profile')
            selection = blocks.load_json(target / 'docs/architecture/building-block-selection.json')
            installed = target / '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
            blocks.preserve_dependency_profile(target, selection, blocks.consumer_catalog(target, selection, installed))
        local_bundle=[sys.executable,str(release/'scripts/record_local_bundle.py')]
        if '--site-packages' in specify:
            local_bundle+=['--site-packages',specify[specify.index('--site-packages')+1]]
        else:
            environment=uv_windows_specify_environment(specify)
            if environment is not None: local_bundle[0]=str(environment[0])
        local_bundle+=['--release-root',str(release),'--target',str(target),'--integration',integration]
        steps = [
            (specify + ["workflow", "add", str(release / "workflows/program-kit-bootstrap"), "--dev"], "Install bootstrap workflow"),
            (specify + ["extension", "add", str(release / "extensions/program-kit-governance"), "--dev", "--force"], "Install governance extension"),
            (specify + ["extension", "add", str(release / "extensions/program-kit-building-blocks"), "--dev", "--force"], "Install building-block extension"),
            (specify + ["extension", "add", str(release / "extensions/program-kit-dotnet"), "--dev", "--force"], "Install .NET extension"),
            (specify + ["preset", "remove", "program-kit-governance-preset"], "Remove prior governance preset"),
            (specify + ["preset", "add", "--dev", str(release / "presets/program-kit-governance-preset")], "Install governance preset"),
            (local_bundle,"Resolve bundle composition record"),
        ]
        total = (
            len(steps)
            + 2 * len(phase_plan['integrations'])
            + (1 if len(phase_plan['integrations']) > 1 else 0)
            + 2
            + 1
            + (1 if has_bootstrap_decisions else 0)
            + (1 if reconciliation else 0)
        )
        # Seal the bundle only after actual core and contribution refresh.
        for number, (command, label) in enumerate(steps[:-1], 1):
            if label == 'Remove prior governance preset' and reuse_completed_preset_removal(
                    target, release, attempt, number, total, attempt_path.parent):
                continue
            run_step(command, target, label, number, total, attempt_path.parent)
        next_step = refresh_phase_integrations(target, release, specify, phase_plan,
                                              attempt_path.parent, len(steps), total)
        run_step(steps[-1][0], target, steps[-1][1], next_step, total, attempt_path.parent)
        next_step += 1
        runtime.record_copy(target)
        retired_sync_integration.verify_removed(target)
        if exporter_transition:
            apply_catalog_transition(target, release, exporter_transition, exporter_transition["resolver"], version)
        print(f"[{next_step}/{total}] Synchronize existing repository setup")
        sync_source = target / ".specify/extensions/program-kit-governance/scripts/repository_sync.py"
        sys.path.insert(0, str(sync_source.parent))
        try:
            sync_spec = importlib.util.spec_from_file_location("program_kit_upgrade_sync", sync_source)
            sync_module = importlib.util.module_from_spec(sync_spec)
            sys.modules[sync_spec.name] = sync_module
            sync_spec.loader.exec_module(sync_module)
            restore_verifier = sync_module.provider('program-kit-building-blocks/scripts/restore_dependencies.py')
            receipt = sync_module.upgrade(target)
            print(f"[{next_step + 1}/{total}] Verify offline repository convergence")
            report = sync_module.readiness(target, "upgrade")
            if not report["ready"]:
                raise UpgradeError("PKU116 repository setup did not converge: " + json.dumps(report))
            print(json.dumps(report, indent=2))
        finally:
            sys.path.remove(str(sync_source.parent))
        if building_block_state == "planned" and building_block_upgrade_state(target, release) != "planned":
            raise UpgradeError("PKU116 planned building-block state changed during upgrade")
        next_step += 2
        validator = target / ".specify/extensions/program-kit-governance/scripts/governance_state.py"
        run_step(
            [sys.executable, str(validator), "validate-installation"],
            target,
            "Validate cross-component version coherence",
            next_step,
            total,
            attempt_path.parent,
        )
        if has_bootstrap_decisions:
            run_step(
                [
                    sys.executable, str(validator), "record-upgrade",
                    "--previous-version", previous_version,
                    "--target-version", version,
                ],
                target,
                "Record accepted governed upgrade",
                next_step + 1,
                total,
            )
            next_step += 1
        renewal_required = False
        if reconciliation:
            print(f"[{next_step + 1}/{total}] Reconcile registered OpenAPI producer pins")
            changed = apply_openapi_reconciliation(target, reconciliation)
            print("atomically reconciled: " + ", ".join(changed))
            print('Exporter configuration updated. Current contract/build checks use the new producer; historical analysis stays historical.')
        if not args.offline and (stale_locks or report.get('pendingPackageVerification')):
            coordinator = target / '.specify/extensions/program-kit-governance/scripts/repository_sync.py'
            executor = target / '.specify/extensions/program-kit-building-blocks/scripts/restore_dependencies.py'
            sync_module.audit_toolchain(target, sync_module.context(target, 'upgrade', None)['toolchainPins'])
            for mode in ('renew', 'locked'):
                for command in ([sys.executable, str(coordinator), 'request-' + mode, '--phase', 'upgrade'],
                                [sys.executable, str(executor), mode, '--approved', '--lock', '.program-kit/sync/dependencies.json',
                                 '--request', 'artifacts/program-kit/building-block-restore-request.json']):
                    run_step(command, target, 'Verify native dependencies: ' + mode, 20 if mode == 'renew' else 21, 21, attempt_path.parent)
            stale_locks = stale_program_kit_locks(target, component_versions, restore_verifier)
            report = sync_module.readiness(target, 'upgrade', None)
        if stale_locks:
            commands = write_lock_renewal(target, component_versions, stale_locks)
            print(
                "PKU113 Orbyss building-block pins changed while consumer NuGet lock files still resolve "
                f"retired or older package identities: {', '.join(path.relative_to(target).as_posix() for path in stale_locks)}. "
                "No network restore was run implicitly. Renew and verify with: "
                + " ; then ".join(commands),
                file=sys.stderr,
            )
            renewal_required = True
        else:
            pending = report.get("pendingPackageVerification", [])
            if not satisfy_lock_renewal(target, component_versions, pending, restore_verifier):
                renewal_required = True
                print("PKU113 managed setup is coherent; dependency verification remains pending. "
                      + " ; then ".join(lock_renewal_commands(target, [])), file=sys.stderr)
        sys.path.insert(0, str(sync_source.parent))
        try:
            remediation_module = sync_module.provider('program-kit-governance/scripts/upgrade_remediation.py')
            remediation = remediation_module.assess(target, report.get('deferredPersistenceAdmissions', []))
        finally:
            sys.path.remove(str(sync_source.parent))
        print('Follow the verified migration plan and its selected method before continuing feature work. '
              'Application correctness and release readiness remain unestablished by this tooling upgrade.')
        migration = guidance.completion(guidance_plan, {
            'installation-coherence': True, 'dependency-verification': not renewal_required})
        migration['applicationReady'] = None
        migration['applicationChecksPerformed'] = False
        migration['releaseReadinessEstablished'] = False
        migration['releaseInputsSha256'] = release_fingerprint(release)
        migration['toolingWitness'] = attempt['toolingWitness']
        migration['originalInputs'] = attempt['originalInputs']
        migration['originals'] = attempt['originals']
        if attempt.get('localRepairs'):
            migration['localRepairs'] = attempt['localRepairs']
        preserve_migration_completion(target, attempt_path)
        write_attempt(target / '.program-kit/installation/migration.json', migration)
        if not migration['migrationCompletionEstablished']:
            print('PKU132 installation is coherent; migration verification remains pending: '
                  + ', '.join(migration['pendingChecks']) + '. Preserve migration-completion.json and renew the named evidence before retry.', file=sys.stderr)
            renewal_required = True
        offer = software_update_offer()
        print('Optional software update review: keep current versions, review qualified dependency profiles, '
              'or review all repository software (packages, toolchains, CI actions and container images).')
        print('List qualified profiles: ' + offer['profileListCommand'])
        print('To opt in, use ' + offer['reviewCommand'] + ' and request: "' + offer['reviewRequest'] + '"')
        print('Review current and proposed versions and required checks before choosing which updates to adopt.')
        if renewal_required:
            attempt.update(status='completed', outcome='offline-coherent-package-verification-pending')
            seal_attempt(attempt_path, attempt)
            return 3
        attempt.update(status='completed', outcome='offline-coherent')
        seal_attempt(attempt_path, attempt)
        print(
            f"Program Kit v{version} upgrade completed: workflow, extensions, preset, bundle record, "
            "managed baseline, and installation metadata are coherent."
        )
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        print('No component installation started; resolve the reported input/permission issue.' if attempt is None else
              'Tooling installation may be partial. Whether the migration introduced an application failure is unverified; application source and unfinished work remain available.', file=sys.stderr)
        recovery = [sys.executable, str(release / 'scripts/upgrade_program_kit.py'), '--release-root', str(release), '--target', str(target)]
        if args.repair_of_release_sha256:
            recovery.extend(['--repair-of-release-sha256', args.repair_of_release_sha256])
        if args.local_repairs:
            recovery.extend(['--local-repairs', args.local_repairs, '--local-repairs-sha256', args.local_repairs_sha256])
        if args.offline: recovery.append('--offline')
        if args.accept_openapi_producer_pin_reconciliation: recovery.append('--accept-openapi-producer-pin-reconciliation')
        print('Next action: fix the reported cause, then run ' + subprocess.list2cmdline(recovery), file=sys.stderr)
        if attempt is not None and attempt_path is not None:
            attempt.update(status='incomplete', diagnostic=str(error))
            try:
                seal_attempt(attempt_path, attempt)
            except OSError as evidence_error:
                print(f'PKU121 cannot seal attempt {attempt_path}: {evidence_error}; preserve the original diagnostic above.', file=sys.stderr)
            else:
                print(f'PKU121 upgrade attempt preserved at {attempt_path}; fix the reported cause and retry '
                      'the same verified release command. Installation success and upgrade authority remain separate.', file=sys.stderr)
        return 2
    finally:
        if descriptor is not None:
            os.close(descriptor)
        # OS locks release on close/process exit; the inert marker survives retries.



if __name__ == "__main__":
    raise SystemExit(main())
