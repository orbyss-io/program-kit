using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.Resolution;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Kernel.Resolution;

public sealed record ResolvedFactoryInput(
    FactoryInput Input,
    IFactoryProvider Provider,
    ResolutionLock Lock,
    IntegrationResolutionExplanation Explanation);

public sealed class ResolutionEngine
{
    private readonly ProviderRegistry providers;

    public ResolutionEngine(ProviderRegistry providers)
    {
        this.providers = providers;
    }

    public ResolvedFactoryInput Resolve(FactoryInput input)
    {
        IFactoryProvider provider = providers.Resolve(input.ProviderSelection);
        if (!provider.Manifest.Profiles.Any(profile => string.Equals(profile, input.ProfileSelection, StringComparison.Ordinal)))
        {
            throw new KeyNotFoundException($"The selected provider does not support exact profile {input.ProfileSelection}.");
        }

        JsonObject component = RequireObject(input.Definition, "component");
        JsonObject application = RequireObject(input.Definition, "application");
        string componentName = RequireString(component, "name");
        string applicationName = RequireString(application, "name");
        string packageId = RequireString(component, "packageId");
        string packageVersion = RequireString(component, "version");
        string route = RequireString(application, "route");
        string requestDigest = CanonicalJson.Digest(input.CanonicalDocument);

        GovernedIdentity rootIdentity = Identity("application-bundle", applicationName, input.Definition);
        GovernedIdentity componentIdentity = Identity("component-bundle", componentName, component);
        GovernedIdentity contractIdentity = Identity("consumer-contract", RequireString(component, "contractName"), component);
        GovernedIdentity relationshipIdentity = Identity("relationship", $"{applicationName}-consumes-{componentName}", application);
        ArtifactReference rootReference = new(
            rootIdentity,
            "application/vnd.program-kit.software-definition+json",
            "definitions/application.json",
            rootIdentity.Digest,
            ArtifactOwnership.ConsumerOwned);

        JsonObject lockDocument = new()
        {
            ["schema"] = "program-kit.resolution-lock/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["requestDigest"] = requestDigest,
            ["root"] = IdentityJson(rootIdentity),
            ["resolvedItems"] = new JsonArray
            {
                new JsonObject { ["role"] = "component", ["identity"] = IdentityJson(componentIdentity), ["availability"] = "available" },
                new JsonObject { ["role"] = "contract", ["identity"] = IdentityJson(contractIdentity), ["availability"] = "available" },
            },
            ["relationship"] = new JsonObject
            {
                ["identity"] = IdentityJson(relationshipIdentity),
                ["status"] = "direct",
                ["contract"] = IdentityJson(contractIdentity),
            },
            ["provider"] = IdentityJson(provider.Manifest.Identity),
            ["profile"] = input.ProfileSelection,
            ["package"] = new JsonObject { ["id"] = packageId, ["version"] = packageVersion },
            ["route"] = route,
            ["evaluationContext"] = new JsonObject
            {
                ["instant"] = input.EvaluationInstant.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", System.Globalization.CultureInfo.InvariantCulture),
                ["source"] = input.EvaluationSource,
                ["assurance"] = "approved-declared-instant",
            },
        };
        string closureDigest = CanonicalJson.Digest(lockDocument);
        string constructionIdentity = Digests.Sha256(Encoding.UTF8.GetBytes($"{requestDigest}\n{closureDigest}"));
        lockDocument["closureDigest"] = closureDigest;
        lockDocument["constructionIdentity"] = constructionIdentity;
        string lockDigest = CanonicalJson.Digest(lockDocument);
        GovernedIdentity lockIdentity = new("orbyss.program-kit", "resolution-lock", input.WorkspaceIdentity, "1", lockDigest);

        ResolutionLock resolutionLock = new(
            "program-kit.resolution-lock/v1",
            CanonicalJson.Profile,
            lockIdentity,
            requestDigest,
            rootReference,
            Array.Empty<ResolvedItem>(),
            Array.Empty<ResolvedRelationship>(),
            Array.Empty<ExactSelection>(),
            Array.Empty<GovernedIdentity>(),
            closureDigest,
            constructionIdentity,
            lockDocument);

        JsonObject explanationDocument = BuildExplanation(
            requestDigest,
            lockDigest,
            rootIdentity,
            componentIdentity,
            contractIdentity,
            relationshipIdentity,
            provider.Manifest.Identity,
            input.ProfileSelection,
            packageId,
            packageVersion,
            route,
            component,
            application);
        IntegrationResolutionExplanation explanation = new(
            "program-kit.integration-resolution-explanation/v1",
            CanonicalJson.Profile,
            requestDigest,
            lockDigest,
            rootIdentity,
            Array.Empty<JsonObject>(),
            Array.Empty<JsonObject>(),
            Array.Empty<JsonObject>(),
            Array.Empty<JsonObject>(),
            Array.Empty<JsonObject>(),
            Array.Empty<JsonObject>(),
            Array.Empty<JsonObject>(),
            Array.Empty<JsonObject>(),
            Array.Empty<JsonObject>(),
            explanationDocument);
        return new ResolvedFactoryInput(input, provider, resolutionLock, explanation);
    }

