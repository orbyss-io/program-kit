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
}
