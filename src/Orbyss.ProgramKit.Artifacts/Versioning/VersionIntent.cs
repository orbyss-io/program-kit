namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Declares the semantic role of one version-bearing value.</summary>
public enum VersionIntent
{
    /// <summary>One coordinated release value for packaged first-party outputs.</summary>
    ProductRelease,

    /// <summary>One immutable revision of a Program Kit-owned governed identity.</summary>
    OwnedArtifactRevision,

    /// <summary>An exact version selected from an upstream or external owner.</summary>
    ExternalSelection,

    /// <summary>An immutable version carried by approval, closure, or receipt evidence.</summary>
    HistoricalEvidenceRevision,

    /// <summary>An explicitly synthetic version used only by a test identity.</summary>
    FixtureRevision,
}
