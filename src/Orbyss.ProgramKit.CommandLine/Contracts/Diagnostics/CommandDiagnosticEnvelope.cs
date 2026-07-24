using System.Collections.Immutable;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

/// <summary>Canonical JSON diagnostic output for one command invocation.</summary>
public sealed record CommandDiagnosticEnvelope(
    [property: JsonPropertyName("diagnostics")] ImmutableArray<CommandDiagnostic> Diagnostics,
    [property: JsonPropertyName("exitCode")] int ExitCode);
