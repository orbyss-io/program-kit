using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Whether a version dependency crosses a public consumer boundary.</summary>
public enum DependencyExposure
{
    /// <summary>The dependency is an implementation detail.</summary>
    Private,

    /// <summary>The dependency is exposed to consumers.</summary>
    Public,
}
