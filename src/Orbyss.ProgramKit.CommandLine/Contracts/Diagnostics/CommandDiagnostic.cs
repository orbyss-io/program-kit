using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

/// <summary>One stable, script-readable command diagnostic.</summary>
public sealed record CommandDiagnostic(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("severity")] string Severity,
    [property: JsonPropertyName("message")] string Message,
    [property: JsonPropertyName("path")] string Path);
