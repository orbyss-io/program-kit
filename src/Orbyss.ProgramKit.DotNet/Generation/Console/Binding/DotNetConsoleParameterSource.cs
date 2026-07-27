namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Exact Open Console input mapped to a request constructor parameter.</summary>
public sealed record DotNetConsoleParameterSource(
    [property: JsonPropertyName("kind")] DotNetConsoleBindingSourceKind Kind,
    [property: JsonPropertyName("name")] string Name);
