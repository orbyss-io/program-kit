namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Declared lifetime of the consuming service.</summary>
public enum DotNetServiceLifetime
{
    /// <summary>Singleton consumer.</summary>
    Singleton,
    /// <summary>Scoped consumer.</summary>
    Scoped,
    /// <summary>Transient consumer.</summary>
    Transient,
}
