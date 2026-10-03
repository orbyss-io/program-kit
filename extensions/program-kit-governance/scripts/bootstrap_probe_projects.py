"""Read-only upgrade classification; preserve existing proof tooling source hashes."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('upgrade_probe_contract_validator', Path(__file__).with_name('bootstrap_lifecycle.py'))
_lifecycle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_lifecycle)
LifecycleError = _lifecycle.LifecycleError
load, local, validate_recipe = _lifecycle.load, _lifecycle.local, _lifecycle.validate_recipe

def registered_probe_projects(root: Path) -> set[Path]:
    """Read-only classification of valid, planned scratch-project fixture sources.

    Registration does not establish successful proof or persistence admission.
    Invalid/unregistered declarations never exempt a repository project.
    """
    plan_path = root / 'docs/architecture/bootstrap-proof-plan.json'
    if not plan_path.is_file():
        return set()
    directory = local(root, 'docs/architecture/compatibility')
    try:
        plan = load(plan_path)
        probes = plan.get('probes')
        if plan.get('schemaVersion') != 1 or not isinstance(probes, list):
            return set()
        identities = [probe['id'] for probe in probes]
        if len(identities) != len(set(identities)):
            return set()
    except (LifecycleError, TypeError, KeyError):
        return set()
    projects = set()
    for probe in probes:
        try:
            recipe_path, _, contract, _ = validate_recipe(root, probe['id'], probe['recipe'])
            if not recipe_path.is_relative_to(directory):
                continue
            for target in contract.get('dependencyTargets', []):
                source = local(root, contract['fixtures'][target])
                if Path(target).suffix == '.csproj' and source.suffix == '.csproj' and source.is_relative_to(directory):
                    projects.add(source)
        except (LifecycleError, OSError, ValueError, TypeError, KeyError):
            continue
    # A declared consumer target remains an application even if also offered as
    # a probe fixture. Registration cannot hide materialized application targets.
    selection_path = root / 'docs/architecture/building-block-selection.json'
    try:
        selection = load(selection_path) if selection_path.is_file() else {}
        for target in selection.get('targets', []):
            relative = target.get('path')
            if relative and Path(relative).suffix == '.csproj':
                projects.discard(local(root, relative))
    except (LifecycleError, OSError, TypeError, ValueError, AttributeError):
        return set()
    return projects

