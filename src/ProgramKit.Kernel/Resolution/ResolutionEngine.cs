using System;
using System.Collections.Generic;
using System.Linq;
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
    IConstructionProvider ConstructionProvider,
    IEvaluationProvider EvaluationProvider,
    ResolutionLock Lock,
    IntegrationResolutionExplanation Explanation);

public sealed class ResolutionEngine
{
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
    private readonly ProviderRegistry providers;

    public ResolutionEngine(ProviderRegistry providers)
    {
        this.providers = providers;
    }

    public ResolvedFactoryInput Resolve(FactoryInput input)
    {
        IConstructionProvider constructionProvider = providers.ResolveRole<IConstructionProvider>(input.Request.Selections, ProviderRole.Construction);
        IEvaluationProvider evaluationProvider = providers.ResolveRole<IEvaluationProvider>(input.Request.Selections, ProviderRole.Evaluation);
        ExactSelection profileSelection = input.Request.Selections.SingleOrDefault(static selection => string.Equals(selection.Role, "target-profile", StringComparison.Ordinal))
            ?? throw new KeyNotFoundException("Exactly one target-profile selection is required.");
        string profile = profileSelection.Selected.Name;
        if (!constructionProvider.Manifest.Profiles.Contains(profile, StringComparer.Ordinal)
            || !evaluationProvider.Manifest.Profiles.Contains(profile, StringComparer.Ordinal))
        {
            throw new KeyNotFoundException($"The selected providers do not support exact profile {profile}.");
        }

        JsonObject component = RequireObject(input.Definition, "component");
        JsonObject application = RequireObject(input.Definition, "application");
        string componentName = RequireString(component, "name");
        string applicationName = RequireString(application, "name");
        string packageId = RequireString(component, "packageId");
        string packageVersion = RequireString(component, "version");
        string route = RequireString(application, "route");
        GovernedIdentity rootIdentity = input.Request.RootBundle.Identity;
        GovernedIdentity componentIdentity = Identity("component-bundle", componentName, component);
        GovernedIdentity applicationIdentity = Identity("application-bundle", applicationName, application);
        GovernedIdentity contractIdentity = Identity("consumer-contract", RequireString(component, "contractName"), component);
        GovernedIdentity relationshipIdentity = Identity("relationship", $"{applicationName}-consumes-{componentName}", application);
        GovernedIdentity seamIdentity = Identity("contribution-seam", $"{applicationName}-http-endpoints", application);
        TraceReference rootTrace = FirstTrace(input.Request);

        JsonObject closureDocument = new()
        {
            ["schema"] = "program-kit.operation-closure/v1",
            ["operation"] = ContractJson.Kebab(input.Request.Operation),
            ["requestedEffect"] = ContractJson.Kebab(input.Request.RequestedEffect),
            ["workspace"] = ContractJson.Identity(input.Request.WorkspaceIdentity),
            ["rootBundle"] = ContractJson.Artifact(input.Request.RootBundle),
            ["resolvedItems"] = new JsonArray(input.Inputs.OrderBy(static artifact => artifact.LogicalPath, StringComparer.Ordinal).Select(ContractJson.Artifact).ToArray()),
            ["relationship"] = new JsonObject
            {
                ["identity"] = ContractJson.Identity(relationshipIdentity),
                ["status"] = "direct",
                ["contract"] = ContractJson.Identity(contractIdentity),
            },
            ["providers"] = new JsonArray(
                ContractJson.Identity(constructionProvider.Manifest.Identity),
                ContractJson.Identity(evaluationProvider.Manifest.Identity)),
            ["distribution"] = ContractJson.Identity(constructionProvider.Manifest.Distribution),
            ["profile"] = ContractJson.Identity(profileSelection.Selected),
            ["package"] = new JsonObject { ["id"] = packageId, ["version"] = packageVersion },
            ["route"] = route,
            ["evaluationContext"] = new JsonObject
            {
                ["instant"] = input.Request.EvaluationContext.Instant.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", System.Globalization.CultureInfo.InvariantCulture),
                ["source"] = ContractJson.Identity(input.Request.EvaluationContext.Source),
                ["assurance"] = "approved-declared-instant",
            },
        };
        if (input.Request.ConstructionMode is not null)
        {
            closureDocument["constructionMode"] = ContractJson.Kebab(input.Request.ConstructionMode.Value);
        }
        string closureDigest = CanonicalJson.Digest(closureDocument);
        string constructionIdentity = CanonicalJson.Digest(new JsonObject
        {
            ["closureDigest"] = closureDigest,
            ["distributionDigest"] = constructionProvider.Manifest.Distribution.Digest,
            ["profileDigest"] = profileSelection.Selected.Digest,
        });

        ResolvedItem[] resolvedItems = input.Inputs.OrderBy(static artifact => artifact.LogicalPath, StringComparer.Ordinal).Select(artifact => new ResolvedItem(
            artifact.MediaType.Contains("component-api", StringComparison.Ordinal) ? "semantic-record" : "implementation-record",
            artifact.Identity,
            artifact,
            "available")).ToArray();
        ResolvedRelationship relationship = new(
            relationshipIdentity,
            applicationIdentity,
            componentIdentity,
            "direct",
            contractIdentity,
            null,
            new[] { rootTrace });
        ExactSelection[] providerSelections = input.Request.Selections
            .Where(static selection => selection.Role is "intake-mapping" or "construction" or "evaluation")
            .OrderBy(static selection => selection.Role, StringComparer.Ordinal)
            .ToArray();
        GovernedIdentity toolIdentity = ContractJson.StableIdentity("microsoft.dotnet", "toolchain", "dotnet-sdk", "10.0.302", "dotnet-sdk:10.0.302");
        ArtifactReference toolArtifact = new(
            toolIdentity,
            "application/vnd.microsoft.dotnet-sdk",
            "toolchain/dotnet-sdk/10.0.302",
            toolIdentity.Digest,
            ArtifactOwnership.GeneratedOwned);
        GovernedIdentity governance = ContractJson.StableIdentity("orbyss.program-kit", "governance-profile", "constitution", "1.0.0", "program-kit-constitution-v1.0.0");
        GovernedIdentity lockIdentity = new("orbyss.program-kit", "resolution-lock", input.Request.WorkspaceIdentity.Name, "1", EmptyDigest);
        JsonObject lockDocument = new()
        {
            ["schema"] = "program-kit.resolution-lock/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["identity"] = ContractJson.Identity(lockIdentity),
            ["requestDigest"] = input.RequestDigest,
            ["rootBundle"] = ContractJson.Artifact(input.Request.RootBundle),
            ["resolvedItems"] = new JsonArray(resolvedItems.Select(ResolvedItemJson).ToArray()),
            ["relationships"] = new JsonArray(ResolvedRelationshipJson(relationship)),
            ["providers"] = new JsonArray(providerSelections.Select(ContractJson.Selection).ToArray()),
            ["profiles"] = new JsonArray(ContractJson.Identity(profileSelection.Selected)),
            ["toolchain"] = new JsonArray(new JsonObject
            {
                ["role"] = "construction-toolchain",
                ["identity"] = ContractJson.Identity(toolIdentity),
                ["artifact"] = ContractJson.Artifact(toolArtifact),
                ["declaredEnvironment"] = new JsonObject { ["sdkVersion"] = "10.0.302" },
            }),
            ["policies"] = new JsonObject
            {
                ["governanceProfile"] = ContractJson.Identity(governance),
                ["waivers"] = new JsonArray(),
            },
            ["closureDigest"] = closureDigest,
            ["constructionIdentity"] = constructionIdentity,
        };
        lockIdentity = lockIdentity with { Digest = CanonicalJson.Digest(lockDocument) };
        lockDocument["identity"] = ContractJson.Identity(lockIdentity);
        string lockDigest = CanonicalJson.Digest(lockDocument);
        ResolutionLock resolutionLock = new(
            "program-kit.resolution-lock/v1",
            CanonicalJson.Profile,
            lockIdentity,
            input.RequestDigest,
            input.Request.RootBundle,
            resolvedItems,
            new[] { relationship },
            providerSelections,
            new[] { profileSelection.Selected },
            closureDigest,
            constructionIdentity,
            lockDocument);

        JsonObject explanationDocument = BuildExplanation(
            input,
            lockDigest,
            rootIdentity,
            componentIdentity,
            applicationIdentity,
            contractIdentity,
            relationshipIdentity,
            seamIdentity,
            constructionProvider.Manifest.Identity,
            profileSelection,
            packageId,
            packageVersion,
            component,
            application,
            rootTrace);
        IntegrationResolutionExplanation explanation = new(
            "program-kit.integration-resolution-explanation/v1",
            CanonicalJson.Profile,
            input.RequestDigest,
            lockDigest,
            rootIdentity,
            JsonObjects(explanationDocument, "semanticCoverage"),
            JsonObjects(explanationDocument, "relationships"),
            JsonObjects(explanationDocument, "selections"),
            JsonObjects(explanationDocument, "seams"),
            JsonObjects(explanationDocument, "artifactPlan"),
            JsonObjects(explanationDocument, "gates"),
            JsonObjects(explanationDocument, "evidence"),
            JsonObjects(explanationDocument, "blockers"),
            JsonObjects(explanationDocument, "trace"),
            explanationDocument);
        return new ResolvedFactoryInput(input, constructionProvider, evaluationProvider, resolutionLock, explanation);
    }

