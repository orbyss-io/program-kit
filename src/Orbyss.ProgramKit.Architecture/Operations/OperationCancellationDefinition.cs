using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>How an operation accepts, propagates, and observes cancellation.</summary>
public sealed record OperationCancellationDefinition(
    bool IsSupported,
    string AcceptanceSemantics,
    string PropagationSemantics,
    string CompletionRaceSemantics);
