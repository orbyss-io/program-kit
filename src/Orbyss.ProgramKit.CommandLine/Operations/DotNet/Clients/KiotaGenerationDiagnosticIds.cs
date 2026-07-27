namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Stable diagnostics for pinned foreign-client generation.</summary>
public static class KiotaGenerationDiagnosticIds
{
    /// <summary>The local input or its references are invalid.</summary>
    public const string InvalidInput = "PKKIO001";

    /// <summary>The exact tool manifest does not match the reviewed selection.</summary>
    public const string InvalidToolManifest = "PKKIO002";

    /// <summary>The selected Kiota process failed or reported a different version.</summary>
    public const string ToolFailure = "PKKIO003";

    /// <summary>The explicit output or staging path is unsafe.</summary>
    public const string UnsafeOutput = "PKKIO004";

    /// <summary>The generated Kiota lock does not bind the exact input and options.</summary>
    public const string LockMismatch = "PKKIO005";

    /// <summary>The generated tree is empty, partial, or contains a reserved path.</summary>
    public const string InvalidOutput = "PKKIO006";

    /// <summary>The exact Kiota package archive or reviewed entry bytes differ.</summary>
    public const string InvalidToolPackage = "PKKIO007";
}
