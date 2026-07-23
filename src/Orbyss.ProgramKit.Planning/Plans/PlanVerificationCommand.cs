using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Defines a process invocation as an executable plus already-tokenized arguments.</summary>
public sealed record PlanVerificationCommand(
    string Executable,
    ImmutableArray<string> Arguments,
    string WorkingDirectory,
    string ExpectedObservation);
