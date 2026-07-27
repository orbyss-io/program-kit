using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>
/// Records one handler execution without claiming a domain-specific outcome.
/// </summary>
/// <param name="Handler">The exact handler registration revision.</param>
/// <param name="Status">The infrastructure execution status.</param>
/// <param name="Diagnostic">The stable failure diagnostic, if any.</param>
/// <param name="Failure">The in-process exception, if any.</param>
public sealed record DomainContributionHandlerExecution(
    ArtifactReference Handler,
    DomainContributionHandlerExecutionStatus Status,
    ProgramKitDiagnostic? Diagnostic,
    Exception? Failure);
