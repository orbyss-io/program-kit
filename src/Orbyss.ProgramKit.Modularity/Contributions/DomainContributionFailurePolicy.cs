namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Controls whether publication stops or continues after a handler failure.</summary>
public enum DomainContributionFailurePolicy
{
    /// <summary>Stop and throw after the first failed handler.</summary>
    FailFast,

    /// <summary>Run remaining handlers and return all execution observations.</summary>
    Continue,
}
