using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

/// <summary>A receipt emitted for every accepted temporary non-execution.</summary>
public sealed record CSharpGateExceptionUseReceipt(
    ProgramKitIdentifier Identity,
    ArtifactReference Exception,
    Sha256Digest EvaluatedConditionInputsDigest,
    bool ConditionMatched,
    Sha256Digest CompilationDigest,
    ImmutableArray<ArtifactReference> CompensatingVerification,
    DateTimeOffset EvaluatedAt,
    TimeSpan? RemainingLifetime,
    int? RemainingUses);
