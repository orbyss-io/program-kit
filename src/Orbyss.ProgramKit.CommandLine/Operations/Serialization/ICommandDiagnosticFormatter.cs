using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Formats stable diagnostics for one selected script representation.</summary>
public interface ICommandDiagnosticFormatter
{
    /// <summary>Formats diagnostics as exact UTF-8 bytes.</summary>
    ReadOnlyMemory<byte> Format(
        string representation,
        CommandExitCode exitCode,
        ImmutableArray<CommandDiagnostic> diagnostics);
}
