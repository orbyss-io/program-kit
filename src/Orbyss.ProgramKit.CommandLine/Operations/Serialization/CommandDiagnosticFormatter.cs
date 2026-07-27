using System.Collections.Immutable;
using System.Text;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Canonical JSON and stable invariant-text diagnostic formatter.</summary>
public sealed class CommandDiagnosticFormatter : ICommandDiagnosticFormatter
{
    private readonly IProgramKitJsonSerializer serializer;

    /// <summary>Initializes the formatter with the exact selected serializer.</summary>
    public CommandDiagnosticFormatter(IProgramKitJsonSerializer serializer)
    {
        this.serializer = serializer ?? throw new ArgumentNullException(nameof(serializer));
    }

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Format(
        string representation,
        CommandExitCode exitCode,
        ImmutableArray<CommandDiagnostic> diagnostics)
    {
        var ordered = diagnostics
            .OrderBy(static diagnostic => diagnostic.Id, StringComparer.Ordinal)
            .ThenBy(static diagnostic => diagnostic.Path, StringComparer.Ordinal)
            .ThenBy(static diagnostic => diagnostic.Message, StringComparer.Ordinal)
            .ToImmutableArray();
        if (string.Equals(representation, "json", StringComparison.Ordinal))
        {
            return serializer.Write(
                new CommandDiagnosticEnvelope(ordered, (int)exitCode),
                CommandLineJsonProfiles.Diagnostics.Reference,
                JsonSerializationLimits.Default).ToArray();
        }

        var text = new StringBuilder();
        foreach (var diagnostic in ordered)
        {
            text.Append(diagnostic.Id);
            text.Append(' ');
            text.Append(diagnostic.Severity);
            text.Append(' ');
            text.Append(diagnostic.Path);
            text.Append(": ");
            text.AppendLine(diagnostic.Message);
        }

        return Encoding.UTF8.GetBytes(text.ToString());
    }
}
