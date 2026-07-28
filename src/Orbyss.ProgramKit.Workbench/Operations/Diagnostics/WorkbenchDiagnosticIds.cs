namespace Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

/// <summary>Stable diagnostics emitted by deterministic Workbench operations.</summary>
public static class WorkbenchDiagnosticIds
{
    /// <summary>An explicit extension selection is invalid or unavailable.</summary>
    public const string InvalidExtensionSelection = "PKWB001";

    /// <summary>JSON Schema validation could not be completed or failed.</summary>
    public const string SchemaValidationFailed = "PKWB002";

    /// <summary>A generated projection no longer binds its current inputs.</summary>
    public const string StaleProjection = "PKWB003";

    /// <summary>A bounded operation exceeded a declared limit.</summary>
    public const string OperationLimitExceeded = "PKWB004";

    /// <summary>Transactional output publication failed.</summary>
    public const string OutputPublicationFailed = "PKWB005";

    /// <summary>Private staging cleanup could not be confirmed after failure.</summary>
    public const string OutputRollbackFailed = "PKWB006";

    /// <summary>An operation was cancelled before successful publication.</summary>
    public const string OperationCancelled = "PKWB007";

    /// <summary>A Version Map build request is incomplete or contradictory.</summary>
    public const string InvalidVersionMapBuild = "PKVER001";

    /// <summary>A migration request is incomplete or has unknown compatibility.</summary>
    public const string InvalidMigrationRequest = "PKVER002";

    /// <summary>Migration reverse closure exceeded its explicit limits.</summary>
    public const string MigrationClosureLimitExceeded = "PKVER003";

    /// <summary>A bounded version-intent inventory request is incomplete or inconsistent.</summary>
    public const string InvalidVersionIntentInventoryRequest = "PKVER004";

    /// <summary>An explicit alpha progression proposal does not satisfy its policy.</summary>
    public const string InvalidAlphaVersionProgressionProposal = "PKVER005";
}
