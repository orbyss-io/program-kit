namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Classifies one infrastructure-level handler execution observation.</summary>
public enum DomainContributionHandlerExecutionStatus
{
    /// <summary>The handler completed without throwing.</summary>
    Succeeded,

    /// <summary>The handler threw and publication policy captured the failure.</summary>
    Failed,
}
