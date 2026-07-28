namespace Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

/// <summary>The immutable diagnostic catalog owned by Workbench operations.</summary>
public static class WorkbenchDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable diagnostic identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
    [
        Error(WorkbenchDiagnosticIds.InvalidVersionMapBuild, "Invalid Version Map build"),
        Error(WorkbenchDiagnosticIds.InvalidMigrationRequest, "Invalid migration request"),
        Error(
            WorkbenchDiagnosticIds.MigrationClosureLimitExceeded,
            "Migration closure limit exceeded"),
        Error(
            WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest,
            "Invalid version-intent inventory request"),
        Error(
            WorkbenchDiagnosticIds.InvalidAlphaVersionProgressionProposal,
            "Invalid alpha version progression proposal"),
        Error(WorkbenchDiagnosticIds.InvalidExtensionSelection, "Invalid extension selection"),
        Error(WorkbenchDiagnosticIds.SchemaValidationFailed, "Schema validation failed"),
        Error(WorkbenchDiagnosticIds.StaleProjection, "Stale generated projection"),
        Error(WorkbenchDiagnosticIds.OperationLimitExceeded, "Operation limit exceeded"),
        Error(WorkbenchDiagnosticIds.OutputPublicationFailed, "Output publication failed"),
        Error(WorkbenchDiagnosticIds.OutputRollbackFailed, "Output rollback failed"),
        Error(WorkbenchDiagnosticIds.OperationCancelled, "Operation cancelled"),
    ];

    private static ProgramKitDiagnosticDefinition Error(string id, string title) =>
        new(id, ProgramKitDiagnosticSeverity.Error, title);
}
