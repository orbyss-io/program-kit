"""Postpublication explicit-tag public initializer and installed checks, no agents.

This is a separate delivery-surface check. It runs only after approved publication,
uses the actual public URLs, and never rebuilds or changes the published payload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.request

from owned_fixture import FixtureDirectory
from validate_package_smoke import extract


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from live.v2.supervisor import run_supervised
from release_candidate import policy, read, require, source, verify_payload, write


class PublicDelivery:
    def __init__(self, diagnostics, budget=120):
        self.diagnostics = diagnostics
        self.started = time.monotonic()
        self.budget = budget
        self.operations = []
        diagnostics.mkdir(parents=True, exist_ok=True)

    def remaining(self):
        remaining = self.budget - (time.monotonic() - self.started)
        require(remaining > 0, 'Public installation/upgrade exceeded its runtime budget')
        return remaining

    def run(self, name, command, cwd):
        started = time.monotonic()
        print('Public delivery: ' + name, flush=True)
        output = self.diagnostics / name
        result = run_supervised([str(x) for x in command], cwd=cwd, environment=os.environ.copy(),
                                evidence_directory=output, timeout_seconds=max(1,int(self.remaining())),
                                secrets=[os.environ[key] for key in ('GH_TOKEN','GITHUB_TOKEN') if os.environ.get(key)])
        self.operations.append({'name':name,'seconds':time.monotonic()-started,'exitCode':result.exitCode,
                                'timedOut':result.timedOut,'cleanupComplete':result.cleanupComplete,'logsDrained':result.logsDrained})
        require(result.exitCode == 0 and not result.timedOut and result.cleanupComplete and result.logsDrained,
                f'Public {name} failed or timed out; inspect retained diagnostics')
        self.remaining()
        return (output / result.stdout.path).read_text(encoding='utf-8')

    def download(self, url, destination, expected):
        require(url.startswith('https://github.com/' + policy()['repository'] + '/releases/download/'),
                'Public package URL must belong to this repository release')
        with urllib.request.urlopen(url, timeout=min(30,self.remaining())) as response:
            data = response.read(expected['size'] + 1)
        require(len(data) == expected['size'] and hashlib.sha256(data).hexdigest() == expected['sha256'],
                'Public download differs from inspected package: ' + destination.name)
        destination.write_bytes(data)
        self.remaining()


def installed_versions(project):
    import yaml
    result = {}
    for kind, identity in (('extensions','program-kit-governance'), ('extensions','program-kit-building-blocks'),
                           ('extensions','program-kit-dotnet'), ('presets','program-kit-governance-preset')):
        filename = 'extension.yml' if kind == 'extensions' else 'preset.yml'
        value = yaml.safe_load((project / '.specify' / kind / identity / filename).read_text())
        result[identity] = value['extension' if kind == 'extensions' else 'preset']['version']
    return result


def journey(session, workspace, promotion):
    version = promotion['source']['version']
    tag = 'v' + version
    by_name = {r['name']:r for r in promotion['assets']}
    base = 'https://github.com/' + policy()['repository'] + '/releases/download/' + tag + '/'
    clean = workspace / 'public clean consumer'
    clean.mkdir()
    initializer = f'Initialize-ProgramKit-{version}.sh'
    session.download(base+initializer,clean/initializer,by_name[initializer])
    session.run('initialize-git',['git','init'],clean)
    # No agent-context variables are removed. The real initializer preserves its
    # user-terminal boundary; CI is a non-agent process with actual prerequisites.
    session.run('public-initializer',['bash',clean/initializer,'copilot'],clean)
    require(set(installed_versions(clean).values()) == {version}, 'Public initializer installed incoherent component versions')
    governance = clean/'.specify/extensions/program-kit-governance/scripts/governance_state.py'
    session.run('public-installation-check',[sys.executable,governance,'validate-installation'],clean)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True,help='Already inspected promotion directory')
    parser.add_argument('--budget-seconds',type=int,default=120)
    args = parser.parse_args()
    require(not any(os.environ.get(key) for key in ('CODEX_SESSION_ID','CODEX_THREAD_ID','CODEX_INTERNAL_ORIGINATOR_OVERRIDE')),
            'Run public delivery only in release CI or a normal human-owned terminal; never strip agent-context variables')
    require(args.budget_seconds > 0,'Public delivery budget must be positive')
    directory = args.directory.resolve()
    promotion = read(directory/'promotion.json')
    require(promotion['source'] == source(),'Public delivery source differs from inspected candidate')
    verify_payload(read(directory/'payload/candidate-payload.json'),directory/'payload',source())
    diagnostics = ROOT/'artifacts/public-delivery'
    session = PublicDelivery(diagnostics,args.budget_seconds)
    outcome = 'failed'
    try:
        with FixtureDirectory() as temporary:
            journey(session,Path(temporary),promotion)
        outcome = 'passed'
    finally:
        write(diagnostics/'result.json',{'status':outcome,'source':promotion['source'],'seconds':time.monotonic()-session.started,
              'budgetSeconds':args.budget_seconds,'operations':session.operations,
              'scope':'explicit-tag public initializer and installed checks; 0.x re-onboarding is not semantic migration; no application or agent acceptance'})
    print('Public explicit-tag installation passed.')
    return 0


if __name__ == '__main__': raise SystemExit(main())
