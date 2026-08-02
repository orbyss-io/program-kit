using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.SpecKitAdapter.Publication;

public static class AdapterFeatureClosure
{
    public static IReadOnlyDictionary<string, JsonObject> Load(string workspaceRoot, string featureRoot)
    {
        string manifestPath = LogicalPathPolicy.Resolve(workspaceRoot, $"{featureRoot}/adapter-manifest.json");
        if (!File.Exists(manifestPath)) throw new AdapterPublicationException("The adapter generated manifest is unavailable.");
        JsonObject manifest;
        try
        {
            manifest = CanonicalDocument.Parse(File.ReadAllBytes(manifestPath)).AsObject();
            AdapterSchemaValidator.Validate("generated-manifest.schema.json", manifest);
        }
        catch (InvalidDataException exception)
        {
            throw new AdapterPublicationException("The adapter generated manifest is invalid.", exception);
        }
        Dictionary<string, JsonObject> documents = new(StringComparer.Ordinal);
        foreach (JsonObject output in manifest["outputs"]!.AsArray().OfType<JsonObject>())
        {
            if (output["state"]?.GetValue<string>() == "removed") continue;
            string logicalPath = output["logicalPath"]!.GetValue<string>();
            string path = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
            if (!File.Exists(path)) throw new AdapterPublicationException("An adapter-generated feature artifact is missing.");
            byte[] bytes = File.ReadAllBytes(path);
            string digest = "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(bytes)).ToLowerInvariant();
            if (!string.Equals(digest, output["digest"]!.GetValue<string>(), StringComparison.Ordinal))
                throw new AdapterPublicationException("An adapter-generated feature artifact changed outside its exact manifest.");
            try
            {
                documents[logicalPath] = CanonicalDocument.Parse(bytes).AsObject();
            }
            catch (System.Text.Json.JsonException exception)
            {
                throw new AdapterPublicationException("An adapter-generated feature artifact is not canonical JSON.", exception);
            }
        }

        return documents;
    }

    public static PublicationResult Publish(string workspaceRoot, AdapterFeatureContext context, IReadOnlyDictionary<string, JsonObject> documents)
    {
        string featureRoot = $"specs/{context.FeatureKey}/program-kit/generated";
        Dictionary<string, JsonObject> closure = new(documents, StringComparer.Ordinal);
        TranslationResult translation = new(featureRoot, closure, CanonicalArtifactWriter.Materialize(closure));
        JsonObject manifest = AdapterGeneratedManifestBuilder.Build(
            context.Handoff!,
            context.Review!["digest"]!.GetValue<string>(),
            translation,
            context.Trace!);
        return new AdapterArtifactPublisher().Publish(workspaceRoot, translation, manifest);
    }
}
