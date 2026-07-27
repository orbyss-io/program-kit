using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The signals and correlation behavior exposed by an operation.</summary>
public sealed record OperationObservabilityDefinition(
    ImmutableArray<string> Signals,
    string CorrelationSemantics,
    string SensitiveDataPolicy);
