namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Exact consumer project and compiled reference-assembly input.</summary>
public sealed record DotNetConsoleConsumerProject(
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("relativeProjectPath")] string RelativeProjectPath,
    [property: JsonPropertyName("targetFramework")] string TargetFramework,
    [property: JsonPropertyName("referenceAssemblyName")] string ReferenceAssemblyName,
    [property: JsonPropertyName("relativeReferenceAssemblyPath")]
    string RelativeReferenceAssemblyPath,
    [property: JsonPropertyName("referenceAssemblyDigest")]
    Sha256Digest ReferenceAssemblyDigest);
