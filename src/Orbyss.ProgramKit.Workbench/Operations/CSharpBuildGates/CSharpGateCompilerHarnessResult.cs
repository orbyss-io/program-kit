using System.Collections.Immutable;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>Typed outcome from one finite compiler-backed verification.</summary>
public sealed record CSharpGateCompilerHarnessResult(
    bool Succeeded,
    int ExitCode,
    CSharpGateEvidenceLayer? FailureLayer,
    string OutputDigest,
    ImmutableArray<string> ParticipationReceiptDigests,
    ImmutableArray<string> ExceptionUseReceiptDigests,
    ImmutableArray<string> PackageDigests);
