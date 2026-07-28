using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Refresh;

internal sealed class RefreshTestCompilerHarness : ICSharpGateCompilerHarness
{
    internal int CallCount { get; private set; }

    public ValueTask<CSharpGateCompilerHarnessResult> VerifyAsync(
        CSharpGateVerificationRequest request,
        CancellationToken cancellationToken)
    {
        CallCount++;
        return ValueTask.FromResult(
            new CSharpGateCompilerHarnessResult(
                true,
                0,
                null,
                "test",
                [],
                [],
                []));
    }
}