    private static JsonObject BuildExplanation(
        string requestDigest,
        string lockDigest,
        GovernedIdentity root,
        GovernedIdentity component,
        GovernedIdentity contract,
        GovernedIdentity relationship,
        GovernedIdentity provider,
        string profile,
        string packageId,
        string packageVersion,
        string route,
        JsonObject componentDefinition,
        JsonObject applicationDefinition) => new()
        {
            ["schema"] = "program-kit.integration-resolution-explanation/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["requestDigest"] = requestDigest,
            ["lockDigest"] = lockDigest,
            ["root"] = IdentityJson(root),
            ["semanticCoverage"] = new JsonArray
        {
            new JsonObject { ["subject"] = IdentityJson(contract), ["state"] = "declared", ["source"] = "definition.component.contractName" },
            new JsonObject { ["subject"] = IdentityJson(component), ["state"] = "custom-bounded", ["source"] = "definition.component.implementationSource" },
        },
            ["relationships"] = new JsonArray
        {
            new JsonObject { ["assertion"] = IdentityJson(relationship), ["status"] = "direct", ["contract"] = IdentityJson(contract) },
        },
            ["selections"] = new JsonArray
        {
            new JsonObject { ["role"] = "construction", ["selected"] = IdentityJson(provider), ["profile"] = profile },
        },
            ["seams"] = new JsonArray
        {
            new JsonObject { ["kind"] = "http-endpoint-contribution", ["owner"] = "application-host-assembler", ["route"] = route, ["ordering"] = "identity-ordinal" },
        },
            ["artifactPlan"] = new JsonArray
        {
            new JsonObject { ["logicalPath"] = $"products/{RequireString(componentDefinition, "name")}", ["ownership"] = "generated-owned", ["claimClass"] = "canonical-byte" },
            new JsonObject { ["logicalPath"] = $"products/{RequireString(applicationDefinition, "name")}", ["ownership"] = "generated-owned", ["claimClass"] = "canonical-byte" },
            new JsonObject { ["logicalPath"] = $"feeds/component/{packageId}.{packageVersion}.nupkg", ["ownership"] = "generated-owned", ["claimClass"] = "verified-equivalent" },
        },
            ["gates"] = new JsonArray("exact-resolution", "ownership", "provider-conformance", "runtime-isolation", "publication"),
            ["waivers"] = new JsonArray(),
            ["evidence"] = new JsonArray("locked-restore", "build", "pack", "consumer-runtime"),
            ["blockers"] = new JsonArray(),
            ["trace"] = new JsonArray(
            "definition.component",
            "definition.application",
            "selections.provider",
            "selections.profile"),
            ["limitations"] = new JsonArray(
            "No generalized impact or migration claim",
            "Custom behavior remains consumer-owned",
            "Runtime behavior is proven only by selected evidence"),
        };

    private static GovernedIdentity Identity(string kind, string name, JsonNode content) =>
        new("consumer.reference", kind, name, "1.0.0", CanonicalJson.Digest(content));

    private static JsonObject IdentityJson(GovernedIdentity identity) => new()
    {
        ["authority"] = identity.Authority,
        ["kind"] = identity.Kind,
        ["name"] = identity.Name,
        ["revision"] = identity.Revision,
        ["digest"] = identity.Digest,
    };

    private static JsonObject RequireObject(JsonObject parent, string name) =>
        parent[name] as JsonObject ?? throw new InvalidOperationException($"definition.{name} must be an object.");

    private static string RequireString(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidOperationException($"{name} must be a non-empty string.");
}
