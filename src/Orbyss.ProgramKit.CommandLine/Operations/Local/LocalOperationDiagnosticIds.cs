namespace Orbyss.ProgramKit.CommandLine.Operations.Local;

/// <summary>Stable package preparation and local publish diagnostics.</summary>
public static class LocalOperationDiagnosticIds
{
    /// <summary>An explicit workspace-package manifest is invalid.</summary>
    public const string InvalidWorkspaceManifest = "PKPUB001";

    /// <summary>A package preparation process failed.</summary>
    public const string PackagePreparationFailed = "PKPUB002";

    /// <summary>A prepared package differs from its exact selection.</summary>
    public const string PackageMismatch = "PKPUB003";

    /// <summary>A local package-root manifest or package bytes are invalid.</summary>
    public const string InvalidPackageRoot = "PKPUB004";

    /// <summary>A selected host or its lock does not match the publish request.</summary>
    public const string HostSelectionMismatch = "PKPUB005";

    /// <summary>The isolated restore closure is not exactly approved.</summary>
    public const string RestoreClosureMismatch = "PKPUB006";

    /// <summary>The isolated restore or publish process failed.</summary>
    public const string PublishProcessFailed = "PKPUB007";

    /// <summary>An output path escapes, collides, or is otherwise unsafe.</summary>
    public const string UnsafeOutput = "PKPUB008";
}
