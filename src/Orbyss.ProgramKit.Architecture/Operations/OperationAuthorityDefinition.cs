using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The authority required to invoke and execute an operation.</summary>
public sealed record OperationAuthorityDefinition(
    bool IsRequired,
    ImmutableArray<ProgramKitIdentifier> RequirementIds,
    string EvaluationPoint,
    string DenialSemantics);
