namespace Orbyss.ProgramKit.DotNet.Shells;

/// <summary>One reviewed CShells shell and its enabled feature names.</summary>
public sealed record DotNetShellSelection(
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("enabledFeatures")] ImmutableArray<string> EnabledFeatures);
