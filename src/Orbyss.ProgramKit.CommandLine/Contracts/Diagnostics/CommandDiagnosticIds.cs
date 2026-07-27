namespace Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

/// <summary>Stable PKCLI diagnostic identifiers.</summary>
public static class CommandDiagnosticIds
{
    /// <summary>The command grammar was not satisfied.</summary>
    public const string InvalidInvocation = "PKCLI001";

    /// <summary>An explicit input could not be read or resolved.</summary>
    public const string InvalidInput = "PKCLI002";

    /// <summary>An unexpected internal failure was contained.</summary>
    public const string InternalFailure = "PKCLI003";

    /// <summary>The command has no explicitly registered operation adapter.</summary>
    public const string OperationUnavailable = "PKCLI004";

    /// <summary>An exact command operation registration was duplicated.</summary>
    public const string DuplicateOperation = "PKCLI005";

    /// <summary>The canonical capability index cannot be projected safely.</summary>
    public const string InvalidCapabilityIndex = "PKCLI006";

    /// <summary>The capability bundle differs from its exact content allow-list.</summary>
    public const string InvalidCapabilityBundle = "PKCLI007";

    /// <summary>Provider capability initialization is unsafe or inconsistent.</summary>
    public const string InvalidCapabilityInitialization = "PKCLI008";
}
