namespace Orbyss.ProgramKit.DotNet.Shells;

/// <summary>Reviewed direct CShells ABI and finite shell selections.</summary>
public sealed record DotNetShellComposition(
    [property: JsonPropertyName("provider")] string Provider,
    [property: JsonPropertyName("abiVersion")] SemanticVersion AbiVersion,
    [property: JsonPropertyName("shells")] ImmutableArray<DotNetShellSelection> Shells);
