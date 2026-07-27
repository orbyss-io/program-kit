using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>The terminal disposition assigned to an impacted version node.</summary>
public enum MigrationTerminalDisposition
{
    /// <summary>The node is unaffected and carries explicit proof.</summary>
    UnaffectedWithProof,

    /// <summary>The node is compatible after all declared actions complete.</summary>
    CompatibleAfterActions,

    /// <summary>The node requires a major upgrade.</summary>
    MajorUpgrade,

    /// <summary>The node must be redesigned.</summary>
    Redesign,

    /// <summary>The node requires human semantic review.</summary>
    ManualReview,

    /// <summary>The migration cannot currently proceed.</summary>
    Blocked,
}
