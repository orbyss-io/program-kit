using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Schemas;

namespace Orbyss.ProgramKit.SpecKitAdapter.Contracts;

public sealed record AdapterTranslationProfile(
    JsonObject DefinitionFamily,
    string DefinitionSchema,
    string DefinitionMediaType,
    string BundleSchema,
    string BundleMediaType,
    string PreparationSchema,
    string FactoryRequestSchema,
    string OperationResultSchema,
    JsonObject Provider,
    JsonObject TargetProfile);

public sealed record AdapterCompatibilityDocument(JsonObject Document, string Digest, AdapterTranslationProfile TranslationProfile);

public static class AdapterCompatibility
{
    public const string LogicalPath = "compatibility.json";
    public const string CanonicalProfile = "program-kit.canonical-json/v1";

    public static AdapterCompatibilityDocument Load()
    {
        JsonObject document = ReadResource();
        AdapterSchemaValidator.Validate("compatibility.schema.json", document);
        string declaredDigest = Required(document, "digest");
        JsonObject digestMaterial = (JsonObject)document.DeepClone();
        digestMaterial.Remove("digest");
        if (!string.Equals(declaredDigest, CanonicalDocument.Digest(digestMaterial), StringComparison.Ordinal))
            throw new InvalidDataException("The adapter compatibility manifest digest is not exact.");

        JsonObject bindings = document["contractBindings"]!.AsObject();
        RequireBinding(bindings, CanonicalProfile, Digest(Encoding.UTF8.GetBytes(CanonicalProfile)));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById("https://schemas.program-kit.dev/v1/workspace-lock.schema.json"));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById("https://schemas.program-kit.dev/v1/software-definition-bundle.schema.json"));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById(ContractSchemaResources.PreparationRequestId));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById(ContractSchemaResources.PreparationProposalId));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById(ContractSchemaResources.AuthorityDecisionRecordId));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById(ContractSchemaResources.AuthorityRecordRequestId));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById("https://schemas.program-kit.dev/v1/authority-grant.schema.json"));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById("https://schemas.program-kit.dev/v1/factory-request.schema.json"));
        RequireContractBinding(bindings, ContractSchemaResources.ReadById(ContractSchemaResources.OperationResultId));
        foreach (string schema in AdapterSchemaResources.ReadAll().Values) RequireContractBinding(bindings, schema);

        JsonObject profile = document["translationProfile"]!.AsObject();
        return new AdapterCompatibilityDocument(
            (JsonObject)document.DeepClone(),
            declaredDigest,
            new AdapterTranslationProfile(
                (JsonObject)profile["definitionFamily"]!.DeepClone(),
                Required(profile, "definitionSchema"),
                Required(profile, "definitionMediaType"),
                Required(profile, "bundleSchema"),
                Required(profile, "bundleMediaType"),
                Required(profile, "preparationSchema"),
                Required(profile, "factoryRequestSchema"),
                Required(profile, "operationResultSchema"),
                (JsonObject)profile["provider"]!.DeepClone(),
                (JsonObject)profile["targetProfile"]!.DeepClone()));
    }

    private static void RequireContractBinding(JsonObject bindings, string schemaText)
    {
        JsonObject schema = JsonNode.Parse(schemaText)!.AsObject();
        RequireBinding(bindings, Required(schema, "$id"), CanonicalDocument.Digest(schema));
    }

    private static void RequireBinding(JsonObject bindings, string identity, string expectedDigest)
    {
        string actual = bindings[identity]?.GetValue<string>()
            ?? throw new InvalidDataException($"The adapter compatibility manifest omits {identity}.");
        if (!string.Equals(actual, expectedDigest, StringComparison.Ordinal))
            throw new InvalidDataException($"The adapter compatibility binding for {identity} is stale.");
    }

    private static JsonObject ReadResource()
    {
        Assembly assembly = typeof(AdapterCompatibility).Assembly;
        string name = assembly.GetManifestResourceNames().Single(item => item.EndsWith($".Resources.{LogicalPath}", StringComparison.Ordinal));
        using Stream stream = assembly.GetManifestResourceStream(name) ?? throw new InvalidDataException("The adapter compatibility manifest is not embedded.");
        return JsonNode.Parse(stream)!.AsObject();
    }

    private static string Required(JsonObject document, string name) => document[name]?.GetValue<string>() is { Length: > 0 } value
        ? value
        : throw new InvalidDataException($"The adapter compatibility field {name} is required.");

    private static string Digest(ReadOnlySpan<byte> bytes) =>
        $"sha256:{Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()}";
}
