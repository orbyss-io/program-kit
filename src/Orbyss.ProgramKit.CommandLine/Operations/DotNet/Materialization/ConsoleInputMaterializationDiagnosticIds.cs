namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Stable diagnostics for Console input materialization.</summary>
public static class ConsoleInputMaterializationDiagnosticIds
{
    /// <summary>The semantic materialization request is invalid.</summary>
    public const string InvalidRequest = "PKCIM001";

    /// <summary>An explicit workspace or output path is unsafe.</summary>
    public const string UnsafePath = "PKCIM002";

    /// <summary>The explicitly authorized consumer build failed.</summary>
    public const string BuildFailed = "PKCIM003";

    /// <summary>The exact MSBuild reference query failed.</summary>
    public const string ReferenceQueryFailed = "PKCIM004";

    /// <summary>The evaluated managed reference closure is invalid.</summary>
    public const string InvalidReferenceClosure = "PKCIM005";

    /// <summary>The selected Console integration assembly seam is invalid.</summary>
    public const string InvalidIntegrationAssembly = "PKCIM006";

    /// <summary>Existing materialized output is modified or unowned.</summary>
    public const string OutputOwnershipConflict = "PKCIM007";

    /// <summary>The materialization transaction could not complete safely.</summary>
    public const string TransactionFailed = "PKCIM008";

    /// <summary>Program Kit's authoring workspace rejected product activation.</summary>
    public const string AuthoringWorkspaceRejected = "PKCIM009";
}
