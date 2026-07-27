using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations;

/// <summary>Transport-neutral result returned by one command operation adapter.</summary>
public sealed record CommandOperationResult(
    CommandExitCode ExitCode,
    ReadOnlyMemory<byte> StandardOutput,
    ImmutableArray<CommandDiagnostic> Diagnostics)
{
    /// <summary>Creates a successful result with optional standard output.</summary>
    public static CommandOperationResult Success(ReadOnlyMemory<byte> standardOutput = default) =>
        new(CommandExitCode.Success, standardOutput, []);
}
