using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;

namespace Orbyss.ProgramKit.SpecKitAdapter.Translation;

public sealed record TranslationResult(string FeatureRoot, IReadOnlyDictionary<string, JsonObject> Documents, IReadOnlyDictionary<string, byte[]> Bytes);

public sealed class DotNetHandoffTranslator
{
    private const string ZeroDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    public TranslationResult Translate(BoundHandoff handoff, JsonObject workspaceLock)
    {
        AdapterTranslationProfile compatibility;
        try
        {
            compatibility = AdapterCompatibility.Load().TranslationProfile;
        }
        catch (InvalidDataException exception)
        {
            throw new AdapterBoundaryException(AdapterFailureKind.UnsupportedCompatibility, "The adapter compatibility envelope is invalid.", innerException: exception);
        }
        RequireExact(handoff.Document["definitionFamily"]!, compatibility.DefinitionFamily, "The handoff definition family is outside the tested adapter compatibility manifest.");
        string featureKey = handoff.Document["feature"]!["key"]!.GetValue<string>();
        string featureRoot = $"specs/{featureKey}/program-kit/generated";
        JsonObject definition = (JsonObject)handoff.Document["definition"]!.DeepClone();
        if (definition["schema"]?.GetValue<string>() != compatibility.DefinitionSchema)
            throw new InvalidOperationException("Only the bounded .NET component API definition family is supported.");
        string definitionPath = $"{featureRoot}/definitions/dotnet-component-api.json";
        string definitionDigest = CanonicalDocument.Digest(definition);
        string componentName = definition["component"]!["name"]!.GetValue<string>();
        JsonObject definitionIdentity = TranslationIdentityResolver.Identity("semantic-record", componentName, definition);
        JsonObject definitionArtifact = TranslationIdentityResolver.Artifact(
            definitionIdentity,
            compatibility.DefinitionMediaType,
            definitionPath,
            definitionDigest,
            "generated-owned");

        JsonObject lockIdentity = TranslationIdentityResolver.Identity("workspace-lock", handoff.Document["feature"]!["key"]!.GetValue<string>(), workspaceLock);
        string lockDigest = CanonicalDocument.Digest(workspaceLock);
        JsonObject lockArtifact = TranslationIdentityResolver.Artifact(lockIdentity, "application/json", "program-kit.lock.json", lockDigest, "generated-owned");
        JsonObject[] selections = BuildSelections(handoff, workspaceLock, lockArtifact, compatibility);
        JsonObject targetProfile = (JsonObject)selections.Single(static item => item["role"]!.GetValue<string>() == "target-profile")["selected"]!.DeepClone();
        JsonObject bundleIdentity = new()
        {
            ["authority"] = "consumer.program-kit-adapter",
            ["kind"] = "application-bundle",
            ["name"] = definition["application"]!["name"]!.GetValue<string>(),
            ["revision"] = "1.0.0",
            ["digest"] = ZeroDigest,
        };
        JsonObject bundle = new()
        {
            ["schema"] = compatibility.BundleSchema,
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["identity"] = bundleIdentity,
            ["semanticRecords"] = new JsonArray(definitionArtifact),
            ["implementationRecords"] = new JsonArray(handoff.Document["implementation"]!.AsArray().Select(static item => item!.DeepClone()).ToArray()),
            ["relationships"] = new JsonArray(),
            ["profiles"] = new JsonArray(targetProfile.DeepClone()),
            ["selections"] = new JsonArray(selections.Select(static item => item.DeepClone()).ToArray()),
            ["dispositions"] = new JsonArray(),
        };
        bundleIdentity["digest"] = CanonicalDocument.Digest(bundle);
        string bundlePath = $"{featureRoot}/definitions/software-bundle.json";
        string bundleDigest = CanonicalDocument.Digest(bundle);
        JsonObject bundleArtifact = TranslationIdentityResolver.Artifact(bundleIdentity, compatibility.BundleMediaType, bundlePath, bundleDigest, "generated-owned");
        JsonObject workspaceIdentity = (JsonObject)workspaceLock["workspaceIdentity"]!.DeepClone();
        JsonObject evaluationContext = (JsonObject)handoff.Document["evaluationContext"]!.DeepClone();
        string constructionMode = handoff.Document["constructionMode"]?.GetValue<string>() ?? "new";
        string maximumEffect = handoff.Document["maximumEffect"]!.GetValue<string>();
        if (maximumEffect == "none") throw new InvalidOperationException("Preparation requires a candidate-only or committed maximum effect.");
        JsonObject preparation = new()
        {
            ["schema"] = compatibility.PreparationSchema,
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["rootBundle"] = bundleArtifact.DeepClone(),
            ["workspaceIdentity"] = workspaceIdentity.DeepClone(),
            ["constructionMode"] = constructionMode,
            ["desiredEffect"] = maximumEffect,
            ["selections"] = new JsonArray(selections.Select(static item => item.DeepClone()).ToArray()),
            ["evaluationContext"] = evaluationContext.DeepClone(),
            ["expectedLock"] = lockArtifact,
        };
        JsonObject explain = new()
        {
            ["schema"] = compatibility.FactoryRequestSchema,
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["operation"] = "explain",
            ["rootBundle"] = bundleArtifact.DeepClone(),
            ["workspaceIdentity"] = workspaceIdentity,
            ["evaluationContext"] = evaluationContext,
            ["requestedEffect"] = "none",
            ["selections"] = new JsonArray(selections.Select(static item => item.DeepClone()).ToArray()),
        };
        Dictionary<string, JsonObject> documents = new(StringComparer.Ordinal)
        {
            [definitionPath] = definition,
            [bundlePath] = bundle,
            [$"{featureRoot}/requests/prepare.json"] = preparation,
            [$"{featureRoot}/requests/explain.json"] = explain,
        };
        return new TranslationResult(featureRoot, documents, CanonicalArtifactWriter.Materialize(documents));
    }

