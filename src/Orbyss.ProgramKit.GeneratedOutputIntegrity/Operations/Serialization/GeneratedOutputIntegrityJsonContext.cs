using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Serialization;

[JsonSourceGenerationOptions(
    WriteIndented = true,
    PropertyNamingPolicy = JsonKnownNamingPolicy.Unspecified,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(GeneratedOutputManifest))]
[JsonSerializable(typeof(GeneratedOutputAnchor))]
internal sealed partial class GeneratedOutputIntegrityJsonContext :
    JsonSerializerContext;
