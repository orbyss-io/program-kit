"""Deployment administrator and application-role separation in an owned PostgreSQL fixture."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence = ROOT / 'artifacts/tests/schema-role-grants' / uuid.uuid4().hex
    evidence.mkdir(parents=True)
    selected = json.loads((ROOT / 'extensions/program-kit-dotnet/references/persistence-runtimes.json').read_text())['profiles']['ef-postgresql']
    image = selected['image']
    assert '@sha256:' in image
    container = 'pk-schema-grants-' + uuid.uuid4().hex
    password = secrets.token_hex(24)
    app_password = secrets.token_hex(24)
    environment = {**os.environ, 'POSTGRES_PASSWORD': password}
    operations = []
    created = False

    def run(arguments, input=None, allowed=(0,), child_environment=None):
        result = subprocess.run(['docker', *arguments], input=input, capture_output=True, text=True,
                                env={**environment, **(child_environment or {})}, timeout=90)
        log = (result.stdout + result.stderr).replace(password, '[REDACTED]').replace(app_password, '[REDACTED]')
        (evidence / (str(len(operations)) + '.log')).write_text(log, encoding='utf-8')
        operations.append({'operation': arguments[0], 'exitCode': result.returncode})
        if result.returncode not in allowed:
            raise RuntimeError('Inspect ' + str(evidence))
        return result.returncode, log

    def sql(statement, succeeds=True, application_login=False):
        arguments = (['exec', '-i', '-e', 'PGPASSWORD', container, 'psql', '-h', '127.0.0.1',
                      '-U', 'managed_app', '-d', 'postgres', '-v', 'ON_ERROR_STOP=1'] if application_login else
                     ['exec', '-i', container, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1'])
        code, output = run(arguments, statement, (0,) if succeeds else (3,),
                           {'PGPASSWORD': app_password} if application_login else None)
        if not succeeds:
            assert 'permission denied' in output
        return output

    try:
        run(['pull', image])
        run(['run', '-d', '--pull=never', '--name', container, '--label', 'program-kit.fixture=schema-role-grants',
             '-e', 'POSTGRES_PASSWORD', image])
        created = True
        deadline = time.monotonic() + 45
        while True:
            # The immutable image starts a socket-only initialization server and stops
            # it before the real server starts. Admit the application's TCP transport.
            code, _ = run(['exec', container, 'pg_isready', '-h', '127.0.0.1', '-U', 'postgres'], allowed=(0, 1, 2))
            if not code:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned PostgreSQL fixture did not become ready')
            time.sleep(.25)
        # Only the deployment administrator creates this synthetic journal/schema.
        sql(f"CREATE ROLE managed_app LOGIN PASSWORD '{app_password}'; CREATE SCHEMA deployment; "
            'CREATE TABLE deployment.journal(version text); '
            "INSERT INTO deployment.journal VALUES ('accepted'); "
            'CREATE TABLE deployment.operations(id integer PRIMARY KEY, value text); '
            'CREATE TABLE deployment.unrelated(secret text);')
        sql('SET ROLE managed_app; SELECT version FROM deployment.journal;', succeeds=False)
        sql('GRANT USAGE ON SCHEMA deployment TO managed_app;')
        sql('SET ROLE managed_app; SELECT version FROM deployment.journal;', succeeds=False)
        sql('GRANT SELECT ON TABLE deployment.journal TO managed_app;')
        assert 'accepted' in sql('SET ROLE managed_app; SELECT version FROM deployment.journal;')
        sql('SET ROLE managed_app; SELECT secret FROM deployment.unrelated;', succeeds=False)
        deployment = ('GRANT USAGE ON SCHEMA deployment TO managed_app; '
                      'GRANT SELECT ON TABLE deployment.journal TO managed_app; '
                      'GRANT SELECT, INSERT, UPDATE ON TABLE deployment.operations TO managed_app;')
        sql(deployment)
        sql(deployment)  # Administrator-owned replay does not create/reset data.
        admission = sql('SELECT current_user, version FROM deployment.journal;', application_login=True)
        assert 'managed_app' in admission and 'accepted' in admission
        sql("INSERT INTO deployment.operations VALUES (1, 'initial'); "
            "UPDATE deployment.operations SET value='updated' WHERE id=1;", application_login=True)
        assert 'updated' in sql('SELECT value FROM deployment.operations WHERE id=1;', application_login=True)
        sql('SELECT secret FROM deployment.unrelated;', succeeds=False, application_login=True)
        sql('CREATE TABLE deployment.runtime_created(id integer);', succeeds=False, application_login=True)
        sql('CREATE SCHEMA runtime_created;', succeeds=False, application_login=True)
        sql('DELETE FROM deployment.operations WHERE id=1;', succeeds=False, application_login=True)
    finally:
        if created:
            run(['rm', '-f', '-v', container])
        (evidence / 'operations.json').write_text(json.dumps(operations, indent=2))
    (evidence / 'result.json').write_text(json.dumps({'status': 'passed', 'image': image,
        'schemaUsageRequired': True, 'journalSelectRequired': True, 'exactRoleReadAdmitted': True,
        'unrelatedTableStillDenied': True, 'cleanupComplete': True,
        'actualApplicationLogin': True, 'idempotentDeploymentReplay': True,
        'applicationTcpReadinessRequired': True,
        'exactOperationInsertUpdateAdmitted': True, 'runtimeCreateDenied': True, 'ungrantedDeleteDenied': True,
        'scope': 'Synthetic deployment guidance; no consumer schema, startup creation or reset.'}, indent=2))
    print('Exact application-role grant regression passed: ' + str(evidence))


if __name__ == '__main__':
    main()