    private static JsonObject BuildExplanation(
        FactoryInput input,
        string lockDigest,
        GovernedIdentity root,
        GovernedIdentity component,
        GovernedIdentity application,
        GovernedIdentity contract,
        GovernedIdentity relationship,
        GovernedIdentity seam,
        GovernedIdentity provider,
        ExactSelection profile,
        string packageId,
        string packageVersion,
        JsonObject componentDefinition,
        JsonObject applicationDefinition,
        TraceReference trace)
    {
        JsonObject traceJson = ContractJson.Trace(trace);
        GovernedIdentity packageProducer = ContractJson.StableIdentity("orbyss.program-kit.dotnet", "producer", "dotnet-cshells", "1.0.0", provider.Digest);
        JsonArray gates = new(new[] { "exact-resolution", "candidate-integrity", "ownership", "provider-support", "provider-evaluation", "package-agreement", "claim-class" }
            .Select(name => ContractJson.Gate(
                ContractJson.StableIdentity("orbyss.program-kit", "gate", name, "1.0.0", name),
                name.StartsWith("provider-", StringComparison.Ordinal) ? "evidence-backed" : "executable-invariant",
                "not-evaluated",
                new[] { ContractJson.Subject("root-bundle", root) }))
            .ToArray());
        return new JsonObject
        {
            ["schema"] = "program-kit.integration-resolution-explanation/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["requestDigest"] = input.RequestDigest,
            ["lockDigest"] = lockDigest,
            ["root"] = ContractJson.Identity(root),
            ["semanticCoverage"] = new JsonArray(
                new JsonObject
                {
                    ["subject"] = ContractJson.Subject("consumer-contract", contract),
                    ["state"] = "declared",
                    ["trace"] = traceJson.DeepClone(),
                },
                new JsonObject
                {
                    ["subject"] = ContractJson.Subject("component-bundle", component),
                    ["state"] = "custom-bounded",
                    ["trace"] = traceJson.DeepClone(),
                }),
            ["relationships"] = new JsonArray(new JsonObject
            {
                ["assertion"] = ContractJson.Identity(relationship),
                ["status"] = "direct",
                ["contract"] = ContractJson.Identity(contract),
                ["trace"] = new JsonArray(traceJson.DeepClone()),
            }),
            ["selections"] = new JsonArray(input.Request.Selections.OrderBy(static selection => selection.Role, StringComparer.Ordinal).Select(ContractJson.Selection).ToArray()),
            ["seams"] = new JsonArray(new JsonObject
            {
                ["seam"] = ContractJson.Identity(seam),
                ["owner"] = ContractJson.Identity(application),
                ["contributions"] = new JsonArray(ContractJson.Identity(component)),
                ["ordering"] = new JsonArray(ContractJson.Identity(component)),
                ["status"] = "resolved",
            }),
            ["artifactPlan"] = new JsonArray(
                Planned($"products/{RequireString(componentDefinition, "name")}", "canonical-byte", packageProducer),
                Planned($"products/{RequireString(applicationDefinition, "name")}", "canonical-byte", packageProducer),
                Planned($"feeds/component/{packageId}.{packageVersion}.nupkg", "verified-equivalent", packageProducer)),
            ["gates"] = gates,
            ["waivers"] = new JsonArray(),
            ["evidence"] = new JsonArray(),
            ["blockers"] = new JsonArray(),
            ["trace"] = new JsonArray(traceJson.DeepClone()),
        };
    }

