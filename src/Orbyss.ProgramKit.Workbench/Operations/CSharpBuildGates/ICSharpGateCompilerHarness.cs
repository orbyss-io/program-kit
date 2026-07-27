namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>Executes only the finite pinned C# gate verification templates.</summary>
public interface ICSharpGateCompilerHarness
{
    /// <summary>Runs one exact verification and atomically emits evidence.</summary>
    ValueTask<CSharpGateCompilerHarnessResult> VerifyAsync(
        CSharpGateVerificationRequest request,
        CancellationToken cancellationToken);
}
