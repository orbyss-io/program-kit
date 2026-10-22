"""Compiled fictional dispatch/accounting cancellation through maintained evaluation.

No provider transport, account, consumer source, worker or product acceptance is used.
"""
from pathlib import Path
import json
import subprocess
import sys
import uuid
from contextlib import nullcontext
from unittest.mock import patch
from coding_evaluation_fixture import fictional_claims

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from dotnet_adapter import bootstrap
bootstrap()
import coding_context as coding
import toolkit_verification as toolkit

PROGRAM = '''using System;
using System.Threading;
using System.Threading.Tasks;

/// <summary>Exercises fictional acquired-operation cleanup across accounting cancellation.</summary>
internal static class Program
{
    private static readonly bool ProtectedAccounting = false;

    private static async Task<int> Main()
    {
        var normal = await Run(false);
        if (!normal.Deleted || normal.Uncertain || normal.OperationId != "fictional-operation")
            throw new InvalidOperationException("Valid control failed before the adverse assertion.");
        Console.WriteLine("VALID_CONTROL_PASSED");
        var canceled = await Run(true);
        if (!canceled.Deleted || !canceled.Uncertain || canceled.OperationId != "fictional-operation")
        {
            Console.WriteLine("ACCOUNTING_CANCELLATION_LOST_CLEANUP");
            return 42;
        }
        Console.WriteLine("CANCELED_ACCOUNTING_CLEANED_AND_UNCERTAINTY_RETAINED");
        return 0;
    }

    private static async Task<Observation> Run(bool cancelAccounting)
    {
        var observation = new Observation();
        using var cancellation = new CancellationTokenSource();
        try
        {
            // Fictional dispatch has completed: the locator exists before accounting.
            observation.OperationId = "fictional-operation";
            if (cancelAccounting)
                cancellation.Cancel();
            if (!ProtectedAccounting)
                await RecordSubmitted(cancellation.Token);
            try
            {
                if (ProtectedAccounting)
                    await RecordSubmitted(cancellation.Token);
            }
            finally
            {
                observation.Deleted = true;
            }
        }
        catch (OperationCanceledException)
        {
            // No retry/redispatch: preserve the known locator and uncertain accounting.
            observation.Uncertain = true;
        }
        return observation;
    }

    private static async Task RecordSubmitted(CancellationToken token)
    {
        await Task.Yield();
        token.ThrowIfCancellationRequested();
    }
}
'''
OBSERVATION = '''/// <summary>Independent fake transport/accounting observation.</summary>
internal sealed class Observation
{
    internal string? OperationId;
    internal bool Deleted;
    internal bool Uncertain;
}
'''


def build(root, label):
    process = subprocess.run(['dotnet', 'build', str(root / 'Boundary.csproj'), '--nologo'], cwd=root,
                             capture_output=True, text=True, encoding='utf-8', timeout=90)
    (root / (label + '.build.log')).write_text(process.stdout + process.stderr, encoding='utf-8')
    if process.returncode:
        raise AssertionError('Compiler/setup failure cannot count as adverse rejection: ' + process.stdout + process.stderr)


def main():
    retained = ROOT / 'artifacts/coding-adverse-boundary' / uuid.uuid4().hex
    retained.mkdir(parents=True)
    with nullcontext(retained) as name:
        root = Path(name)
        feature = root / 'specs/001-boundary'; feature.mkdir(parents=True)
        (feature / 'tasks.md').write_text('- [ ] T001 Repair the acquired remote locator cleanup boundary.\n')
        (root / 'Boundary.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework>'
            '<OutputType>Exe</OutputType><Nullable>enable</Nullable></PropertyGroup></Project>')
        (root / 'Program.cs').write_text(PROGRAM)
        (root / 'source.before.txt').write_text(PROGRAM)
        (root / 'Observation.cs').write_text(OBSERVATION)
        (root / 'review.md').write_text('Fictional independent inspection: cleanup begins before the accounting await after acquisition; cancellation retains locator/uncertainty. No provider deletion claim.')
        (root / 'check.py').write_text('import subprocess,sys\nr=subprocess.run(["dotnet","run","--project","Boundary.csproj","--no-build","--no-restore"],capture_output=True,text=True)\n'
            'print(r.stdout); print(r.stderr,file=sys.stderr)\nassert "VALID_CONTROL_PASSED" in r.stdout\n'
            'assert r.returncode == 0 and "CANCELED_ACCOUNTING_CLEANED_AND_UNCERTAINTY_RETAINED" in r.stdout, "compiled adverse cleanup oracle failed"\n')
        (root / 'eng').mkdir()
        config = {'schemaVersion': 1, 'toolkitChecks': [{'id': 'accounting-cleanup', 'script': 'check.py', 'arguments': [],
            'inputs': ['check.py', 'Program.cs', 'Observation.cs', 'Boundary.csproj'], 'timeoutSeconds': 30}]}
        (root / 'eng/verification.json').write_text(json.dumps(config))
        declarations = toolkit.declarations(root, config)
        value = {'scope': {'taskIds': ['T001']}, 'inputs': [coding.source(root, root / p) for p in ('Program.cs', 'Observation.cs', 'Boundary.csproj')],
                 'projects': [], 'frontendProjects': [], 'profiles': [], 'patternsContext': {}, 'architecture': {},
                 'nativeContext': {'applicable': False, 'configuration': 'Debug', 'framework': None},
                 'evaluation': {'duties': [{'rule': 'fictional.acquired-operation-cleanup', 'fingerprint': 'finite-cleanup-v1',
                     'required': True, 'technicalRequired': True, 'owner': 'fictional boundary owner', 'independentReviewRequired': True}]}}
        claims = fictional_claims(value, 'Program.cs', [{'kind': 'toolkit', 'id': 'accounting-cleanup'}])
        build(root, 'broken-source')
        # Independently inspect the intended compiled negative marker before toolkit rejection.
        adverse = subprocess.run(['dotnet', 'run', '--project', 'Boundary.csproj', '--no-build', '--no-restore'], cwd=root,
                                 capture_output=True, text=True, timeout=30)
        (root / 'broken-source.oracle.log').write_text(adverse.stdout + adverse.stderr)
        assert adverse.returncode == 42 and 'VALID_CONTROL_PASSED' in adverse.stdout and 'ACCOUNTING_CANCELLATION_LOST_CLEANUP' in adverse.stdout
        try:
            toolkit.execute(root, ['accounting-cleanup'], declarations)
            raise AssertionError('Broken behavior unexpectedly passed the maintained execution owner')
        except ValueError:
            pass
        try:
            coding.bind_evaluation(root, feature, value, claims)
            raise AssertionError('Failed compiled behavior unexpectedly closed evaluation')
        except ValueError:
            pass
        (root / 'Program.cs').write_text(PROGRAM.replace('ProtectedAccounting = false', 'ProtectedAccounting = true'))
        build(root, 'repaired-source')
        toolkit.execute(root, ['accounting-cleanup'], declarations)
        value['inputs'][0] = coding.source(root, root / 'Program.cs')
        records = coding.bind_evaluation(root, feature, value, claims)
        coding.require_evaluated(root, feature, value, records)
        coding.require_independent_review(value, records)
        print('BUILD_SUCCEEDED_BEFORE_BEHAVIOR; compiled cancellation negative blocked evaluation; protected accounting/cleanup retained locator and uncertainty with current independent authored findings. Retained: ' + str(root))


if __name__ == '__main__':
    main()