    private static JsonObject Planned(string path, string claimClass, GovernedIdentity producer) => new()
    {
        ["logicalPath"] = path,
        ["ownership"] = "generated-owned",
        ["producer"] = ContractJson.Identity(producer),
        ["claimClass"] = claimClass,
    };

    private static JsonObject ResolvedItemJson(ResolvedItem item) => new()
    {
        ["role"] = item.Role,
        ["identity"] = ContractJson.Identity(item.Identity),
        ["artifact"] = ContractJson.Artifact(item.Artifact),
        ["availability"] = item.Availability,
    };

    private static JsonObject ResolvedRelationshipJson(ResolvedRelationship item)
    {
        JsonObject document = new()
        {
            ["assertion"] = ContractJson.Identity(item.Assertion),
            ["status"] = item.Status,
            ["contract"] = ContractJson.Identity(item.Contract),
            ["trace"] = new JsonArray(item.Trace.Select(ContractJson.Trace).ToArray()),
        };
        if (item.Mapping is not null)
        {
            document["mapping"] = ContractJson.Identity(item.Mapping);
        }

        return document;
    }

    private static IReadOnlyList<JsonObject> JsonObjects(JsonObject document, string name) => document[name] is JsonArray array
        ? array.OfType<JsonObject>().Select(static item => (JsonObject)item.DeepClone()).ToArray()
        : Array.Empty<JsonObject>();

    private static TraceReference FirstTrace(FactoryRequest request) => request.Selections
        .Select(static selection => selection.Trace)
        .FirstOrDefault(static trace => trace is not null)
        ?? throw new InvalidOperationException("The exact request has no traceable selection.");

    private static GovernedIdentity Identity(string kind, string name, JsonNode content) =>
        new("consumer.reference", kind, name, "1.0.0", CanonicalJson.Digest(content));

    private static JsonObject RequireObject(JsonObject parent, string name) =>
        parent[name] as JsonObject ?? throw new InvalidOperationException($"definition.{name} must be an object.");

    private static string RequireString(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidOperationException($"{name} must be a non-empty string.");
}
