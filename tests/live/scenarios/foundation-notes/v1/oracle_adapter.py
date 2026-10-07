"""Explicit Notes scenario routing; never silently delegate to the historical lending oracle."""
from pathlib import Path
import importlib.util


def load_notes_oracle(repository: Path):
    path = repository / 'tests/validate_foundation_notes.py'
    if not path.is_file():
        raise RuntimeError('Notes-specific deterministic oracle is missing; this scenario cannot be accepted.')
    specification = importlib.util.spec_from_file_location('foundation_notes_v1_oracle', path)
    if specification is None or specification.loader is None:
        raise RuntimeError('Notes-specific oracle cannot be loaded.')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if getattr(module, 'ORACLE_SCENARIO', None) != 'foundation-notes-v1':
        raise RuntimeError('The selected oracle does not qualify the versioned Notes scenario.')
    return module
