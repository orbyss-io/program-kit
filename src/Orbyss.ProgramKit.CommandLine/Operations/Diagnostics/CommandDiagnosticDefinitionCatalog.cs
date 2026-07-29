using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Diagnostics;

/// <summary>Stable CLI transport diagnostics not owned by another module.</summary>
public static class CommandDiagnosticDefinitionCatalog
{
    /// <summary>Gets exact CLI and gate-transport definitions.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions
    { get; } =
    [
        Error("PKCLI001", "Invalid finite command invocation"),
        Error("PKCLI002", "Invalid explicit command input"),
        Error("PKCLI003", "Contained internal command failure"),
        Error("PKCLI004", "Command operation unavailable"),
        Error("PKCLI005", "Duplicate command operation registration"),
        Error("PKCLI006", "Invalid capability index"),
        Error("PKCLI007", "Invalid capability bundle"),
        Error("PKCLI008", "Invalid capability initialization"),
        Error("PKCLI009", "Capability setup required"),
        Error("PKCLI010", "Capability unavailable"),
        Error("PKCLI011", "Invalid capability knowledge closure"),
        Error("PKCIM001", "Invalid Console input materialization request"),
        Error("PKCIM002", "Unsafe Console materialization path"),
        Error("PKCIM003", "Consumer Console integration build failed"),
        Error("PKCIM004", "MSBuild reference query failed"),
        Error("PKCIM005", "Invalid managed reference closure"),
        Error("PKCIM006", "Invalid Console integration assembly"),
        Error("PKCIM007", "Console materialization ownership conflict"),
        Error("PKCIM008", "Console materialization transaction failed"),
        Error("PKCIM009", "Program Kit authoring workspace rejected"),
        Error("PKCG070", "C# gate verification failed"),
        Error("PKCG071", "C# gate operation failed"),
        Error("PKCG072", "C# gate command input failed"),
    ];

    private static ProgramKitDiagnosticDefinition Error(
        string id,
        string title) =>
        new(id, ProgramKitDiagnosticSeverity.Error, title);
}
