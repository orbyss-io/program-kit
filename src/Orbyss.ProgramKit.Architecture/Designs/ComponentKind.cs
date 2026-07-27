using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>The architectural role of a component.</summary>
public enum ComponentKind
{
    /// <summary>A dependency-light domain contract and semantic model owner.</summary>
    DomainCore,

    /// <summary>An activatable user-visible capability.</summary>
    Feature,

    /// <summary>A replaceable implementation of an owned contract.</summary>
    Provider,

    /// <summary>A non-activatable, single-owner implementation helper.</summary>
    FocusedHelper,

    /// <summary>An explicit translation boundary between owned sides.</summary>
    Bridge,

    /// <summary>A composition root.</summary>
    Host,

    /// <summary>An authoritative design-time input.</summary>
    DesignTimeSource,

    /// <summary>A generated or queried read-only view.</summary>
    ReadProjection,

    /// <summary>An output evaluated against an owned specification.</summary>
    EvaluatedArtifact
}
