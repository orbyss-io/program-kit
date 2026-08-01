using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Authority;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Evidence;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Publication;
using Orbyss.ProgramKit.Kernel.Resolution;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class ConstructOperation
{
    private readonly IntakePipeline intake;
    private readonly ResolutionEngine resolution;
    private readonly RepositoryAuthorityProvider authority = new();
    private readonly CandidateArtifactSetBuilder candidates = new();
    private readonly RecoverablePublisher publisher = new();
    private readonly AdmissionService admission = new();

    private readonly RepositoryAuthorityGrantStore authorityGrants = new();
    public ConstructOperation(IntakePipeline intake, ResolutionEngine resolution)
    {
        this.intake = intake;
        this.resolution = resolution;
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        JsonObject document;
        try
        {
            document = intake.Load(requestPath);
            IReadOnlyList<string> missing = intake.MissingFields(document);
            if (missing.Count > 0)
            {
                Diagnostic missingDiagnostic = DiagnosticFactory.Create(
                    DiagnosticIds.MissingInput,
                    OperationPhase.Validation,
                    "factory-request",
                    $"Missing required input fields: {string.Join(", ", missing)}",
                    "No candidate was created.");
                return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.NeedsInput, OperationPhase.Validation, EffectState.None, PrimaryDisposition.ProvideInput, new[] { missingDiagnostic }, CanonicalJson.Digest(document));
            }

            FactoryInput input = intake.Bind(document);
            if (input.Operation != FactoryOperation.Construct || input.RequestedEffect == RequestedEffect.None || input.ConstructionMode is null)
            {
                throw new InvalidDataException("The request operation, effect, or construction mode conflicts with construct.");
            }

            string grantLogicalPath = input.AuthorityGrantLogicalPath ?? throw new UnauthorizedAccessException("Construct requires an exact request-bound authority grant artifact.");
            AuthorityDemand authorityDemand = new(input.WorkspaceIdentity, "construct", input.RequestedEffect, input.RequestCoreIdentity, input.ProviderSelection, "workspace", input.EvaluationInstant);
            RequestBoundAuthorityGrant grant = authorityGrants.Load(workspaceRoot, grantLogicalPath, authorityDemand);
            authority.Demand(authorityDemand, grant);
            ResolvedFactoryInput resolved = resolution.Resolve(input);
            string constructionIdentity = resolved.Lock.ConstructionIdentity
                ?? throw new InvalidOperationException("Construction identity is unavailable.");
            string candidateRoot = Path.Combine(workspaceRoot, ".program-kit", "candidates", constructionIdentity["sha256:".Length..]);
            if (Directory.Exists(candidateRoot))
            {
                Diagnostic interrupted = DiagnosticFactory.Create(
                    DiagnosticIds.InterruptedPublication,
                    OperationPhase.Construction,
                    ".program-kit/candidates",
                    "An exact candidate already exists and its recovery state has not been resolved.",
                    "Blind retry is refused; evaluate and authorize recovery or repair.");
                return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, OperationPhase.Construction, EffectState.CandidateOnly, PrimaryDisposition.Repair, new[] { interrupted }, resolved.Lock.RequestDigest, constructionIdentity);
            }

            Directory.CreateDirectory(candidateRoot);
            string stateRoot = Path.Combine(candidateRoot, ".program-kit");
            Directory.CreateDirectory(stateRoot);
            File.WriteAllBytes(Path.Combine(stateRoot, "resolution.lock.json"), CanonicalJson.Encode(resolved.Lock.CanonicalDocument));
            File.WriteAllBytes(Path.Combine(stateRoot, "integration-resolution.json"), CanonicalJson.Encode(resolved.Explanation.CanonicalDocument));

            string mirrorLogicalPath = input.Definition["dependencyMirror"]?.GetValue<string>()
                ?? throw new InvalidDataException("definition.dependencyMirror is required.");
            string dependencyMirror = LogicalPaths.ResolveInside(workspaceRoot, mirrorLogicalPath);
            ProviderConstructionResult providerResult = resolved.Provider.ConstructAsync(new ProviderConstructionContext(
                workspaceRoot,
                candidateRoot,
                dependencyMirror,
                input.Definition,
                constructionIdentity,
                System.Threading.CancellationToken.None)).GetAwaiter().GetResult();
            if (!providerResult.Succeeded)
            {
                Diagnostic[] providerDiagnostics = providerResult.Diagnostics.Select(id => DiagnosticFactory.Create(
                    id,
                    OperationPhase.Construction,
                    resolved.Provider.Manifest.Identity.StableKey,
                    "The exact provider reported a bounded construction failure.",
                    "No candidate was admitted or published.")).ToArray();
                return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, OperationPhase.Construction, EffectState.CandidateOnly, PrimaryDisposition.Revise, providerDiagnostics, resolved.Lock.RequestDigest, constructionIdentity);
            }

            CandidateArtifactSet preliminary = candidates.Seal(constructionIdentity, candidateRoot, providerResult.Artifacts);
            string evidenceDigest = Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', providerResult.Evidence.Select(CanonicalJson.Digest))));
            JsonObject snapshot = WorkspaceSnapshotBuilder.Build(resolved.Lock, preliminary, evidenceDigest);
            File.WriteAllBytes(Path.Combine(stateRoot, "workspace.snapshot.json"), CanonicalJson.Encode(snapshot));
            CandidateArtifactSet candidate = candidates.Seal(constructionIdentity, candidateRoot, providerResult.Artifacts);
            candidates.Rehash(candidate);

            ArtifactReference[] artifactReferences = candidate.Artifacts.Select(artifact => Reference(artifact, constructionIdentity)).ToArray();
            if (input.RequestedEffect == RequestedEffect.CandidateOnly)
            {
                authorityGrants.MarkConsumed(workspaceRoot, grant.GrantIdentity, input.RequestCoreIdentity);
                return OperationResultFactory.Success(
                    PublicCommand.Construct,
                    OperationPhase.Evaluation,
                    EffectState.CandidateOnly,
                    resolved.Lock.RequestDigest,
                    constructionIdentity,
                    artifacts: artifactReferences,
                    changes: candidate.Artifacts.Select(static item => new OperationChange("created", item.LogicalPath, EffectState.CandidateOnly)).ToArray());
            }

            PublicationResult publication = publisher.Publish(workspaceRoot, candidate, input.ConstructionMode.Value);
            string lockDigest = CanonicalJson.Digest(resolved.Lock.CanonicalDocument);
            string receiptDigest = admission.Admit(workspaceRoot, candidate, lockDigest, publication.LiveStateDigest);
            ArtifactReference receipt = new(
                new GovernedIdentity("orbyss.program-kit", "construction-receipt", input.WorkspaceIdentity, "1", receiptDigest),
                "application/json",
                ".program-kit/construction-receipt.json",
                receiptDigest,
                ArtifactOwnership.GeneratedOwned);
            authorityGrants.MarkConsumed(workspaceRoot, grant.GrantIdentity, input.RequestCoreIdentity);
            return OperationResultFactory.Success(
                PublicCommand.Construct,
                OperationPhase.Completion,
                EffectState.Committed,
                resolved.Lock.RequestDigest,
                constructionIdentity,
                artifacts: artifactReferences,
                receipts: new[] { receipt },
                changes: publication.Changes);
        }
        catch (UnauthorizedAccessException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.MissingAuthority,
                OperationPhase.Validation,
                "authority",
                exception.Message,
                "The requested effect was not authorized; no candidate or live output is trusted.");
            return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, OperationPhase.Validation, EffectState.None, PrimaryDisposition.RequestApproval, new[] { diagnostic });
        }
        catch (IOException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.Collision,
                OperationPhase.Publication,
                "workspace",
                exception.Message,
                "Publication did not receive a trusted admission receipt.");
            return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, OperationPhase.Publication, EffectState.Indeterminate, PrimaryDisposition.Repair, new[] { diagnostic });
        }
        catch (Exception exception) when (exception is InvalidDataException or InvalidOperationException or FormatException or System.Text.Json.JsonException or YamlDotNet.Core.YamlException)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.InvalidInput,
                OperationPhase.Validation,
                "factory-request",
                exception.Message,
                "Construction was refused before trusted admission.");
            return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, OperationPhase.Validation, EffectState.None, PrimaryDisposition.Revise, new[] { diagnostic });
        }
    }

    private static ArtifactReference Reference(ArtifactManifestEntry artifact, string constructionIdentity) => new(
        new GovernedIdentity("orbyss.program-kit", "generated-artifact", artifact.LogicalPath, constructionIdentity["sha256:".Length..20], artifact.Digest),
        artifact.MediaType,
        artifact.LogicalPath,
        artifact.Digest,
        artifact.Ownership);
}
