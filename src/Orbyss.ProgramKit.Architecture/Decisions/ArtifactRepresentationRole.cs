using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>The representation role selected by question 7.</summary>
public enum ArtifactRepresentationRole
{
    /// <summary>The artifact is the authoritative representation.</summary>
    Canonical,

    /// <summary>The artifact is derived from a separately identified canonical artifact.</summary>
    Projection,

    /// <summary>The artifact exists only within a declared transient boundary.</summary>
    Ephemeral
}
