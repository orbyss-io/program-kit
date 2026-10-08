"""Verified effective consumer dependency authority, shared by every projection."""
from pathlib import Path


def resolve(blocks, repository, catalog_path=None):
    repository = repository.resolve()
    sources = {}

    def bind(path):
        path = Path(path).resolve()
        if not path.is_file():
            blocks.fail('PKB111', 'dependency authority source is missing: ' + str(path) + '; restore this exact source before continuing')
        if str(path) not in sources: sources[str(path)] = blocks.raw_sha256(path)
        return path

    candidate = Path(catalog_path) if catalog_path is not None else repository / '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
    if not candidate.is_file():
        if catalog_path is not None or candidate.parent.parent.is_dir():
            blocks.fail('PKB111', 'dependency catalog is missing: ' + str(candidate) + '; restore the selected catalog instead of choosing another default')
        candidate = blocks.default_catalog(Path(blocks.__file__))
    base = blocks.load_json(bind(candidate))
    selected_path = repository / 'docs/architecture/building-block-selection.json'
    record_path = repository / '.program-kit/dependency-profile.json'
    managed_path = repository / '.program-kit/managed.json'
    selection = blocks.load_json(bind(selected_path)) if selected_path.is_file() else None
    record = blocks.load_json(bind(record_path)) if record_path.is_file() else None
    managed = blocks.load_json(bind(managed_path)) if managed_path.is_file() else {}
    scaffold = managed.get('newProjectDependencyProfile')
    identity = None
    qualification = record.get('newProjectQualification') if record else None
    directory = blocks.profile_registry() if catalog_path is not None else candidate.parent / 'dependency-profiles'
    # Standalone upgrade adapters can inspect pre-registry legacy installations.
    # Their installed catalog remains dependency authority; the adapter supplies
    # only reviewed supplemental publisher/ABI metadata, never replacement pins.
    if not (directory / 'index.json').is_file() and selection is not None and not qualification and scaffold is None:
        directory = blocks.profile_registry()
    index = blocks.load_json(bind(directory / 'index.json'))
    catalog_path = candidate
    if selection is not None:
        if selection.get('status') not in {'Draft', 'Accepted'}:
            blocks.fail('PKB111', 'dependency authority needs a Draft or Accepted selection')
        catalog_path = blocks.consumer_catalog(repository, selection, candidate)
        catalog = blocks.load_json(bind(catalog_path))
        if record: bind(blocks.repository_path(repository, record['profilePath']))
        blocks.validate_catalog(catalog)
        blocks.verify_catalog_binding(selection, catalog)
        blocks.verify_new_project_profile(repository, catalog, [])
        authority = 'captured-' + selection['status'].lower()
        if qualification: identity = qualification['profile']
    elif record is not None:
        blocks.fail('PKB111', '.program-kit/dependency-profile.json has no selection; recover its captured selection instead of choosing a default')
    else:
        identity = scaffold.get('profile') if isinstance(scaffold, dict) else (None if managed_path.is_file() else index['default'])
        if scaffold is not None and not identity:
            blocks.fail('PKB611', '.program-kit/managed.json recorded scaffold profile is corrupt; restore its exact recorded authority')
        if identity:
            catalog, _ = blocks.qualified_dependency_profile(directory, identity, base)
            entry = index['profiles'][identity]
            if scaffold is not None and (blocks.catalog_resolution_sha256(catalog) != scaffold.get('catalogResolutionSha256')
                    or not blocks.profile_entry_matches_hash(entry, scaffold.get('entrySha256'))):
                blocks.fail('PKB611', '.program-kit/managed.json scaffold authority changed; restore its recorded profile or review an explicit dependency transition')
            authority = 'recorded-scaffold' if scaffold is not None else 'qualified-default'
        else:
            catalog, authority = base, 'legacy-installation'
    blocks.validate_catalog(catalog)
    resolution = blocks.catalog_resolution_sha256(catalog)
    # Full tuple matching preserves independently versioned tools and Forms.
    if identity is None:
        for name, entry in index['profiles'].items():
            profile = blocks.load_json(directory / entry['path'])
            if profile.get('catalogResolutionSha256') == resolution:
                identity = name
                break
    knowledge = None
    if identity is not None:
        qualified, _ = blocks.qualified_dependency_profile(directory, identity, base)
        if blocks.catalog_resolution_sha256(qualified) != resolution:
            blocks.fail('PKB111', 'qualification differs from captured catalog; restore exact authority or review a dependency transition')
        entry = index['profiles'][identity]
        # All files used to verify this authority participate in context reuse.
        def entry_sources(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if (key == 'path' or key.endswith('Path')) and isinstance(child, str):
                        path = directory / child
                        if path.is_file(): bind(path)
                    entry_sources(child)
            elif isinstance(value, list):
                for child in value: entry_sources(child)
        entry_sources(entry)
        if entry.get('knowledge'):
            knowledge = blocks.load_json(directory / entry['knowledge']['path'])
            entry_sources(knowledge)
    abi = blocks.load_json(bind(directory / 'engineering-contracts.json'))['releases'].get(catalog['families']['foundation']['releaseVersion'].split('-')[0])
    if abi is None: blocks.fail('PKB611', 'selected Foundation has no reviewed shared ABI; repair that exact profile')
    if knowledge and abi['sourceCommit'] != knowledge['sourceCommit']:
        blocks.fail('PKB611', 'publisher knowledge and engineering-contracts.json bind different source commits; repair the selected profile')
    return {'catalog': catalog, 'catalogPath': str(catalog_path), 'authority': authority,
            'authorityPath': str(directory / index['profiles'][identity]['path']) if authority in {'recorded-scaffold', 'qualified-default'} else str(catalog_path),
            'profile': identity, 'qualification': qualification, 'resolutionSha256': resolution,
            'profileEntrySha256': blocks.canonical_sha256(index['profiles'][identity]) if identity else None,
            'sharedAbi': abi, 'publisherKnowledge': knowledge, 'sources': sources}
