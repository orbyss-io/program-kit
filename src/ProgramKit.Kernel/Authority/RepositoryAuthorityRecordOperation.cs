using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Preparation;
using Orbyss.ProgramKit.Kernel.Resolution;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Authority;

public sealed class RepositoryAuthorityRecordOperation
{
    private static readonly HashSet<string> ProviderConditionKinds = new(StringComparer.Ordinal)
    {
        "operation-closure", "review-digest", "expected-live-state", "revocation-handle",
    };

    private readonly IntakePipeline intake;
    private readonly ResolutionEngine resolution;
    private readonly StructuralSchemaValidator structural = new(new SchemaRegistry());
    private readonly TypedContractBinder binder = new();

    public RepositoryAuthorityRecordOperation(ProviderRegistry providers)
    {
        intake = new IntakePipeline(providers);
        resolution = new ResolutionEngine(providers);
    }

    public OperationResult Execute(string workspaceRoot, JsonObject request)
    {
        Validate(ContractSchemaResources.AuthorityRecordRequestId, request);
        ArtifactReference proposalReference = binder.BindArtifact(request["proposal"]!.AsObject());
        ArtifactReference decisionReference = binder.BindArtifact(request["decision"]!.AsObject());
        RequireArtifactIdentity(proposalReference);
        RequireArtifactIdentity(decisionReference);

        JsonObject preparationResult = IntakePipeline.LoadExactArtifact(workspaceRoot, proposalReference);
        Validate(ContractSchemaResources.OperationResultId, preparationResult);
        if (preparationResult["command"]?.GetValue<string>() != "prepare"
            || preparationResult["outcome"]?.GetValue<string>() != "succeeded"
            || preparationResult["effectState"]?.GetValue<string>() != "none")
            throw new InvalidDataException("Authority recording requires one successful effect-free preparation result.");
        JsonObject proposal = preparationResult["payload"]?["proposal"]?.AsObject()
            ?? throw new InvalidDataException("The preparation result has no exact proposal.");
        Validate(ContractSchemaResources.PreparationProposalId, proposal);
        RequireSelfDigest(proposal);

        JsonObject decision = IntakePipeline.LoadExactArtifact(workspaceRoot, decisionReference);
        Validate(ContractSchemaResources.AuthorityDecisionRecordId, decision);
        if (!CanonicalJson.Encode(decision["proposal"]!).SequenceEqual(CanonicalJson.Encode(request["proposal"]!)))
            throw new InvalidDataException("The human decision is bound to a different preparation result.");
        if (decision["decision"]!.GetValue<string>() != "approve")
            throw new UnauthorizedAccessException("The human authority decision does not approve construction.");

        ValidateCurrentProposal(workspaceRoot, proposal);
        ValidateDecision(workspaceRoot, decision, proposal);

        string grantPath = Required(request, "grantPath");
        string revocationPath = Required(request, "revocationPath");
        if (string.Equals(grantPath, revocationPath, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Grant and revocation paths must be distinct.");

        string handle = Digests.Sha256(Encoding.UTF8.GetBytes($"{proposal["digest"]!.GetValue<string>()}\n{decisionReference.Digest}\n{grantPath}\n{revocationPath}"));
        JsonObject revocations = new()
        {
            ["schema"] = "program-kit.authority-revocations/v1",
            ["grantHandle"] = handle,
            ["revokedGrantDigests"] = new JsonArray(),
        };
        byte[] revocationBytes = CanonicalJson.Encode(revocations);
        string revocationDigest = Digests.Sha256(revocationBytes);
        ArtifactReference revocationReference = new(
            new GovernedIdentity("consumer.repository", "revocation-state", handle["sha256:".Length..20], "1.0.0", revocationDigest),
            "application/vnd.program-kit.authority-revocations+json",
            revocationPath,
            revocationDigest,
            ArtifactOwnership.SeededHandoff);

        JsonObject ungranted = proposal["ungrantedProjection"]!.AsObject();
        string authorityBinding = CanonicalJson.Digest(IntakePipeline.NormalizeRequest(ungranted));
        JsonObject[] subjects = decision["subjects"]!.AsArray().OfType<JsonObject>()
            .Select(static subject => new JsonObject { ["kind"] = subject["kind"]!.DeepClone(), ["identity"] = subject.DeepClone() })
            .ToArray();
        JsonArray conditions = ProviderConditions(proposal, decisionReference.Digest, handle);
        foreach (JsonObject condition in decision["conditions"]!.AsArray().OfType<JsonObject>())
        {
            string kind = Required(condition, "kind");
            if (ProviderConditionKinds.Contains(kind) || conditions.OfType<JsonObject>().Any(item => Required(item, "kind") == kind))
                throw new InvalidDataException("Authority condition kinds must be unique and cannot replace provider freshness bindings.");
            conditions.Add(condition.DeepClone());
        }

        JsonObject validity = decision["validity"]!.AsObject();
        JsonObject grant = new()
        {
            ["schema"] = "program-kit.authority-grant/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["identity"] = new JsonObject
            {
                ["authority"] = "consumer.repository",
                ["kind"] = "authority-grant",
                ["name"] = $"proposal-{proposal["digest"]!.GetValue<string>()["sha256:".Length..20]}",
                ["revision"] = "1.0.0",
                ["digest"] = "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            },
            ["issuerAssertion"] = new JsonObject
            {
                ["provider"] = ContractJson.Identity(ContractJson.StableIdentity("orbyss.program-kit", "authority-provider", "repository-record", "1.0.0", "repository-record@1.0.0")),
                ["issuer"] = decision["reviewer"]!.DeepClone(),
                ["assurance"] = "repository-record-presence",
            },
            ["subjects"] = new JsonArray(subjects),
            ["operations"] = decision["operations"]!.DeepClone(),
            ["effects"] = decision["effects"]!.DeepClone(),
            ["requestBinding"] = authorityBinding,
            ["conditions"] = conditions,
            ["validity"] = new JsonObject
            {
                ["notBefore"] = NormalizeInstant(Required(validity, "notBefore")),
                ["notAfter"] = NormalizeInstant(Required(validity, "notAfter")),
            },
            ["revocationReference"] = ContractJson.Artifact(revocationReference),
            ["provenance"] = ContractJson.Artifact(decisionReference),
        };
        grant["identity"]!["digest"] = IntakePipeline.DocumentIdentityDigest(grant);
        Validate(RepositoryAuthorityProvider.SchemaId, grant);
        byte[] grantBytes = CanonicalJson.Encode(grant);
        string grantDigest = Digests.Sha256(grantBytes);
        ArtifactReference grantReference = new(
            binder.BindIdentity(grant["identity"]!.AsObject()),
            "application/vnd.program-kit.authority-grant+json",
            grantPath,
            grantDigest,
            ArtifactOwnership.SeededHandoff);

        RequirePublishable(workspaceRoot, grantPath, grantBytes);
        RequirePublishable(workspaceRoot, revocationPath, revocationBytes);

        NamespacedPublicationResult publication = new NamespacedArtifactSetPublisher().Publish(
            workspaceRoot,
            "authority-record",
            CanonicalJson.Digest(request),
            new[]
            {
                new NamespacedArtifact(grantPath, grantBytes),
                new NamespacedArtifact(revocationPath, revocationBytes),
            });
        return OperationResultFactory.Success(
            PublicCommand.AuthorityRecord,
            OperationPhase.Completion,
            publication.Changes.All(static change => change.Kind == "unchanged") ? EffectState.None : EffectState.Committed,
            requestIdentity: CanonicalJson.Digest(request),
            artifacts: new[] { grantReference, revocationReference },
            changes: publication.Changes,
            payload: new JsonObject
            {
                ["grant"] = ContractJson.Artifact(grantReference),
                ["revocation"] = ContractJson.Artifact(revocationReference),
                ["proposalDigest"] = proposal["digest"]!.DeepClone(),
                ["decisionDigest"] = decisionReference.Digest,
            });
    }

    private void ValidateCurrentProposal(string workspaceRoot, JsonObject proposal)
    {
        JsonObject prospectiveRequest = PreparationService.ProspectiveConstructRequest(proposal["ungrantedProjection"]!.AsObject());
        FactoryInput admitted = intake.AdmitAndMap(workspaceRoot, prospectiveRequest);
        ResolvedFactoryInput resolved = resolution.Resolve(admitted);
        if (!string.Equals(resolved.Lock.ClosureDigest, proposal["closureDigest"]!.GetValue<string>(), StringComparison.Ordinal)
            || !CanonicalJson.Encode(resolved.Explanation.CanonicalDocument).SequenceEqual(CanonicalJson.Encode(proposal["explanation"]!)))
            throw new InvalidDataException("The preparation closure or explanation is stale.");
        string liveState = PreparationService.ProspectiveLiveState(workspaceRoot, resolved.Explanation.CanonicalDocument);
        if (!string.Equals(liveState, proposal["liveStateDigest"]!.GetValue<string>(), StringComparison.Ordinal))
            throw new InvalidDataException("The preparation live-state precondition is stale.");
    }

    private void ValidateDecision(string workspaceRoot, JsonObject decision, JsonObject proposal)
    {
        if (!CanonicalJson.Encode(decision["subjects"]!).SequenceEqual(CanonicalJson.Encode(proposal["subjects"]!)))
            throw new UnauthorizedAccessException("The human decision subjects do not exactly match the prepared subjects.");
        JsonArray operations = decision["operations"]!.AsArray();
        if (operations.Count != 1 || operations[0]!.GetValue<string>() != proposal["operation"]!.GetValue<string>())
            throw new UnauthorizedAccessException("The human decision operation is missing, ambiguous, or widened.");
        JsonArray effects = decision["effects"]!.AsArray();
        if (effects.Count != 1 || !EffectAllowed(proposal["maximumEffect"]!.GetValue<string>(), effects[0]!.GetValue<string>()))
            throw new UnauthorizedAccessException("The human decision effect is missing, ambiguous, or widened.");

        JsonObject validity = decision["validity"]!.AsObject();
        DateTimeOffset notBefore = ParseInstant(Required(validity, "notBefore"));
        DateTimeOffset notAfter = ParseInstant(Required(validity, "notAfter"));
        DateTimeOffset evaluation = ParseInstant(proposal["ungrantedProjection"]!["evaluationContext"]!["instant"]!.GetValue<string>());
        if (notBefore >= notAfter || evaluation < notBefore || evaluation > notAfter)
            throw new UnauthorizedAccessException("The authority validity is not finite and current for the prepared evaluation instant.");

        ArtifactReference provenance = binder.BindArtifact(decision["provenance"]!.AsObject());
        RequireArtifactIdentity(provenance);
        JsonObject review = IntakePipeline.LoadExactArtifact(workspaceRoot, provenance);
        if (review["schema"]?.GetValue<string>() != "program-kit.spec-kit-handoff-review/v1"
            || review["decision"]?.GetValue<string>() != "approved")
            throw new UnauthorizedAccessException("The authority decision provenance is not one exact approved handoff review.");
    }

    private static JsonArray ProviderConditions(JsonObject proposal, string decisionDigest, string handle) => new(
        Condition("operation-closure", proposal["closureDigest"]!.GetValue<string>()),
        Condition("review-digest", decisionDigest),
        Condition("expected-live-state", proposal["liveStateDigest"]!.GetValue<string>()),
        Condition("revocation-handle", handle));

    private static JsonObject Condition(string kind, string digest) => new()
    {
        ["kind"] = kind,
        ["value"] = new JsonObject { ["classification"] = "public", ["valueKind"] = "digest", ["value"] = digest },
    };

    private static bool EffectAllowed(string maximum, string requested) => maximum == requested;

    private static void RequireSelfDigest(JsonObject document)
    {
        JsonObject material = (JsonObject)document.DeepClone();
        string declared = Required(material, "digest");
        material.Remove("digest");
        if (!string.Equals(declared, CanonicalJson.Digest(material), StringComparison.Ordinal))
            throw new InvalidDataException("The preparation proposal digest is not exact.");
    }

    private static void RequireArtifactIdentity(ArtifactReference artifact)
    {
        if (!string.Equals(artifact.Identity.Digest, artifact.Digest, StringComparison.Ordinal))
            throw new InvalidDataException("Referenced decision and preparation artifacts require exact byte-bound identities.");
    }

    private static void RequirePublishable(string workspaceRoot, string logicalPath, byte[] bytes)
    {
        string path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
        if (File.Exists(path) && !File.ReadAllBytes(path).SequenceEqual(bytes))
            throw new IOException("Repository authority recording refuses an existing non-exact target.");
    }

    private void Validate(string schemaId, JsonObject document)
    {
        IReadOnlyList<string> failures = structural.Validate(schemaId, document);
        if (failures.Count > 0) throw new InvalidDataException(string.Join(" | ", failures));
    }

    private static string Required(JsonObject document, string name) => document[name]?.GetValue<string>() is { Length: > 0 } value
        ? value
        : throw new InvalidDataException($"Authority field {name} is required.");

    private static DateTimeOffset ParseInstant(string value) => DateTimeOffset.ParseExact(
        value,
        "yyyy-MM-dd'T'HH:mm:ss'Z'",
        CultureInfo.InvariantCulture,
        DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);

    private static string NormalizeInstant(string value) => ParseInstant(value).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture);
}
