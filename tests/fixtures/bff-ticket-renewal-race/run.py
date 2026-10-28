"""Diagnostic of the known Foundation 0.3.8 race; success means REPRODUCED, not safe."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).resolve().parent
IMAGE = 'ghcr.io/orbyss-io/foundation-host@sha256:bf27d204ee972b6aadf3b156b493773e7c6e6ae9a3bf010a30b46c6d88b5e93a'
QUALIFICATION = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles/candidates/foundation-0.3.8-build-0.3.3-exporter-0.2.7-forms-0.2.1-localization-0.1.2/qualification.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New diagnostic directory')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    packages = output / 'packages'
    payload = output / 'probe'
    inputs = [p for p in FIXTURE.iterdir() if p.is_file()] + [QUALIFICATION]
    digests = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    report = {'meaning': __doc__, 'image': IMAGE, 'startedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'inputs': digests, 'steps': [], 'status': 'running'}
    started = time.monotonic()

    def run(label, command, timeout=120, cwd=ROOT):
        step = {'label': label, 'command': [str(arg) for arg in command]}
        report['steps'].append(step)
        before = time.monotonic()
        # Docker is foreground, auto-removed and network-disabled; only synthetic
        # identities are used. Retain streams without emitting any cookie values.
        with (output / (label + '.stdout.log')).open('wb') as stdout, (output / (label + '.stderr.log')).open('wb') as stderr:
            result = subprocess.run(command, cwd=cwd, stdout=stdout, stderr=stderr, timeout=timeout)
        step.update(exitCode=result.returncode, elapsedSeconds=round(time.monotonic() - before, 3))
        for suffix in ('stdout', 'stderr'):
            path = output / (label + '.' + suffix + '.log')
            step[suffix + 'Sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        if result.returncode:
            raise RuntimeError(f'{label} failed ({result.returncode}); inspect {output}')

    try:
        run('restore', ['dotnet', 'restore', str(FIXTURE / 'RaceProbe.csproj'), '--locked-mode',
            '--packages', str(packages), '--configfile', str(FIXTURE / 'NuGet.Config'), '--disable-parallel'])
        qualification = json.loads(QUALIFICATION.read_text(encoding='utf-8'))
        checked = {}
        for name, entry in qualification['artifacts'].items():
            archive = packages / name.lower() / entry['version'] / f"{name.lower()}.{entry['version']}.nupkg"
            if archive.is_file():
                digest = hashlib.sha256(archive.read_bytes()).hexdigest()
                if digest != entry['sha256']:
                    raise RuntimeError('Qualified archive mismatch: ' + name)
                checked[name] = digest
        if 'Orbyss.Foundation.Authentication.BffCookie' not in checked:
            raise RuntimeError('Published native authentication archive missing')
        report['qualifiedArchiveSha256'] = checked
        run('build', ['dotnet', 'build', str(FIXTURE / 'RaceProbe.csproj'), '--no-restore', '-c', 'Release', '--output', str(payload)])
        run('image', ['docker', 'image', 'inspect', IMAGE, '--format', '{{json .RepoDigests}}'])
        run('runtime', ['docker', 'run', '--rm', '--network', 'none', '--mount',
            f'type=bind,source={payload},target=/probe,readonly', '--entrypoint', 'dotnet', IMAGE, '/probe/RaceProbe.dll'], timeout=45)
        lines = (output / 'runtime.stdout.log').read_text(encoding='utf-8').splitlines()
        identity = json.loads(lines[0])
        outcome = json.loads('\n'.join(lines[1:]))
        if identity['foundation'] != '0.3.8+2b5f6737e558977fd17cd83fe1e03d0b96aa0df4' or outcome['status'] != 'vulnerability-reproduced':
            raise RuntimeError('Unexpected native source identity or diagnostic outcome')
        if len(outcome['cases']) != 11:
            raise RuntimeError('Missing diagnostic cases')
        report.update(identity=identity, outcome=outcome, status='vulnerability-reproduced')
        report['payloadSha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in payload.glob('*') if p.is_file()}
        if any(hashlib.sha256(p.read_bytes()).hexdigest() != digests[str(p.relative_to(ROOT))] for p in inputs):
            raise RuntimeError('Diagnostic inputs changed during execution')
    except BaseException as error:
        report.update(status='failed', diagnostic=str(error))
        raise
    finally:
        report['elapsedSeconds'] = round(time.monotonic() - started, 3)
        (output / 'results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print('Diagnostic evidence: ' + str(output / 'results.json'))
    print('CONFIRMED: Foundation 0.3.8 renews revoked and idle-expired tickets. This is not an acceptance pass.')


if __name__ == '__main__':
    main()
