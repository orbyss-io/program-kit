using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Providers.DotNet.Manifests;

namespace Orbyss.ProgramKit.Providers.DotNet;

public sealed class DotNetProvider : IIntakeMappingProvider, IConstructionProvider, IEvaluationProvider
{
    private readonly DotNetFactoryProvider construction = new();

    public ProviderManifest Manifest => construction.Manifest;

    public Task<ProviderIntakeResult> MapAsync(ProviderIntakeContext context)
    {
        try
        {
            JsonArray semanticRecords = context.RootBundle["semanticRecords"] as JsonArray
                ?? throw new InvalidDataException("The bundle semanticRecords value must be an array.");
            if (semanticRecords.Count != 1)
            {
                throw new InvalidDataException("The exact .NET v1 mapping requires one component/API semantic record.");
            }

            List<ArtifactReference> inputs = new();
            ArtifactReference definitionReference = BindArtifact((JsonObject)semanticRecords[0]!);
            JsonObject definition = ReadExactJson(context.WorkspaceRoot, definitionReference);
            if (!string.Equals(definition["schema"]?.GetValue<string>(), "program-kit.provider.dotnet.component-api-definition/v1", StringComparison.Ordinal))
            {
                throw new InvalidDataException("The selected .NET provider does not support this semantic-record contract.");
            }

            RequireObject(definition, "component");
            RequireObject(definition, "application");
            inputs.Add(definitionReference);

            JsonArray implementationRecords = context.RootBundle["implementationRecords"] as JsonArray
                ?? throw new InvalidDataException("The bundle implementationRecords value must be an array.");
            foreach (JsonNode? node in implementationRecords)
            {
                ArtifactReference artifact = BindArtifact(node as JsonObject ?? throw new InvalidDataException("Every implementation record must be an artifact reference."));
                VerifyExactBytes(context.WorkspaceRoot, artifact);
                inputs.Add(artifact);
            }

            JsonObject evidence = new()
            {
                ["kind"] = "intake-mapping",
                ["provider"] = Manifest.Identity.StableKey,
                ["providerDigest"] = Manifest.Identity.Digest,
                ["requestDigest"] = context.RequestDigest,
                ["inputDigest"] = Digest(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', inputs.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).Select(static item => $"{item.LogicalPath}:{item.Digest}")))),
            };
            return Task.FromResult(new ProviderIntakeResult((JsonObject)definition.DeepClone(), inputs, new[] { evidence }, Array.Empty<string>(), true));
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or JsonException)
        {
            return Task.FromResult(new ProviderIntakeResult(
                new JsonObject(),
                Array.Empty<ArtifactReference>(),
                Array.Empty<JsonObject>(),
                new[] { DiagnosticIds.IncompleteMeaning },
                false));
        }
    }

    public Task<ProviderConstructionResult> ConstructAsync(ProviderConstructionContext context) =>
        construction.ConstructAsync(context);

    public Task<ProviderEvaluationResult> EvaluateAsync(ProviderEvaluationContext context)
    {
        try
        {
            RequireObject(context.Definition, "component");
            RequireObject(context.Definition, "application");
            JsonObject evidence = new()
            {
                ["kind"] = "provider-evaluation",
                ["provider"] = Manifest.Identity.StableKey,
                ["providerDigest"] = Manifest.Identity.Digest,
                ["distribution"] = Manifest.Distribution.StableKey,
                ["distributionDigest"] = Manifest.Distribution.Digest,
                ["profile"] = DotNetProviderManifest.Profile,
                ["closureDigest"] = context.ClosureDigest,
                ["support"] = "supported",
            };
            if (context.ConstructionIdentity is not null)
            {
                evidence["constructionIdentity"] = context.ConstructionIdentity;
            }

            return Task.FromResult(new ProviderEvaluationResult(new[] { evidence }, Array.Empty<string>(), true));
        }
        catch (InvalidDataException)
        {
            return Task.FromResult(new ProviderEvaluationResult(Array.Empty<JsonObject>(), new[] { DiagnosticIds.GateFailed }, false));
        }
    }

    private static ArtifactReference BindArtifact(JsonObject document) => new(
        BindIdentity(document["identity"] as JsonObject ?? throw new InvalidDataException("Artifact identity is required.")),
        Required(document, "mediaType"),
        Required(document, "logicalPath"),
        Required(document, "digest"),
        Required(document, "ownership") switch
        {
            "generated-owned" => ArtifactOwnership.GeneratedOwned,
            "seeded-handoff" => ArtifactOwnership.SeededHandoff,
            "consumer-owned" => ArtifactOwnership.ConsumerOwned,
            _ => throw new InvalidDataException("Unsupported artifact ownership."),
        });

    private static GovernedIdentity BindIdentity(JsonObject document) => new(
        Required(document, "authority"),
        Required(document, "kind"),
        Required(document, "name"),
        Required(document, "revision"),
        Required(document, "digest"));

    private static JsonObject ReadExactJson(string workspaceRoot, ArtifactReference artifact)
    {
        byte[] bytes = VerifyExactBytes(workspaceRoot, artifact);
        using JsonDocument parsed = JsonDocument.Parse(bytes, new JsonDocumentOptions
        {
            AllowDuplicateProperties = false,
            AllowTrailingCommas = false,
            CommentHandling = JsonCommentHandling.Disallow,
            MaxDepth = 128,
        });
        return JsonNode.Parse(parsed.RootElement.GetRawText()) as JsonObject
            ?? throw new InvalidDataException("The provider semantic record must be an object.");
    }

    private static byte[] VerifyExactBytes(string workspaceRoot, ArtifactReference artifact)
    {
        string root = Path.GetFullPath(workspaceRoot).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        string path = Path.GetFullPath(Path.Combine(root, artifact.LogicalPath.Replace('/', Path.DirectorySeparatorChar)));
        if (!path.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)
            || !File.Exists(path)
            || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
        {
            throw new InvalidDataException("A referenced provider input is unavailable or outside the workspace.");
        }

        byte[] bytes = File.ReadAllBytes(path);
        if (!string.Equals(Digest(bytes), artifact.Digest, StringComparison.Ordinal))
        {
            throw new InvalidDataException("A referenced provider input has changed.");
        }

        return bytes;
    }

    private static JsonObject RequireObject(JsonObject parent, string name) =>
        parent[name] as JsonObject ?? throw new InvalidDataException($"{name} must be an object.");

    private static string Required(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidDataException($"{name} must be a non-empty string.");

    private static string Digest(ReadOnlySpan<byte> bytes) =>
        $"sha256:{Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()}";
}
