using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;

namespace Orbyss.ProgramKit.SpecKitAdapter.Translation;

public sealed record TranslationResult(string FeatureRoot, IReadOnlyDictionary<string, JsonObject> Documents, IReadOnlyDictionary<string, byte[]> Bytes);

public sealed class DotNetHandoffTranslator
{
    private const string ZeroDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    public TranslationResult Translate(BoundHandoff handoff, JsonObject workspaceLock)
    {
        string featureKey = handoff.Document["feature"]!["key"]!.GetValue<string>();
        string featureRoot = $"specs/{featureKey}/program-kit/generated";
        JsonObject definition = (JsonObject)handoff.Document["definition"]!.DeepClone();
        if (definition["schema"]?.GetValue<string>() != "program-kit.provider.dotnet.component-api-definition/v1")
            throw new InvalidOperationException("Only the bounded .NET component API definition family is supported.");
        string definitionPath = $"{featureRoot}/definitions/dotnet-component-api.json";
        string definitionDigest = CanonicalDocument.Digest(definition);
        string componentName = definition["component"]!["name"]!.GetValue<string>();
        JsonObject definitionIdentity = TranslationIdentityResolver.Identity("semantic-record", componentName, definition);
        JsonObject definitionArtifact = TranslationIdentityResolver.Artifact(
            definitionIdentity,
            "application/vnd.program-kit.provider.dotnet.component-api+json",
            definitionPath,
            definitionDigest,
            "generated-owned");

        JsonObject lockIdentity = TranslationIdentityResolver.Identity("workspace-lock", handoff.Document["feature"]!["key"]!.GetValue<string>(), workspaceLock);
        string lockDigest = CanonicalDocument.Digest(workspaceLock);
        JsonObject lockArtifact = TranslationIdentityResolver.Artifact(lockIdentity, "application/json", "program-kit.lock.json", lockDigest, "generated-owned");
        JsonObject[] selections = BuildSelections(handoff, workspaceLock, lockArtifact);
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
            ["schema"] = "program-kit.software-definition-bundle/v1",
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
        JsonObject bundleArtifact = TranslationIdentityResolver.Artifact(bundleIdentity, "application/vnd.program-kit.software-definition+json", bundlePath, bundleDigest, "generated-owned");
        JsonObject workspaceIdentity = (JsonObject)workspaceLock["workspaceIdentity"]!.DeepClone();
        JsonObject evaluationContext = (JsonObject)handoff.Document["evaluationContext"]!.DeepClone();
        string constructionMode = handoff.Document["constructionMode"]?.GetValue<string>() ?? "new";
        string maximumEffect = handoff.Document["maximumEffect"]!.GetValue<string>();
        if (maximumEffect == "none") throw new InvalidOperationException("Preparation requires a candidate-only or committed maximum effect.");
        JsonObject preparation = new()
        {
            ["schema"] = "program-kit.preparation-request/v1",
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
            ["schema"] = "program-kit.factory-request/v1",
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

    private static JsonObject[] BuildSelections(BoundHandoff handoff, JsonObject workspaceLock, JsonObject lockArtifact)
    {
        string alias = handoff.Document["effectiveSelection"]!["alias"]!.GetValue<string>();
        JsonObject selected = workspaceLock["selections"]!.AsArray().OfType<JsonObject>()
            .Single(item => string.Equals(item["alias"]!.GetValue<string>(), alias, StringComparison.Ordinal));
        JsonObject provider = selected["provider"]!.AsObject();
        JsonObject profile = selected["targetProfile"]!.AsObject();
        JsonObject authority = selected["selectionAuthority"]!.AsObject();
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
}
