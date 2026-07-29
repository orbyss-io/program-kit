using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Diagnostics;

/// <summary>Finite ownership and remediation metadata for one diagnostic.</summary>
public sealed record DiagnosticExplanation(
    string Id,
    string Classification,
    string Owner,
    string Meaning,
    string AffectedContract,
    string ExpectedEvidence,
    string LikelyCauses,
    string BoundedRemediation,
    string StopCondition,
    ImmutableArray<string> RelatedCommands,
    ImmutableArray<string> RelatedSchemas);
