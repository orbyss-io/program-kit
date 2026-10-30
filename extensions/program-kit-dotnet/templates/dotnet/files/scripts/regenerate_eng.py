"""Rebuild disposable engineering projections from durable, explicitly selected inputs.

This stdlib-only entrypoint is shared by native MSBuild, humans and the installed
agent command. It never installs tools, resolves new versions or starts services.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import time

sys.dont_write_bytecode = True

RECIPE = 'config/program-kit/engineering.json'


def native_bootstrap_nodes(tree):
    """Recognize only the maintained projection hook, including read-only admission."""
    matches = [node for node in tree if node.tag == 'Target' and node.get('Name') == 'ProgramKitRegenerateEngineering']
    expected = {'Name': 'ProgramKitRegenerateEngineering',
        'BeforeTargets': '_GenerateRestoreGraphProjectEntry;_GenerateRestoreProjectPathWalk;CollectPackageReferences;Restore;PrepareForBuild',
        'Condition': "'$(ProgramKitReadOnlyRestoreGraph)' != 'true'"}
    command = '"$(ProgramKitPythonCommand)" "$(ProgramKitRepositoryRoot)/scripts/regenerate_eng.py" --repository "$(ProgramKitRepositoryRoot)"'
    require(len(matches) == 1 and matches[0].attrib == expected and len(matches[0]) == 1
            and matches[0][0].tag == 'Exec' and matches[0][0].attrib == {'Command': command}
            and not list(matches[0][0])
            and tree.findtext('./PropertyGroup/ProgramKitRepositoryRoot') == "$([System.IO.Path]::GetFullPath('$(MSBuildThisFileDirectory)../../..'))",
            'engineering regeneration target differs from its maintained deterministic recipe')
    return {id(node) for node in matches[0].iter()}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def require(value, message):
    if not value:
        raise ValueError('PKE001 ' + message)


def inside(root, relative):
    path = PurePosixPath(relative)
    require(isinstance(relative, str) and relative and not path.is_absolute()
            and ':' not in relative and '\\' not in relative and '..' not in path.parts
            and path.as_posix() == relative, 'invalid repository input path: ' + str(relative))
    target = root / relative
    require(target.resolve().is_relative_to(root), 'input/output escapes the repository: ' + relative)
    for candidate in (target, *target.parents):
        if candidate == root:
            break
        require(not candidate.is_symlink() and not candidate.is_junction(),
                'linked engineering input/output is not supported: ' + relative)
    return target


def read(root, relative):
    path = inside(root, relative)
    require(path.is_file(), 'missing durable input ' + relative + '; restore it from source control or the exact selected toolkit; no defaults were substituted')
    return path.read_bytes()


def project(root):
    """Validate all inputs and compute all bytes before creating any output."""
    require(Path(__file__).resolve() == inside(root, 'scripts/regenerate_eng.py').resolve(),
            'invoke the target consumer generator at scripts/regenerate_eng.py; an external checkout cannot supply its selected helper behavior')
    recipe = json.loads(read(root, RECIPE))
    require(recipe.get('schemaVersion') == 1, 'unsupported engineering recipe; restore the selected toolkit')
    runtime = recipe.get('runtime')
    require(isinstance(runtime, dict) and 'scripts/regenerate_eng.py' in runtime,
            'engineering recipe has no pinned generator identity')
    for relative, expected in runtime.items():
        require(hashlib.sha256(read(root, relative)).hexdigest() == expected,
                'selected toolkit helper differs: ' + relative + '; restore its exact selected version')
        loaded = sys.modules.get(Path(relative).stem)
        require(loaded is None or Path(getattr(loaded, '__file__', '')).resolve() == inside(root, relative).resolve(),
                'a different checkout supplied an already-loaded helper: ' + relative)
    sys.path.insert(0, str(root / 'scripts'))
    from program_kit_version import PROGRAM_KIT_VERSION
    require(recipe.get('toolkitVersion') == PROGRAM_KIT_VERSION,
            'selected toolkit version differs from scripts/program_kit_version.py; restore the exact selected toolkit')
    pin = read(root, '.python-version').decode('utf-8-sig').strip()
    require(pin == '.'.join(map(str, sys.version_info[:3])),
            'selected Python ' + pin + ' is required; select an already installed matching interpreter')
    inputs = recipe.get('inputs')
    require(isinstance(inputs, list) and inputs and len(inputs) == len(set(inputs)), 'invalid durable input selection')
    contents = {relative: read(root, relative) for relative in inputs}
    # An authored edit is a new input, never an approval/hash mismatch. The owning
    # architecture and composition validators retain their semantic contracts.
    from repository_architecture import validate_manifest
    architecture = json.loads(contents['config/program-kit/architecture.json'])
    validate_manifest(root, architecture)
    result = {'eng/architecture.json': encoded(architecture)}
    if 'config/program-kit/foundation-composition.json' in contents:
        import composition_model
        import composition_render
        graph = composition_model.validate(json.loads(contents[composition_model.INPUT]))
        contract = json.loads(contents[composition_render.CONTRACT])
        result[composition_render.RESOLVED] = encoded(composition_render.resolve(graph, contract))
        baseline = json.loads(contents['tools/program-kit/web/web-contract.json'])
        result.update(composition_render.web_contract_projections(graph, contract, baseline))
    result['eng/inputs.json'] = encoded({'schemaVersion': 1, 'toolkitVersion': PROGRAM_KIT_VERSION,
        'inputs': {relative: hashlib.sha256(data).hexdigest() for relative, data in sorted(contents.items())},
        'scope': 'Deterministic engineering projections; no execution, approval or acceptance evidence'})
    return result


def regenerate(root, check=False):
    root = root.resolve()
    outputs = project(root)
    # Resolve every destination before mutation. Different native projects may
    # regenerate concurrently; identical bytes and unique atomic replacements
    # make that safe without persisted locks, checkpoints or timestamps.
    require(isinstance(outputs, dict) and outputs, 'projection helper returned no output map')
    for relative, payload in outputs.items():
        require(isinstance(relative, str) and len(PurePosixPath(relative).parts) > 1
                and PurePosixPath(relative).parts[0] == 'eng' and isinstance(payload, bytes),
                'projection output must be strictly below root eng/: ' + str(relative))
    destinations = {relative: inside(root, relative) for relative in outputs}
    changed = [relative for relative, path in destinations.items()
               if not path.is_file() or path.read_bytes() != outputs[relative]]
    if check:
        return changed
    for relative in changed:
        path = destinations[relative]
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(outputs[relative])
            for attempt in range(5):
                try:
                    os.replace(temporary, path)
                    break
                except PermissionError as error:
                    if os.name != 'nt' or getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 4:
                        raise
                    time.sleep(.02 * (attempt + 1))
        finally:
            Path(temporary).unlink(missing_ok=True)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        changed = regenerate(args.repository, args.check)
        print('Engineering projections: ' + (', '.join(changed) if changed else 'current'))
        return int(bool(changed) and args.check)
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        print('PKE001 cannot regenerate eng: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
