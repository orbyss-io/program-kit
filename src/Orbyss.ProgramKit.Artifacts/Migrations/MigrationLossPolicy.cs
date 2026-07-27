using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>The declared data-loss behavior of a migration.</summary>
public enum MigrationLossPolicy
{
    /// <summary>The migration preserves all represented meaning.</summary>
    Lossless,

    /// <summary>Any loss is explicit, reviewed, and described by preconditions.</summary>
    ExplicitlyLossy,

    /// <summary>The migration must fail rather than lose represented meaning.</summary>
    RejectLoss,
}
