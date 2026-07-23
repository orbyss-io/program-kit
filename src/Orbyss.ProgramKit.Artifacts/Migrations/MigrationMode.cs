using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>The mechanism used to move from a source revision to a target revision.</summary>
public enum MigrationMode
{
    /// <summary>Transforms a durable artifact into a new artifact.</summary>
    ArtifactTransform,

    /// <summary>Transforms configuration into a new configuration revision.</summary>
    ConfigurationTransform,

    /// <summary>Provides source-level migration guidance.</summary>
    SourceGuidance,

    /// <summary>Regenerates an output from upgraded canonical inputs.</summary>
    Regenerate,

    /// <summary>Upgrades an exact package selection.</summary>
    PackageUpgrade,

    /// <summary>Temporarily adapts incompatible runtime revisions.</summary>
    RuntimeAdapter,
}
