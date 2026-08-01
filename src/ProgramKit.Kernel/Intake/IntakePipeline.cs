using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Intake;

public sealed class IntakePipeline
{
    private readonly RestrictedYamlParser yamlParser = new();

    public JsonObject Load(string path)
    {
        byte[] bytes = File.ReadAllBytes(path);
        JsonNode node = Path.GetExtension(path).ToLowerInvariant() switch
        {
            ".json" => CanonicalJson.Parse(bytes),
            ".yaml" or ".yml" => yamlParser.Parse(bytes),
            _ => throw new InvalidDataException("Only .json, .yaml, and .yml request files are supported."),
        };
        return node as JsonObject ?? throw new InvalidDataException("The request root must be a mapping/object.");
    }

    public FactoryInput Bind(JsonObject document)
    {
        string schema = RequiredString(document, "schema");
        if (!string.Equals(schema, "program-kit.dotnet-factory-intake/v1", StringComparison.Ordinal))
        {
            throw new InvalidDataException("Unsupported request schema.");
        }

        FactoryOperation operation = ParseEnum<FactoryOperation>(RequiredString(document, "operation"));
        RequestedEffect effect = ParseEnum<RequestedEffect>(RequiredString(document, "requestedEffect"));
        ConstructionMode? mode = document["constructionMode"] is null
            ? null
            : ParseEnum<ConstructionMode>(RequiredString(document, "constructionMode"));
        if (operation == FactoryOperation.Construct && mode is null)
        {
            throw new InvalidDataException("construct requires constructionMode.");
        }

        if (operation != FactoryOperation.Construct && mode is not null)
        {
            throw new InvalidDataException("constructionMode is valid only for construct.");
        }

        JsonObject evaluation = RequiredObject(document, "evaluationContext");
        DateTimeOffset instant = DateTimeOffset.ParseExact(
            RequiredString(evaluation, "instant"),
            "yyyy-MM-dd'T'HH:mm:ss'Z'",
            CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
        string assurance = RequiredString(evaluation, "assurance");
        if (!string.Equals(assurance, "approved-declared-instant", StringComparison.Ordinal))
        {
            throw new InvalidDataException("Unsupported evaluation-context assurance.");
        }

        JsonObject? legacyAuthority = document["authority"] as JsonObject;
        JsonObject requestCore = (JsonObject)document.DeepClone();
        requestCore.Remove("authorityGrant");
        requestCore.Remove("authority");
        string? authorityGrant = (document["authorityGrant"] as JsonObject)?["logicalPath"]?.GetValue<string>();
        string requestCoreIdentity = CanonicalJson.Digest(requestCore);
        JsonObject selections = RequiredObject(document, "selections");
        JsonObject definition = RequiredObject(document, "definition");

        return new FactoryInput(
            operation,
            mode,
            effect,
            RequiredString(document, "workspaceIdentity"),
            instant,
            RequiredString(evaluation, "source"),
            legacyAuthority is not null && RequiredBoolean(legacyAuthority, "approved"),
            legacyAuthority is null ? instant : ParseInstant(legacyAuthority, "notBefore"),
            legacyAuthority is null ? instant : ParseInstant(legacyAuthority, "notAfter"),
            authorityGrant,
            requestCoreIdentity,
            RequiredString(selections, "provider"),
            RequiredString(selections, "profile"),
            (JsonObject)definition.DeepClone(),
            (JsonObject)document.DeepClone());
    }

    public IReadOnlyList<string> MissingFields(JsonObject document)
    {
        string[] paths =
        {
            "schema", "operation", "workspaceIdentity", "requestedEffect",
            "evaluationContext.instant", "evaluationContext.source", "evaluationContext.assurance",
            "selections.provider", "selections.profile", "definition.component", "definition.application",
        };
        List<string> missing = new();
        foreach (string path in paths)
        {
            JsonNode? node = document;
            foreach (string segment in path.Split('.'))
            {
                node = node?[segment];
            }

            if (node is null)
            {
                missing.Add(path);
            }
        }

        string? requestedEffect = document["requestedEffect"]?.GetValue<string>();
        if (requestedEffect is "candidate-only" or "committed" && document["authorityGrant"] is null)
        {
            missing.Add("authorityGrant");
        }

        return missing;
    }

    private static JsonObject RequiredObject(JsonObject parent, string name) =>
        parent[name] as JsonObject ?? throw new InvalidDataException($"{name} must be an object.");

    private static string RequiredString(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidDataException($"{name} must be a non-empty string.");

    private static bool RequiredBoolean(JsonObject parent, string name) =>
        parent[name]?.GetValue<bool>() ?? throw new InvalidDataException($"{name} must be a Boolean.");

    private static DateTimeOffset ParseInstant(JsonObject parent, string name) =>
        DateTimeOffset.ParseExact(RequiredString(parent, name), "yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);

    private static T ParseEnum<T>(string value)
        where T : struct, Enum
    {
        string normalized = value.Replace("-", string.Empty, StringComparison.Ordinal);
        return Enum.TryParse(normalized, true, out T result)
            ? result
            : throw new InvalidDataException($"Unsupported {typeof(T).Name} value: {value}");
    }
}
