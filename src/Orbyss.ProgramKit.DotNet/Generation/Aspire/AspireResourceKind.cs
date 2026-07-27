namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>Finite resource kinds supported by the reviewed AppHost projection.</summary>
public enum AspireResourceKind
{
    /// <summary>No resource kind was selected.</summary>
    Unspecified,
    /// <summary>An explicit .NET project resource.</summary>
    Project,
    /// <summary>An explicit local executable resource.</summary>
    Executable,
    /// <summary>An exact digest-pinned container resource.</summary>
    Container,
}
