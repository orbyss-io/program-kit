"""Prepare exact development candidates for paid learning trials, without Release acceptance."""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import uuid
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from live.v2.common import LiveContractError, atomic_write_json, load_object, safe_relative, sha256_file, utc_now, validate

STEPS = ('components', 'schema-runtime', 'build', 'packaged-install')


def artifact_names(version: str) -> set[str]:
    return {f'artifacts/{name}-{version}.zip' for name in (
        'program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet',
        'program-kit-governance-preset', 'program-kit-bootstrap', 'program-kit')} | {
        f'artifacts/Initialize-ProgramKit-{version}.cmd', f'artifacts/Initialize-ProgramKit-{version}.sh', 'artifacts/SHA256SUMS'}


def file_record(root: Path, path: Path) -> dict:
    return {'path':path.relative_to(root).as_posix(), 'size':path.stat().st_size, 'sha256':sha256_file(path)}


def validate_trial_receipt(root: Path, path: Path, schemas: Path) -> tuple[dict, str]:
    value = load_object(path)
    validate(value, load_object(schemas / 'trial-receipt.schema.json'))
    if {step['id'] for step in value['steps']} != set(STEPS) or len(value['steps']) != len(STEPS):
        raise LiveContractError('LIVE_TRIAL_PREPARATION_STEPS_MISSING')
    if {record['path'] for record in value['artifacts']} != artifact_names(value['version']):
        raise LiveContractError('LIVE_TRIAL_ARTIFACT_INVENTORY_MISMATCH')
    for record in [*value['artifacts'], *value['preparationLogs']]:
        file = root / safe_relative(record['path'])
        if not file.is_file() or not file.resolve().is_relative_to(root.resolve()) or file.stat().st_size != record['size'] or sha256_file(file) != record['sha256']:
            raise LiveContractError(f"LIVE_TRIAL_EVIDENCE_CHANGED: {record['path']}")
    for step in value['steps']:
        if not any(record['path'].endswith(f"/{step['id']}/workflow.stdout.log") for record in value['preparationLogs']):
            raise LiveContractError('LIVE_TRIAL_PREPARATION_LOG_MISSING')
    catalog = root / 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
    # Catalog resolution digest is computed by the source's own resolver, as in Release receipts.
    result = subprocess.run([sys.executable, str(root / 'extensions/program-kit-building-blocks/scripts/building_blocks.py'), 'catalog-hash'],
                            capture_output=True, text=True, encoding='utf-8', check=False)
    if not catalog.is_file() or result.returncode or result.stdout.strip() != value['catalog']['sha256']:
        raise LiveContractError('LIVE_CANDIDATE_CATALOG_MISMATCH')
    return value, sha256_file(path)


def prepare(source: Path, validation_python: Path) -> Path:
    from live.v2 import cli
    root = Path(__file__).resolve().parents[3]
    source = source.resolve()
    if cli.git(source, 'status', '--porcelain=v1') or cli.git(root, 'status', '--porcelain=v1'):
        raise LiveContractError('LIVE_TRIAL_PREPARATION_REQUIRES_CLEAN_SOURCE_AND_HARNESS')
    identity = {'commit':cli.git(source,'rev-parse','HEAD'), 'tree':cli.git(source,'rev-parse','HEAD^{tree}'), 'clean':True}
    version = (source / 'VERSION').read_text(encoding='utf-8').strip()
    started = utc_now()
    output = source / 'artifacts/live-trial-preparation' / uuid.uuid4().hex[:12]
    commands = (
        [str(validation_python), str(source / 'tests/validate_components.py')],
        [str(validation_python), str(source / 'extensions/program-kit-governance/scripts/schema_runtime.py'), 'setup'],
        [str(validation_python), str(source / 'scripts/build_release.py')],
        [str(validation_python), str(source / 'tests/validate_release_install.py')],
    )
    steps, logs = [], []
    environment = cli.supervisor_environment()
    # Desktop's injected TLS key-log hook can crash this installed Windows Python build.
    environment.pop('SSLKEYLOGFILE', None)
    for name, command in zip(STEPS, commands):
        print(f'Development trial preparation: {version} / {name}', flush=True)
        result = cli.run_supervised(command, cwd=source, environment=environment,
                                    evidence_directory=output / name, timeout_seconds=900)
        if result.exitCode or not result.cleanupComplete or not result.logsDrained:
            raise LiveContractError(f'LIVE_TRIAL_PREPARATION_FAILED: {name}; retained evidence: {output / name}')
        steps.append({'id':name, 'command':command, 'exitCode':0, 'startedAt':result.startedAt, 'finishedAt':result.finishedAt})
        logs.extend(file_record(source, output / name / stream.path) for stream in (result.stdout, result.stderr))
    if cli.git(source,'rev-parse','HEAD') != identity['commit'] or cli.git(source,'status','--porcelain=v1'):
        raise LiveContractError('LIVE_TRIAL_SOURCE_CHANGED_DURING_PREPARATION')
    catalog = subprocess.check_output([sys.executable, str(source / 'extensions/program-kit-building-blocks/scripts/building_blocks.py'), 'catalog-hash'], text=True).strip()
    receipt = {'schemaVersion':'2.0', 'status':'development-trial-prepared',
               'acceptanceScope':'development-trial-only', 'releaseValidationPassed':False,
               'version':version, 'source':identity,
               'platform':{'system':platform.system(),'release':platform.release(),'machine':platform.machine()},
               'toolchains':{'python':platform.python_version(), **{name:cli.tool_version(name) for name in cli.LIVE_TOOLCHAINS}},
               'steps':steps, 'preparationLogs':logs,
               'artifacts':[file_record(source, source / name) for name in sorted(artifact_names(version))],
               'catalog':{'sha256':catalog}, 'startedAt':started, 'finishedAt':utc_now()}
    path = output / f'trial-receipt-{version}.json'
    atomic_write_json(path, receipt)
    validate_trial_receipt(source, path, cli.schemas(root))
    cli.preflight(source, receipt)
    print(f'Development trial receipt: {path}; no paid session or Release validation performed.', flush=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--validation-python', type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(args.source_root, args.validation_python.resolve())
        return 0
    except (LiveContractError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
