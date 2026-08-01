using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Intake;

public sealed class IntakePipeline
{
    public const string FactoryRequestSchemaId = "https://schemas.program-kit.dev/v1/factory-request.schema.json";
    public const string BundleSchemaId = "https://schemas.program-kit.dev/v1/software-definition-bundle.schema.json";

    private readonly RestrictedYamlParser yamlParser = new();
    private readonly StructuralSchemaValidator structural;
    private readonly TypedContractBinder binder = new();
    private readonly ProviderRegistry providers;

    public IntakePipeline(ProviderRegistry providers)
    {
        this.providers = providers;
        structural = new StructuralSchemaValidator(new SchemaRegistry());
    }

    public JsonObject Load(string path)
    {
        byte[] bytes = File.ReadAllBytes(path);
        JsonNode node = Path.GetExtension(path).ToLowerInvariant() switch
        {
            ".json" => CanonicalJson.Parse(bytes),
            ".yaml" or ".yml" => yamlParser.Parse(bytes),
            _ => throw new InvalidDataException("Only .json, .yaml, and .yml request files are supported."),
        };
        return node as JsonObject ?? throw new InvalidDataException("The document root must be a mapping/object.");
    }

    public FactoryInput AdmitAndMap(string workspaceRoot, JsonObject document)
    {
        IReadOnlyList<string> structuralFailures = structural.Validate(FactoryRequestSchemaId, document);
        if (structuralFailures.Count > 0)
        {
            throw new InvalidDataException(string.Join(" ", structuralFailures));
        }

        FactoryRequest request = binder.BindFactoryRequest(document);
        JsonObject bundle = LoadExactArtifact(workspaceRoot, request.RootBundle);
        IReadOnlyList<string> bundleFailures = structural.Validate(BundleSchemaId, bundle);
        if (bundleFailures.Count > 0)
        {
            throw new InvalidDataException(string.Join(" ", bundleFailures));
        }

        JsonObject bundleIdentity = bundle["identity"] as JsonObject
            ?? throw new InvalidDataException("The root bundle has no identity.");
        if (!string.Equals(bundleIdentity["digest"]?.GetValue<string>(), request.RootBundle.Identity.Digest, StringComparison.Ordinal)
            || !string.Equals(DocumentIdentityDigest(bundle), request.RootBundle.Identity.Digest, StringComparison.Ordinal))
        {
            throw new InvalidDataException("The root bundle identity digest is not exact.");
        }

        JsonObject authorityBindingDocument = NormalizeRequest(document);
        authorityBindingDocument.Remove("authorityGrant");
        string requestDigest = CanonicalJson.Digest(NormalizeRequest(document));
        string authorityBindingDigest = CanonicalJson.Digest(authorityBindingDocument);
        FactoryRequestDocument requestDocument = new(
            request,
            requestDigest,
            authorityBindingDigest,
            bundle,
            NormalizeRequest(document));

        IIntakeMappingProvider mapper = providers.ResolveRole<IIntakeMappingProvider>(request.Selections, ProviderRole.IntakeMapping);
        ProviderIntakeResult mapped = mapper.MapAsync(new ProviderIntakeContext(
            workspaceRoot,
            bundle,
            requestDigest,
            System.Threading.CancellationToken.None)).GetAwaiter().GetResult();
        if (!mapped.Succeeded)
        {
            throw new InvalidDataException($"The selected intake-mapping provider refused the bundle: {string.Join(",", mapped.Diagnostics.OrderBy(static item => item, StringComparer.Ordinal))}");
        }

        return new FactoryInput(requestDocument, (JsonObject)mapped.Definition.DeepClone(), mapped.Inputs, mapped.Evidence);
    }

    public static JsonObject NormalizeRequest(JsonObject document)
    {
        JsonObject normalized = (JsonObject)document.DeepClone();
        if (normalized["selections"] is JsonArray selections)
        {
            normalized["selections"] = new JsonArray(selections
                .OfType<JsonObject>()
                .OrderBy(static selection => selection["role"]?.GetValue<string>(), StringComparer.Ordinal)
                .ThenBy(static selection => CanonicalJson.Digest(selection), StringComparer.Ordinal)
                .Select(static selection => selection.DeepClone())
                .ToArray());
        }

        return normalized;
    }

    public IReadOnlyList<string> MissingFields(JsonObject document)
    {
        string[] paths =
        {
            "schema", "canonicalProfile", "operation", "rootBundle", "workspaceIdentity", "requestedEffect", "selections",
            "evaluationContext.instant", "evaluationContext.source", "evaluationContext.assurance",
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

        string? operation = document["operation"]?.GetValue<string>();
        string? effect = document["requestedEffect"]?.GetValue<string>();
        if (string.Equals(operation, "construct", StringComparison.Ordinal) && document["constructionMode"] is null)
        {
            missing.Add("constructionMode");
        }

        if (effect is "candidate-only" or "committed")
        {
            if (document["authorityGrant"] is null)
            {
                missing.Add("authorityGrant");
            }

            if (document["expectedState"] is null)
            {
                missing.Add("expectedState");
            }
        }

        return missing.OrderBy(static item => item, StringComparer.Ordinal).ToArray();
    }

    public static JsonObject LoadExactArtifact(string workspaceRoot, ArtifactReference artifact)
    {
        string path = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
        if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
        {
            throw new InvalidDataException($"The exact referenced artifact is unavailable: {artifact.LogicalPath}");
        }

        byte[] bytes = File.ReadAllBytes(path);
        if (!string.Equals(Digests.Sha256(bytes), artifact.Digest, StringComparison.Ordinal))
        {
            throw new InvalidDataException($"The referenced artifact digest is not exact: {artifact.LogicalPath}");
        }

        JsonNode node = Path.GetExtension(path).ToLowerInvariant() switch
        {
            ".json" => CanonicalJson.Parse(bytes),
            ".yaml" or ".yml" => new RestrictedYamlParser().Parse(bytes),
            _ => throw new InvalidDataException("Referenced structured artifacts must use JSON or restricted YAML."),
        };
        return node as JsonObject ?? throw new InvalidDataException("The referenced artifact root must be an object.");
    }

    public static string DocumentIdentityDigest(JsonObject document)
    {
        JsonObject clone = (JsonObject)document.DeepClone();
        JsonObject identity = clone["identity"] as JsonObject
            ?? throw new InvalidDataException("Identity-bearing documents require an identity object.");
        identity["digest"] = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
        return CanonicalJson.Digest(clone);
    }
}
