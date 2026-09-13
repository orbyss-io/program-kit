"""Resolve data-owner intent and check adoption without mutating consumer data or source."""
from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from xml.etree import ElementTree as ET

PROFILES = {'ef-postgresql': 'EfPostgreSql', 'ef-sqlserver': 'EfSqlServer', 'ef-sqlite': 'EfSqlite'}
AGGREGATE = '.program-kit/eng/ProgramKit.Persistence.props'
ADMISSIONS = ('ownership', 'atomicity', 'concurrency', 'providerSemantics', 'migrations',
              'queries', 'authorization', 'dataProtection', 'operations', 'realProviderTests')


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def inside(root, relative):
    if not isinstance(relative, str) or not relative:
        raise ValueError(f'PKP001 unsafe persistence path: {relative}')
    path = (root / relative).resolve()
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError(f'PKP001 unsafe persistence path: {relative}')
    return path


def accepted_transition(root, relative):
    if not relative or not inside(root, relative).is_file():
        return False
    path = Path(__file__).resolve().parents[2] / 'program-kit-governance/scripts/decision_status.py'
    spec = importlib.util.spec_from_file_location('persistence_decision_status', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.has_decision_status(inside(root, relative).read_text(encoding='utf-8'), 'Accepted')


def resolve(root, feature=None, requested=None):
    if feature is None:
        feature = read(root / '.specify/feature.json', {}).get('feature_directory')
    decisions = read(root / 'docs/architecture/bootstrap-decisions.json', {})
    ownership = read(inside(root, feature) / 'artifact-ownership.json', {}) if feature else {}
    managed = read(root / '.program-kit/managed.json', {})
    declarations = decisions.get('persistence', managed.get('persistenceOwners', []))
    if not isinstance(declarations, list):
        raise ValueError('PKP001 persistence must be a list of data owners')
    declarations = [dict(item) for item in declarations]
    declared_profiles = set(decisions.get('selected_profiles', [])) | set(ownership.get('profiles', []))
    legacy = requested if requested and requested != 'auto' else managed.get('persistenceProfile', 'none')
    hints = (declared_profiles & set(PROFILES)) or ({legacy} if legacy in PROFILES else set())
    # Retain older explicit intent as a proposal, never silently erase it or pretend it is admitted.
    if not declarations:
        declarations = [{'owner': 'unassigned-' + p, 'storage': 'relational', 'profile': p,
                         'status': 'proposed'} for p in sorted(hints)]
    blockers, owners, identities = [], [], set()
    previous = {item['owner']: item for item in managed.get('persistenceOwners', [])}
    admissions = ownership.get('persistenceAdmissions', {})
    if not isinstance(admissions, dict):
        raise ValueError('PKP001 persistenceAdmissions must be keyed by canonical data owner')
    for item in declarations:
        owner, storage = item.get('owner'), item.get('storage')
        if not isinstance(owner, str) or not owner.strip() or owner in identities:
            raise ValueError('PKP001 persistence owners must be named and unique')
        identities.add(owner)
        profile = item.get('profile', 'auto')
        if profile == 'auto':
            if storage == 'server-relational' and 'dotnet' not in declared_profiles and not managed:
                raise ValueError('PKP001 EF/PostgreSQL default requires selected .NET intent')
            profile = 'ef-postgresql' if storage == 'server-relational' else 'none' if storage == 'none' else None
        if profile not in {*PROFILES, 'none', 'custom'}:
            raise ValueError(f'PKP001 {owner}: choose an explicit supported or custom profile for {storage}')
        baseline_profile = profile
        admitted = admissions.get(owner, {})
        allowed = {'status', 'capability', 'providerProject', 'testProjects', 'admission', 'checkIds',
                   'packages', 'packageAssignments', 'transitionAuthority', 'dbContext', 'testProvisioning', 'providerOverride'}
        if not isinstance(admitted, dict) or set(admitted) - allowed:
            raise ValueError(f'PKP001 {owner}: feature admission cannot override canonical provider/storage intent')
        installed = previous.get(owner, {})
        if (installed.get('profile') == profile or installed.get('baselineProfile') == profile) and installed.get('status') == 'admitted':
            # Upgrade retains an earlier admitted owner's design; renewed phase review binds its sources.
            inherited = {k: v for k, v in installed.items() if k in allowed}
            item = {**item, **inherited}
        item = {**item, **admitted}
        if item.get('testProvisioning', 'testcontainers') not in {'testcontainers', 'supervisor'}:
            raise ValueError('PKP001 unknown test provisioning owner')
        override = item.get('providerOverride')
        override_error = None
        if override is not None:
            if not isinstance(override, dict) or set(override) != {'profile', 'authority'} or override.get('profile') not in {*PROFILES, 'none', 'custom'}:
                raise ValueError('PKP001 providerOverride requires an exact profile and accepted authority')
            profile = override['profile']
            item['transitionAuthority'] = override['authority']
            if not accepted_transition(root, override['authority']):
                override_error = 'provider override requires an Accepted transition decision'
        status = item.get('status', 'proposed')
        if status not in {'proposed', 'admitted'}:
            raise ValueError(f'PKP001 {owner}: status is proposed or admitted; verification is computed evidence')
        errors = []
        if override_error:
            errors.append(override_error)
        if profile != 'none':
            if status != 'admitted':
                errors.append('complete reviewed persistence admission')
            if not item.get('capability') or not item.get('providerProject') or not item.get('testProjects'):
                errors.append('declare owning capability, provider project and real-provider test projects')
            for key in ADMISSIONS:
                refs = item.get('admission', {}).get(key, [])
                if not isinstance(refs, list) or not refs or not all(inside(root, ref).is_file() for ref in refs):
                    errors.append('missing admission evidence: ' + key)
            if not item.get('checkIds'):
                errors.append('name real-provider behavior checks')
            if profile == 'custom' and not item.get('packages'):
                errors.append('custom profile needs exact approved package assignments')
            if profile == 'custom':
                assignments = item.get('packageAssignments', {})
                if (set(assignments) != {'provider', 'tests'} or not assignments.get('provider')
                        or any(not isinstance(values, list) or not set(values) <= set(item.get('packages', {})) for values in assignments.values())):
                    errors.append('custom packageAssignments must name provider/tests packages from approved pins')
        old = previous.get(owner)
        if old and old.get('profile') != profile and old.get('status') == 'admitted':
            authority = item.get('transitionAuthority')
            if not accepted_transition(root, authority):
                errors.append(f"provider transition from {old['profile']} requires accepted migration authority")
        resolved = {**item, 'profile': profile, 'baselineProfile': baseline_profile, 'status': status, 'admissionComplete': not errors}
        owners.append(resolved)
        if not feature or owner in ownership.get('persistenceOwners', []):
            blockers.extend(f'PKP002 {owner}: {error}' for error in errors)
    declared = {item['profile'] for item in owners}
    if (declared_profiles & set(PROFILES)) - (declared | {item['baselineProfile'] for item in owners}):
        blockers.append('PKP002 selected persistence profiles disagree with data-owner declarations')
    if legacy in PROFILES and declared and legacy not in declared and not previous:
        authorities = [i.get('transitionAuthority') for i in owners]
        if not authorities or not all(accepted_transition(root, a) for a in authorities):
            blockers.append(f'PKP002 existing {legacy} differs from desired profiles; preserve it until migration authority is accepted')
    missing = set(ownership.get('persistenceOwners', [])) - identities
    blockers.extend(f'PKP002 missing declared data owner: {owner}' for owner in sorted(missing))
    if set(admissions) - identities or set(admissions) - set(ownership.get('persistenceOwners', [])):
        raise ValueError('PKP001 feature admissions must belong to declared, scoped data owners')
    for owner in previous.keys() - identities:
        if previous[owner].get('status') == 'admitted':
            blockers.append(f'PKP002 removing existing {owner} requires an explicit none transition with migration authority')
    selected = sorted(declared - {'none'})
    return {'schemaVersion': 1, 'owners': owners, 'profiles': selected,
            'scope': ownership.get('persistenceOwners', []) if feature else None,
            'summary': selected[0] if len(selected) == 1 else 'mixed' if selected else 'none',
            'blockers': blockers, 'installedOwners': list(previous.values())}


def packages(owner, template):
    profile = owner['profile']
    if profile == 'none':
        return {}
    if profile == 'custom':
        return owner.get('packages', {})
    path = template / '.program-kit/eng/profiles/persistence' / f'ProgramKit.Persistence.{PROFILES[profile]}.props'
    return {node.attrib['Include']: node.attrib['Version'] for node in ET.parse(path).iter('PackageVersion')
            if owner.get('testProvisioning') != 'supervisor' or not node.attrib['Include'].startswith('Testcontainers.')}


def pins(selection, template):
    result = {}
    for owner in selection['owners']:
        if not owner['admissionComplete']:
            continue
        for package, version in packages(owner, template).items():
            if not isinstance(version, str) or not version or any(c in version for c in '*[](),$'):
                raise ValueError(f'PKP003 {package} requires an exact approved pin')
            if package in result and result[package] != version:
                raise ValueError(f'PKP003 conflicting shared pin for {package}: {result[package]} / {version}')
            result[package] = version
    return result


def project_packages(owner, project, template):
    values = packages(owner, template)
    test = project in owner['testProjects']
    if owner['profile'] == 'custom':
        return {name: values[name] for name in owner['packageAssignments']['tests' if test else 'provider']}
    return {name: version for name, version in values.items()
            if test == name.startswith('Testcontainers.') or name == 'Microsoft.EntityFrameworkCore'}


def render(selection, template):
    project = ET.Element('Project')
    group = ET.SubElement(project, 'ItemGroup')
    # Unresolved transitions never remove the pins of an installed admitted owner.
    for name, version in sorted(pins(effective(selection), template).items()):
        ET.SubElement(group, 'PackageVersion', Include=name, Version=version)
    ET.indent(project, space='  ')
    return ET.tostring(project, encoding='utf-8') + b'\n'


def effective(selection):
    if selection['blockers'] and selection.get('installedOwners'):
        owners = selection['installedOwners']
        profiles = sorted({owner['profile'] for owner in owners} - {'none'})
        return {**selection, 'owners': owners, 'summary': profiles[0] if len(profiles) == 1 else 'mixed' if profiles else 'none'}
    return selection


def coherence(root, selection, template, *, materialized=False):
    """Validate literal project assignments; evaluated restore/build proof remains mandatory."""
    errors = list(selection['blockers'])
    expected = pins(selection, template)
    if not expected:
        return errors
    central = root / 'Directory.Packages.props'
    if not central.is_file():
        return errors + (['PKP004 materialize central package imports'] if materialized else [])
    # Reuse the strict bundle import/central-pin authority, including duplicate/conflicting pins.
    path = template / '.program-kit/eng/central_packages.py'
    spec = importlib.util.spec_from_file_location('persistence_bundle_pins', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        actual = module.central_package_versions(root)
        for name, version in expected.items():
            if actual.get(name.lower()) != version and actual.get(name) != version:
                errors.append(f'PKP004 central pin/import missing or different: {name} {version}')
    except (ValueError, OSError, ET.ParseError) as error:
        errors.append(f'PKP004 central package graph: {error}')
    assigned = {}
    for owner in selection['owners']:
        if not owner['admissionComplete'] or owner['profile'] == 'none':
            continue
        if selection.get('scope') is not None and owner['owner'] not in selection['scope']:
            continue
        for project in [owner['providerProject'], *owner['testProjects']]:
            if project in assigned and assigned[project] != owner['owner']:
                errors.append(f'PKP004 project has multiple data owners: {project}')
            assigned[project] = owner['owner']
            path = inside(root, project)
            if not path.is_file():
                if materialized:
                    errors.append(f'PKP004 create owned persistence project: {project}')
                continue
            refs = {node.attrib.get('Include'): node for node in ET.parse(path).iter('PackageReference')}
            required = project_packages(owner, project, template)
            for name in required:
                if name not in refs:
                    errors.append(f'PKP004 {project} must reference {name}')
                elif any(key in refs[name].attrib for key in ('Version', 'VersionOverride')):
                    errors.append(f'PKP004 {project} overrides central pin {name}')
    return errors


def validate_evaluated(selection, template, evaluated):
    """Check the actual MSBuild graph; conditional/aliased items cannot pass by text presence."""
    if selection['blockers']:
        raise ValueError('PKP005 persistence admission is incomplete: ' + '; '.join(selection['blockers']))
    expected_pins = pins(selection, template)
    assigned = {}
    for owner in selection['owners']:
        if not owner['admissionComplete'] or owner['profile'] == 'none':
            continue
        for project in [owner['providerProject'], *owner['testProjects']]:
            assigned[project] = owner
    if not set(assigned) <= set(evaluated):
        raise ValueError('PKP005 architecture verification omitted owned persistence projects: ' + str(sorted(set(assigned) - set(evaluated))))
    for project, data in evaluated.items():
        references = {p['Identity']: p for p in data['Items'].get('PackageReference', [])}
        owner = assigned.get(project)
        forbidden = set(references) & set(expected_pins) if owner is None else set()
        if forbidden:
            raise ValueError(f'PKP005 persistence packages escape their owning provider/tests: {project}: {sorted(forbidden)}')
        if owner is None:
            continue
        actual_pins = {}
        for item in data['Items'].get('PackageVersion', []):
            key = item['Identity']
            if key in actual_pins:
                raise ValueError(f'PKP005 duplicate evaluated central pin: {key}')
            actual_pins[key] = item.get('Version')
        if data.get('Properties', {}).get('ManagePackageVersionsCentrally', '').lower() != 'true':
            raise ValueError(f'PKP005 central package management is disabled: {project}')
        required = project_packages(owner, project, template)
        for name, version in required.items():
            item = references.get(name)
            if not item or actual_pins.get(name) != version or item.get('VersionOverride') or item.get('Version'):
                raise ValueError(f'PKP005 evaluated persistence assignment/pin differs: {project}: {name}')
        design = references.get('Microsoft.EntityFrameworkCore.Design')
        if design and design.get('PrivateAssets', '').lower() != 'all':
            raise ValueError(f'PKP005 EF Design must remain private tooling: {project}')
