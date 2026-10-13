from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


PROFILE_SHELLS = Path("eng/web-profile.shells.json")
BUILDING_BLOCK_SHELLS = Path("eng/building-blocks.shells.json")
CONSUMER_SHELLS = Path("shells.json")
SELECTION = Path("docs/architecture/building-block-selection.json")


def resource_model(repository):
    path = repository / 'eng/foundation-composition.json'
    if path.is_file() and json.loads(path.read_text(encoding='utf-8')).get('schemaVersion') == 2:
        import composition_model
        return composition_model.load(repository)
    return None


def selected_sources(repository: Path) -> tuple[list[Path], list[Path], dict[Path, set[str]]]:
    """Consume existing Accepted placements; do not create another feature selector."""
    selection_path = repository / SELECTION
    selection = json.loads(selection_path.read_text(encoding="utf-8")) if selection_path.is_file() else {}
    targets = selection.get("targets", []) if selection.get("status") == "Accepted" else []
    selected: dict[Path, set[str]] = {}
    graph = resource_model(repository)
    if graph:
        import composition_model
        for shell in composition_model.resources(graph, 'shell').values():
            selected.setdefault(Path(shell['source']), set()).add(shell['name'])
    for target in targets:
        if target.get("kind") != "cshell-shell":
            continue
        path, name = target.get("path"), target.get("shell")
        if (not isinstance(path, str) or "\\" in path or ":" in path or
                not path.endswith("/shells.json") and path != "shells.json" or
                Path(path).is_absolute() or any(part in {".", "..", ""} for part in path.split("/")) or
                not isinstance(name, str) or not name):
            raise ValueError("PKC006 selected shell requires a local shells.json path and explicit shell identity")
        source = Path(path)
        if not (repository / source).resolve().is_relative_to(repository.resolve()):
            raise ValueError("PKC006 selected shell source must stay inside the repository")
        if graph and (source not in selected or name not in selected[source]):
            raise ValueError('PKC009 Accepted shell placement conflicts with the canonical composition; reconcile the scoped decision')
        selected.setdefault(source, set()).add(name)
    consumers = sorted(selected) if selected else [CONSUMER_SHELLS]
    managed = [path.parent / BUILDING_BLOCK_SHELLS for path in consumers]
    return consumers, managed, selected


def source_paths(repository: Path) -> list[Path]:
    consumers, managed, _ = selected_sources(repository)
    return [PROFILE_SHELLS, *consumers, *managed, *([SELECTION] if (repository / SELECTION).is_file() else []),
            *([Path('eng/foundation-composition.json')] if resource_model(repository) else [])]


def load(path: Path, required: bool) -> dict:
    if not path.is_file():
        if required:
            raise ValueError(f"PKC001 required shell configuration is missing: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        shells = value["CShells"]["Shells"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"PKC002 {path} must use the CShells:Shells object schema: {error}") from error
    if not isinstance(value, dict) or not isinstance(shells, dict) or not shells:
        raise ValueError(f"PKC002 {path} must declare at least one named shell")
    for shell_name, shell in shells.items():
        features = shell.get("Features") if isinstance(shell, dict) else None
        if not isinstance(shell_name, str) or not shell_name or not isinstance(features, dict):
            raise ValueError(f"PKC003 {path} shell {shell_name!r} must declare a Features object")
        for identity, settings in features.items():
            if not isinstance(identity, str) or not identity or not (settings is False or isinstance(settings, dict)):
                raise ValueError(
                    f"PKC004 {path} shell {shell_name!r} feature {identity!r} must be an object or false"
                )
    return value


def merge_value(baseline: object, overlay: object) -> object:
    if not isinstance(baseline, dict) or not isinstance(overlay, dict):
        return deepcopy(overlay)
    result = deepcopy(baseline)
    for key, value in overlay.items():
        result[key] = merge_value(result[key], value) if key in result else deepcopy(value)
    return result


def compose(repository: Path, include_frontend_admission: bool = True) -> dict:
    repository = repository.resolve()
    profile = load(repository / PROFILE_SHELLS, required=False)
    consumers, managed, selected = selected_sources(repository)
    consumer: dict = {}
    building_blocks: dict = {}
    for source, companion in zip(consumers, managed, strict=True):
        value = load(repository / source, required=True)
        names = set(value["CShells"]["Shells"])
        if selected and names != selected[source]:
            raise ValueError("PKC007 selected shell source must match its Accepted identities")
        if names & set(consumer.get("CShells", {}).get("Shells", {})):
            raise ValueError("PKC007 duplicate selected shell identity")
        consumer = merge_value(consumer, value)
        contribution = load(repository / companion, required=False)
        if contribution and not set(contribution["CShells"]["Shells"]) <= names:
            raise ValueError("PKC007 managed shell contribution must belong to its selected source")
        building_blocks = merge_value(building_blocks, contribution)
    # The maintained single-default profile supplies defaults to one explicitly selected
    # application shell. Multiple shells require explicitly named profile entries.
    if selected and profile:
        profile_names = set(profile["CShells"]["Shells"])
        consumer_names = set(consumer["CShells"]["Shells"])
        if profile_names == {"default"} and consumer_names != {"default"}:
            if len(consumer_names) != 1:
                raise ValueError("PKC008 multiple selected shells require explicitly named web-profile defaults")
            name = next(iter(consumer_names))
            profile = deepcopy(profile)
            entry = profile["CShells"]["Shells"].pop("default")
            if "Name" in entry:
                entry["Name"] = name
            profile["CShells"]["Shells"][name] = entry
        elif not profile_names <= consumer_names:
            raise ValueError("PKC008 profile contains an unselected shell")
    effective = merge_value(merge_value(profile, consumer), building_blocks)
    assert isinstance(effective, dict)
    # Consumer values may override profile defaults. An Accepted building-block activation is merged
    # last and cannot be silently disabled in consumer-owned shells.json.
    shells = effective.get("CShells", {}).get("Shells")
    if not isinstance(shells, dict) or not shells:
        raise ValueError("PKC005 effective shell composition contains no named shells")
    graph = resource_model(repository)
    if graph and include_frontend_admission:
        import composition_model
        import prepare_hosted_pages
        for row in composition_model.bindings(graph, 'frontend'):
            options = prepare_hosted_pages.admission(repository, graph, row['frontendRef'], required=False)
            if options:
                shell = shells[graph['resources'][row['shellRef']]['name']]
                shell['Configuration']['Foundation']['HostedPages'].update(options)
    return effective


def compose_for_stage(repository: Path, staged: Path) -> dict:
    value = compose(repository)
    graph = resource_model(repository)
    if graph:
        import composition_model
        import composition_render
        hosts = [name for name, host in composition_model.resources(graph, 'host').items()
                 if (repository / composition_render.stage_path(host)).resolve() == staged.resolve()]
        if len(hosts) != 1:
            raise ValueError('PKC009 runtime stage must belong to exactly one declared host')
        names = {graph['resources'][shell]['name'] for shell in composition_model.host_shells(graph, hosts[0])}
        value['CShells']['Shells'] = {name: shell for name, shell in value['CShells']['Shells'].items() if name in names}
    return value


def write(repository: Path, output: Path) -> Path:
    value = compose(repository)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output


def activated_features(repository: Path) -> dict[str, set[str]]:
    shells = compose(repository)["CShells"]["Shells"]
    return {
        shell_name: {
            identity for identity, settings in shell["Features"].items() if settings is not False
        }
        for shell_name, shell in shells.items()
    }
