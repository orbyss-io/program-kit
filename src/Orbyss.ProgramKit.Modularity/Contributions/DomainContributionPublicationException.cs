using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>
/// Reports fail-fast handler failure while preserving ordered partial
/// publication observations and the original exception.
/// </summary>
public sealed class DomainContributionPublicationException : Exception
{
    /// <summary>Initializes one fail-fast publication exception.</summary>
    /// <param name="result">The partial result ending with the failed handler.</param>
    /// <param name="handler">The failed exact handler registration.</param>
    /// <param name="diagnostic">The stable handler failure diagnostic.</param>
    /// <param name="innerException">The original handler exception.</param>
    public DomainContributionPublicationException(
        DomainContributionPublicationResult result,
        ArtifactReference handler,
        ProgramKitDiagnostic diagnostic,
        Exception innerException)
        : base("Domain-contribution publication stopped after a handler failure.", innerException)
    {
        ArgumentNullException.ThrowIfNull(result);
        ArgumentNullException.ThrowIfNull(handler);
        ArgumentNullException.ThrowIfNull(diagnostic);
        Result = result;
        Handler = handler;
        Diagnostic = diagnostic;
    }

    /// <summary>Gets the ordered partial result ending with the failed handler.</summary>
    public DomainContributionPublicationResult Result { get; }

    /// <summary>Gets the exact failed handler registration.</summary>
    public ArtifactReference Handler { get; }

    /// <summary>Gets the stable failure diagnostic.</summary>
    public ProgramKitDiagnostic Diagnostic { get; }
}
