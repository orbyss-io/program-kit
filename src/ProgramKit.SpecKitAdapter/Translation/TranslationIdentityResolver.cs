using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Translation;

public static class TranslationIdentityResolver
{
    public static JsonObject Identity(string kind, string name, JsonNode material) => new()
    {
        ["authority"] = "consumer.program-kit-adapter",
        ["kind"] = kind,
        ["name"] = name,
        ["revision"] = "1.0.0",
        ["digest"] = CanonicalDocument.Digest(material),
    };

    public static JsonObject Artifact(JsonObject identity, string mediaType, string logicalPath, string digest, string ownership) => new()
    {
        ["identity"] = identity.DeepClone(),
        ["mediaType"] = mediaType,
        ["logicalPath"] = logicalPath,
        ["digest"] = digest,
        ["ownership"] = ownership,
    };
}