    private static JsonObject[] BuildSelections(BoundHandoff handoff, JsonObject workspaceLock, JsonObject lockArtifact, AdapterTranslationProfile compatibility)
    {
        string alias = handoff.Document["effectiveSelection"]!["alias"]!.GetValue<string>();
        JsonObject selected = handoff.Document["effectiveSelection"]!["selection"]!.AsObject();
        JsonObject current = workspaceLock["selections"]!.AsArray().OfType<JsonObject>()
            .Single(item => string.Equals(item["alias"]!.GetValue<string>(), alias, StringComparison.Ordinal));
        RequireExact(selected, current, "The reviewed exact selection is unavailable or changed in the current workspace lock.");
        JsonObject provider = selected["provider"]!.AsObject();
        JsonObject profile = selected["targetProfile"]!.AsObject();
        JsonObject authority = selected["selectionAuthority"]!.AsObject();
        RequireExact(provider, compatibility.Provider, "The selected provider is outside the tested adapter compatibility manifest.");
        RequireExact(profile, compatibility.TargetProfile, "The selected target profile is outside the tested adapter compatibility manifest.");
        return new[] { "intake-mapping", "construction", "evaluation", "target-profile" }.Select(role => new JsonObject
        {
            ["role"] = role,
            ["selected"] = (role == "target-profile" ? profile : provider).DeepClone(),
            ["selectionAuthority"] = authority.DeepClone(),
            ["trace"] = new JsonObject
            {
                ["source"] = lockArtifact.DeepClone(),
                ["pointer"] = $"/selections/{alias}",
                ["claimKind"] = "accepted-workspace-selection",
            },
        }).ToArray();
    }

    private static void RequireExact(JsonNode actual, JsonNode expected, string message)
    {
        if (!CanonicalDocument.Encode(actual).SequenceEqual(CanonicalDocument.Encode(expected)))
            throw new AdapterBoundaryException(AdapterFailureKind.UnsupportedCompatibility, message);
    }
}
