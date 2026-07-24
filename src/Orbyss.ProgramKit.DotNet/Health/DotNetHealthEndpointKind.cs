namespace Orbyss.ProgramKit.DotNet.Health;

/// <summary>Supported health endpoint meanings.</summary>
public enum DotNetHealthEndpointKind
{
    /// <summary>Process-only liveness.</summary>
    Liveness,

    /// <summary>Dependency and acceptance readiness.</summary>
    Readiness,

    /// <summary>Startup completion state.</summary>
    Startup,
}
