namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Finite ownership lifetimes for a resolved capability.</summary>
public enum SecretResultLifetime
{
    /// <summary>No lifetime was selected.</summary>
    Unspecified,
    /// <summary>The capability is valid only for one bounded resolution lease.</summary>
    ResolutionLease,
    /// <summary>The consumer owns the capability until that consumer is disposed.</summary>
    Consumer,
    /// <summary>The host owns the capability until host shutdown.</summary>
    Host,
    /// <summary>The provider owns renewal and lifetime behind a stable capability.</summary>
    ProviderManaged,
}
