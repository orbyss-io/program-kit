"""Execute an explicitly anchored current unittest case inventory, never a count gate.

The caller supplies its previously reviewed contract digest. This binds case
identity/source/execution, not publisher authenticity or application acceptance.
Historical source, retired business fixtures and coding agents are never loaded.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import sys
import types
import unittest
import uuid


def require(value, message):
    if not value: raise ValueError('PKT040 ' + message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, 'duplicate case inventory field'); result[name] = value
    return result


def inside(root, name):
    require(isinstance(name, str) and 0 < len(name) <= 512 and '\\' not in name and ':' not in name,
            'case paths must be literal repository-relative paths')
    path = PurePosixPath(name)
    require(path.as_posix() == name and not path.is_absolute() and '..' not in path.parts
            and not any(ord(c) < 32 for c in name), 'case path alias/traversal is not admitted')
    result = root / name
    require(result.resolve().is_relative_to(root), 'case path escaped its owner')
    require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                    for p in (result, *result.parents) if p.is_relative_to(root)), 'linked case source/evidence is not admitted')
    return result


def contract(root, name, expected):
    require(isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected), 'original reviewed contract SHA-256 is required')
    path = inside(root, name)
    require(path.is_file() and path.stat().st_size <= 2_097_152, 'case inventory is missing or exceeds bounds')
    raw = path.read_bytes(); require(digest(raw) == expected, 'case inventory differs from its original review anchor')
    value = json.loads(raw, object_pairs_hook=unique)
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'modules', 'inputs'} and value['schemaVersion'] == 1
            and isinstance(value['modules'], list) and 0 < len(value['modules']) <= 64, 'unsupported/empty case inventory')
    require(isinstance(value['inputs'], list) and len(value['inputs']) <= 8192
            and all(isinstance(item, str) for item in value['inputs'])
            and len({item.casefold() for item in value['inputs']}) == len(value['inputs']), 'case inputs must be a finite exact path inventory')
    for item in value['inputs']: inside(root, item)
    modules, paths, cases = {}, set(), set()
    for row in value['modules']:
        require(isinstance(row, dict) and set(row) == {'module', 'path', 'sha256', 'cases'}, 'case module requires exact source and case declarations')
        module = row['module']
        require(isinstance(module, str) and re.fullmatch('[A-Za-z_]\\w*', module) and module not in modules, 'case module name must be unique and literal')
        source = inside(root, row['path'])
        require(source.suffix == '.py' and row['path'].casefold() not in paths, 'case module path must be unique Python source')
        require(isinstance(row['sha256'], str) and re.fullmatch('[a-f0-9]{64}', row['sha256']), 'case module source hash is required')
        require(isinstance(row['cases'], dict) and 0 < len(row['cases']) <= 4096, 'every module needs a nonempty exact case inventory')
        for name, platforms in row['cases'].items():
            require(isinstance(name, str) and len(name) <= 256 and name.startswith(module + '.') and name not in cases
                    and re.fullmatch('[A-Za-z_]\\w*\\.[A-Za-z_]\\w*\\.test\\w*', name), 'required case identity must be unique and fully qualified')
            require(isinstance(platforms, list) and platforms and len(set(platforms)) == len(platforms)
                    and set(platforms) <= {'Windows', 'Linux', 'Darwin'}, 'case platforms must be explicit')
            cases.add(name)
        require(len(cases) <= 4096, 'case inventory exceeds finite execution bound')
        modules[module] = row; paths.add(row['path'].casefold())
    return modules, value['inputs']


def leaves(suite):
    if isinstance(suite, unittest.TestSuite):
        for item in suite: yield from leaves(item)
    else:
        require(isinstance(suite, unittest.TestCase), 'unsupported test leaf cannot supply coverage')
        yield suite


class Result(unittest.TextTestResult):
    def __init__(self, *args):
        super().__init__(*args); self.observed = {}; self.started = []
    def startTest(self, test):
        self.started.append(test.id()); super().startTest(test)
    def addSuccess(self, test): self.observed[test.id()] = 'passed'; super().addSuccess(test)
    def addFailure(self, test, error): self.observed[test.id()] = 'failed'; super().addFailure(test, error)
    def addError(self, test, error): self.observed[test.id()] = 'error'; super().addError(test, error)
    def addSkip(self, test, reason): self.observed[test.id()] = 'skipped'; super().addSkip(test, reason)
    def addExpectedFailure(self, test, error): self.observed[test.id()] = 'expected-failure'; super().addExpectedFailure(test, error)
    def addUnexpectedSuccess(self, test): self.observed[test.id()] = 'unexpected-success'; super().addUnexpectedSuccess(test)


class BoundedLog:
    encoding = 'utf-8'
    def __init__(self, stream): self.stream = stream; self.bytes = 0
    def write(self, text):
        self.bytes += len(text.encode('utf-8', errors='replace'))
        require(self.bytes <= 2_097_152, 'case diagnostic stream exceeded its finite bound')
        return self.stream.write(text)
    def flush(self): self.stream.flush()
    def isatty(self): return False


def execute(root, name, expected, selected=None):
    root = Path(root).resolve(strict=True); definitions, inputs = contract(root, name, expected)
    selected = list(definitions) if selected is None else list(selected)
    require(selected and len(set(selected)) == len(selected) and set(selected) <= set(definitions), 'select exact declared modules; unknown/empty selection cannot fall back')
    current_platform = platform.system()
    require(current_platform in {'Windows', 'Linux', 'Darwin'}, 'current platform requires an explicit case inventory')
    directory = inside(root, 'artifacts/tests/toolkit-cases/' + uuid.uuid4().hex); directory.mkdir(parents=True)
    value = {'schemaVersion': 1, 'status': 'running', 'contractSha256': expected, 'platform': current_platform,
             'evidencePath': (directory / 'results.json').relative_to(root).as_posix(),
             'runnerSha256': digest(Path(__file__).read_bytes()), 'python': sys.version,
             'productAcceptanceEstablished': False, 'publisherAuthenticityEstablished': False,
             'moduleSourceSha256': {}, 'requiredCases': [], 'notApplicable': [], 'executedCases': {}}
    imported, previous_path, previous_cwd = {}, list(sys.path), Path.cwd()
    result = None
    try:
        os.chdir(root)
        def input_hashes():
            observed = {}; total = 0
            for relative in inputs:
                path = inside(root, relative)
                require(path.is_file() and path.stat().st_size <= 33_554_432, 'declared case input is missing or oversized: ' + relative)
                raw = path.read_bytes(); total += len(raw)
                require(total <= 268_435_456, 'case source inputs exceed finite read budget')
                observed[relative] = digest(raw)
            return observed
        value['inputSha256'] = input_hashes()
        suite = unittest.TestSuite()
        for module_name in selected:
            row = definitions[module_name]; source = inside(root, row['path'])
            require(source.is_file() and source.stat().st_size <= 4_194_304, 'current case source missing or oversized: ' + row['path'])
            raw = source.read_bytes(); require(digest(raw) == row['sha256'], 'case source differs from original inventory: ' + row['path'])
            value['moduleSourceSha256'][row['path']] = row['sha256']
            previous = sys.modules.get(module_name)
            require(previous is None or Path(getattr(previous, '__file__', '')).resolve() == source, 'case module collides with an existing import')
            imported[module_name] = previous
            module = types.ModuleType(module_name); module.__file__ = str(source); module.__package__ = ''
            module.__spec__ = importlib.util.spec_from_file_location(module_name, source)
            sys.modules[module_name] = module; sys.path[:0] = [str(source.parent), str(root)]
            # Compile exactly the already hash-checked current source bytes. A
            # timestamp-matching .pyc cannot substitute another case body.
            exec(compile(raw, str(source), 'exec'), module.__dict__)
            loaded = list(leaves(unittest.defaultTestLoader.loadTestsFromModule(module)))
            actual = [test.id() for test in loaded]
            require(len(actual) == len(set(actual)) and set(actual) == set(row['cases']),
                    'required case/module set changed (counts cannot substitute identities): ' + module_name)
            required = {case for case, platforms in row['cases'].items() if current_platform in platforms}
            value['requiredCases'].extend(sorted(required))
            value['notApplicable'].extend(sorted(set(actual) - required))
            suite.addTests(test for test in loaded if test.id() in required)
        require(value['requiredCases'], 'no required current-platform cases; empty execution cannot pass')
        with (directory / 'execution.log').open('x', encoding='utf-8', newline='\n') as stream:
            bounded = BoundedLog(stream)
            with contextlib.redirect_stdout(bounded), contextlib.redirect_stderr(bounded):
                result = unittest.TextTestRunner(stream=bounded, verbosity=2, resultclass=Result).run(suite)
        value['executedCases'] = result.observed
        require(len(result.started) == len(set(result.started)) and set(result.started) == set(value['requiredCases'])
                and set(result.observed) == set(value['requiredCases']) and all(status == 'passed' for status in result.observed.values())
                and result.wasSuccessful(), 'required case execution was missing, duplicate, skipped, empty or unsuccessful')
        for relative, original in value['moduleSourceSha256'].items():
            require(digest(inside(root, relative).read_bytes()) == original, 'case source changed during execution')
        require(digest(inside(root, name).read_bytes()) == expected, 'case inventory changed during execution')
        require(input_hashes() == value['inputSha256'], 'declared mechanism/source input changed during execution')
        value['status'] = 'passed'
        return value
    except BaseException as error:
        value.update(status='failed', diagnosticType=type(error).__name__, diagnostic=str(error)[:2048])
        if result is not None: value['executedCases'] = result.observed
        raise
    finally:
        for module_name, previous in imported.items():
            if previous is None: sys.modules.pop(module_name, None)
            else: sys.modules[module_name] = previous
        sys.path[:] = previous_path
        os.chdir(previous_cwd)
        logs = directory / 'execution.log'
        value['evidence'] = {'execution.log': digest(logs.read_bytes())} if logs.is_file() else {}
        (directory / 'results.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        print('Case inventory evidence: ' + str(directory / 'results.json'))
        if value['status'] != 'passed':
            failed = [{'id': case, 'status': status} for case, status in sorted(value.get('executedCases', {}).items())
                      if status != 'passed']
            print('Required case failures: ' + json.dumps({'cases': failed[:20], 'total': len(failed)}))
            print('Bounded execution details: ' + str(directory / 'execution.log'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--contract', required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--module', action='append')
    args = parser.parse_args()
    execute(args.project_root, args.contract, args.contract_sha256, args.module)


if __name__ == '__main__': main()
