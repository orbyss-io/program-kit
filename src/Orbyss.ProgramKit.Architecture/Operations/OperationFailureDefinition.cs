using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>One stable failure code and its caller-visible meaning.</summary>
public sealed record OperationFailureDefinition(
    ProgramKitIdentifier Identity,
    string Code,
    string Meaning,
    bool IsRetryable,
    ArtifactReference? DetailsContract);
