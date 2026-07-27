using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>
/// Exact inputs for one finite compiler-backed verification. No executable or
/// caller-supplied argument surface is part of this contract.
/// </summary>
public sealed record CSharpGateVerificationRequest(
    string WorkingDirectory,
    string ProjectPath,
    CSharpGateCommand Command,
    CSharpGateImplementationBoundary Boundary,
    CSharpGateVerificationProfileKind VerificationProfile,
    SemanticVersion DotNetSdkVersion,
    string EvidenceOutputPath,
    ImmutableArray<string> ParticipationReceiptPaths,
    ImmutableArray<string> ExceptionUseReceiptPaths,
    ImmutableArray<string> PackagePaths,
    int MaximumCapturedOutputBytes,
    int PerformanceBudgetMilliseconds);
