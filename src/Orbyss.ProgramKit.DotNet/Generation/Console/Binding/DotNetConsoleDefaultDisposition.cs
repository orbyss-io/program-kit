namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Mandatory exact disposition of an Open Console default.</summary>
public sealed record DotNetConsoleDefaultDisposition(
    [property: JsonPropertyName("kind")] DotNetConsoleDefaultKind Kind,
    [property: JsonPropertyName("canonicalValue")] string? CanonicalValue);
