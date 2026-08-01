using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Authority;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Authority;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Evaluation;
using Orbyss.ProgramKit.Kernel.Evidence;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Publication;
using Orbyss.ProgramKit.Kernel.Resolution;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class ConstructOperation
{
    private readonly IntakePipeline intake;
    private readonly ResolutionEngine resolution;
    private readonly RepositoryAuthorityProvider authority;
    private readonly CandidateArtifactSetBuilder candidates;
    private readonly CandidateEvaluator candidateEvaluator;
    private readonly RecoverablePublisher publisher;
    private readonly AdmissionService admission;
    private readonly PublicationRecovery recovery;

    public ConstructOperation(
        IntakePipeline intake,
        ResolutionEngine resolution,
        RepositoryAuthorityProvider? authority = null,
        CandidateArtifactSetBuilder? candidates = null,
        CandidateEvaluator? candidateEvaluator = null,
        RecoverablePublisher? publisher = null,
        AdmissionService? admission = null,
        PublicationRecovery? recovery = null)
    {
        this.intake = intake;
        this.resolution = resolution;
        this.authority = authority ?? new RepositoryAuthorityProvider();
        this.candidates = candidates ?? new CandidateArtifactSetBuilder();
        this.candidateEvaluator = candidateEvaluator ?? new CandidateEvaluator();
        this.publisher = publisher ?? new RecoverablePublisher();
        this.admission = admission ?? new AdmissionService();
        this.recovery = recovery ?? new PublicationRecovery();
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        OperationPhase phase = OperationPhase.Request;
        EffectState effect = EffectState.None;
        string? requestIdentity = null;
        bool recoveredPublication = false;
        string? constructionIdentity = null;
        try
        {
            JsonObject document = intake.Load(requestPath);
            requestIdentity = CanonicalJson.Digest(document);
            IReadOnlyList<string> missing = intake.MissingFields(document);
            if (missing.Count > 0)
            {
                Diagnostic missingDiagnostic = DiagnosticFactory.Create(
                    DiagnosticIds.MissingInput,
                    OperationPhase.Validation,
                    DisclosureFilter.PublicText("factory-request"),
                    DisclosureFilter.PublicText($"Missing required input fields: {string.Join(", ", missing)}"),
                    DisclosureFilter.PublicText("No candidate was created."));
                return OperationResultFactory.Failure(
                    PublicCommand.Construct,
                    OperationOutcome.NeedsInput,
                    OperationPhase.Validation,
                    EffectState.None,
                    PrimaryDisposition.ProvideInput,
                    new[] { missingDiagnostic },
                    requestIdentity,
                    continuation: ContinuationBuilder.ForMissing(requestIdentity, missing));
            }

            phase = OperationPhase.Intake;
            OperationExecutionTracker.Advance(phase, effect);
            FactoryInput input = intake.AdmitAndMap(workspaceRoot, document);
            requestIdentity = input.RequestDigest;
            if (input.Request.Operation != FactoryOperation.Construct
                || input.Request.RequestedEffect == RequestedEffect.None
                || input.Request.ConstructionMode is null
                || input.Request.ExpectedState is null)
            {
                throw new InvalidDataException("The request operation, effect, construction mode, or expected state conflicts with construct.");
            }

            phase = OperationPhase.Resolution;
            OperationExecutionTracker.Advance(phase, effect);
            ResolvedFactoryInput resolved = resolution.Resolve(input);
            constructionIdentity = resolved.Lock.ConstructionIdentity
                ?? throw new InvalidOperationException("Construction identity is unavailable.");
            phase = OperationPhase.Validation;
            OperationExecutionTracker.Advance(phase, effect);
            AuthorityDecision authorityDecision = authority.Demand(workspaceRoot, input, resolved.Lock);

            PublicationRecoveryState? interrupted = recovery.Inspect(workspaceRoot);
            if (interrupted?.State is "prepared" or "publishing" or "incomplete" or "published-unadmitted")
            {
                if (input.Request.ConstructionMode != ConstructionMode.Repair)
                {
                    return InterruptedResult(requestIdentity, constructionIdentity, interrupted.Effect);
                }

                phase = OperationPhase.Publication;
                OperationExecutionTracker.Advance(phase, EffectState.Indeterminate);
                recovery.Recover(workspaceRoot, PublicationRecoveryStrategy.Rollback, ConstructionMode.Repair);
                recoveredPublication = true;
                effect = EffectState.None;
                OperationExecutionTracker.Advance(phase, effect);
            }

            if (input.Request.ConstructionMode == ConstructionMode.Repair && !recoveredPublication)
            {
                ValidateRepairPrecondition(workspaceRoot, input.Request.ExpectedState.LiveStateDigest);
            }

            string candidateRoot = Path.Combine(workspaceRoot, ".program-kit", "candidates", constructionIdentity["sha256:".Length..]);
            if (Directory.Exists(candidateRoot))
            {
                return InterruptedResult(requestIdentity, constructionIdentity, EffectState.CandidateOnly);
            }

            phase = OperationPhase.Construction;
            OperationExecutionTracker.Advance(phase, effect);
            Directory.CreateDirectory(candidateRoot);
            effect = EffectState.CandidateOnly;
            OperationExecutionTracker.Advance(phase, effect);
            string stateRoot = Path.Combine(candidateRoot, ".program-kit");
            Directory.CreateDirectory(stateRoot);
            File.WriteAllBytes(Path.Combine(stateRoot, "resolution.lock.json"), CanonicalJson.Encode(resolved.Lock.CanonicalDocument));
            File.WriteAllBytes(Path.Combine(stateRoot, "integration-resolution.json"), CanonicalJson.Encode(resolved.Explanation.CanonicalDocument));

            string mirrorLogicalPath = input.Definition["dependencyMirror"]?.GetValue<string>()
                ?? throw new InvalidDataException("definition.dependencyMirror is required.");
            string dependencyMirror = LogicalPaths.ResolveInside(workspaceRoot, mirrorLogicalPath);
            ProviderConstructionResult providerResult = ProviderInvocation.Invoke(() => resolved.ConstructionProvider.ConstructAsync(new ProviderConstructionContext(
                workspaceRoot,
                candidateRoot,
                dependencyMirror,
                input.Definition,
                constructionIdentity,
                System.Threading.CancellationToken.None)), phase);
            if (!providerResult.Succeeded)
            {
                return ProviderFailure(resolved, providerResult.Diagnostics, requestIdentity, constructionIdentity, phase, effect);
            }

            phase = OperationPhase.Evaluation;
            OperationExecutionTracker.Advance(phase, effect);
            ProviderEvaluationResult providerEvaluation = ProviderInvocation.Invoke(() => resolved.EvaluationProvider.EvaluateAsync(new ProviderEvaluationContext(
                workspaceRoot,
                input.Definition,
                resolved.Lock.ClosureDigest,
                constructionIdentity,
                System.Threading.CancellationToken.None)), phase);
            if (!providerEvaluation.Succeeded)
            {
                return ProviderFailure(resolved, providerEvaluation.Diagnostics, requestIdentity, constructionIdentity, phase, effect);
            }

            JsonObject providerEvidence = new()
            {
                ["schema"] = "program-kit.provider-evidence/v1",
                ["canonicalProfile"] = CanonicalJson.Profile,
                ["constructionIdentity"] = constructionIdentity,
                ["closureDigest"] = resolved.Lock.ClosureDigest,
                ["provider"] = ContractJson.Identity(resolved.ConstructionProvider.Manifest.Identity),
                ["distribution"] = ContractJson.Identity(resolved.ConstructionProvider.Manifest.Distribution),
                ["construction"] = new JsonArray(providerResult.Evidence.Select(static item => item.DeepClone()).ToArray()),
                ["evaluation"] = new JsonArray(providerEvaluation.Evidence.Select(static item => item.DeepClone()).ToArray()),
            };
            File.WriteAllBytes(Path.Combine(stateRoot, "provider-evidence.json"), CanonicalJson.Encode(providerEvidence));
            ProviderArtifact[] kernelArtifacts =
            {
                new(
                    ".program-kit/resolution.lock.json",
                    ArtifactOwnership.GeneratedOwned,
                    "application/json",
                    ClaimClass.CanonicalByte,
                    "orbyss.program-kit:kernel"),
                new(
                    ".program-kit/integration-resolution.json",
                    ArtifactOwnership.GeneratedOwned,
                    "application/json",
                    ClaimClass.CanonicalByte,
                    "orbyss.program-kit:kernel"),
                new(
                    ".program-kit/provider-evidence.json",
                    ArtifactOwnership.GeneratedOwned,
                    "application/json",
                    ClaimClass.VerifiedEquivalent,
                    "orbyss.program-kit:kernel"),
            };
            CandidateArtifactSet candidate = candidates.Seal(
                constructionIdentity,
                candidateRoot,
                providerResult.Artifacts.Concat(kernelArtifacts).ToArray());
            DeterminismGuard.EnsureCompatibleWithAdmittedCanonicalBytes(workspaceRoot, candidate);
            CandidateEvaluation evaluation = candidateEvaluator.Evaluate(candidate, resolved, providerResult, providerEvaluation);
            if (!evaluation.Passed)
            {
                Diagnostic diagnostic = DiagnosticFactory.Create(
                    DiagnosticIds.GateFailed,
                    OperationPhase.Evaluation,
                    DisclosureFilter.PublicText("candidate-artifact-set"),
                    DisclosureFilter.PublicText("One or more mandatory candidate gates did not pass."),
                    DisclosureFilter.PublicText("The candidate remains isolated and cannot be published or admitted."));
                return OperationResultFactory.Failure(
                    PublicCommand.Construct,
                    OperationOutcome.Blocked,
                    OperationPhase.Evaluation,
                    EffectState.CandidateOnly,
                    PrimaryDisposition.Revise,
                    new[] { diagnostic },
                    requestIdentity,
                    constructionIdentity);
            }

            ArtifactReference[] artifactReferences = candidate.Artifacts.Select(artifact => Reference(artifact, constructionIdentity)).ToArray();
            EvidenceReference resultEvidence = ResultEvidence(candidate, evaluation, resolved);
            if (input.Request.RequestedEffect == RequestedEffect.CandidateOnly)
            {
                return OperationResultFactory.Success(
                    PublicCommand.Construct,
                    OperationPhase.Evaluation,
                    EffectState.CandidateOnly,
                    requestIdentity,
                    constructionIdentity,
                    artifacts: artifactReferences,
                    evidence: new[] { resultEvidence },
                    changes: candidate.Artifacts.Select(static item => new OperationChange("created", item.LogicalPath, EffectState.CandidateOnly)).ToArray());
            }

            phase = OperationPhase.Publication;
            OperationExecutionTracker.Advance(phase, EffectState.Indeterminate);
            PublicationResult publication = publisher.Publish(
                workspaceRoot,
                candidate,
                input.Request.ConstructionMode.Value,
                recoveredPublication ? LiveState.Compute(workspaceRoot, candidate.Artifacts) : input.Request.ExpectedState.LiveStateDigest);
            effect = EffectState.Indeterminate;
            string lockDigest = CanonicalJson.Digest(resolved.Lock.CanonicalDocument);
            ExactSelection profile = input.Request.Selections.Single(static item => item.Role == "target-profile");
            PreparedAdmission prepared = admission.Prepare(
                workspaceRoot,
                candidate,
                lockDigest,
                publication.LiveStateDigest,
                evaluation,
                profile.Selected);
            JsonObject snapshot = WorkspaceSnapshotBuilder.Build(
                workspaceRoot,
                resolved,
                candidate,
                evaluation,
                authorityDecision,
                prepared,
                DiagnosticFactory.View(Array.Empty<Diagnostic>()).FullCollectionDigest);
            phase = OperationPhase.Admission;
            OperationExecutionTracker.Advance(phase, effect);
            if (input.Request.ConstructionMode == ConstructionMode.Repair)
            {
                ArchivePriorAdmission(workspaceRoot);
            }

            ArtifactReference receipt = admission.Admit(
                workspaceRoot,
                candidate,
                publication.LiveStateDigest,
                evaluation,
                prepared,
                snapshot);
            effect = EffectState.Committed;
            OperationExecutionTracker.Advance(phase, effect);
            string snapshotPath = Path.Combine(workspaceRoot, ".program-kit", "workspace.snapshot.json");
            string snapshotDigest = Digests.Sha256(File.ReadAllBytes(snapshotPath));
            ArtifactReference snapshotReference = new(
                new GovernedIdentity("orbyss.program-kit", "workspace-snapshot", input.Request.WorkspaceIdentity.Name, "1", snapshotDigest),
                "application/json",
                ".program-kit/workspace.snapshot.json",
                snapshotDigest,
                ArtifactOwnership.GeneratedOwned);
            return OperationResultFactory.Success(
                PublicCommand.Construct,
                OperationPhase.Completion,
                EffectState.Committed,
                requestIdentity,
                constructionIdentity,
                artifacts: artifactReferences.Append(snapshotReference).ToArray(),
                receipts: new[] { receipt },
                evidence: new[] { resultEvidence },
                changes: publication.Changes.Append(new OperationChange("created", snapshotReference.LogicalPath, EffectState.Committed)).ToArray());
        }
        catch (ProgramKitDiagnosticException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                exception.DiagnosticId,
                exception.Phase,
                DisclosureFilter.PublicText("factory-operation"),
                DisclosureFilter.Withhold(exception.Message, "diagnostic-exception-detail"),
                DisclosureFilter.PublicText("No trusted completion is claimed; follow the typed remediation and disposition."));
            return OperationResultFactory.Failure(
                PublicCommand.Construct, OperationOutcome.Blocked, exception.Phase, effect,
                exception.Disposition, new[] { diagnostic }, requestIdentity, constructionIdentity);
        }
        catch (PublicationInterruptedException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.InterruptedPublication,
                OperationPhase.Publication,
                DisclosureFilter.RepositoryRelative(".program-kit/publication.journal.json"),
                DisclosureFilter.Withhold(exception.Message, "publication-interruption-detail"),
                DisclosureFilter.PublicText("No admission receipt was issued; evaluation is read-only and a fresh authorized repair must recover the journal."));
            return OperationResultFactory.Failure(
                PublicCommand.Construct,
                OperationOutcome.Blocked,
                OperationPhase.Publication,
                exception.ProvenEffect,
                PrimaryDisposition.Repair,
                new[] { diagnostic },
                requestIdentity,
                constructionIdentity);
        }
        catch (UnauthorizedAccessException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.MissingAuthority,
                phase,
                DisclosureFilter.PublicText("authority"),
                DisclosureFilter.Withhold(exception.Message, "authority-failure-detail"),
                DisclosureFilter.PublicText("The requested effect was not authorized; no candidate or live output is trusted."));
            return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, phase, effect, PrimaryDisposition.RequestApproval, new[] { diagnostic }, requestIdentity, constructionIdentity);
        }
        catch (IOException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.Collision,
                phase,
                DisclosureFilter.PublicText("workspace"),
                DisclosureFilter.Withhold(exception.Message, "workspace-io-detail"),
                DisclosureFilter.PublicText("Publication did not receive a trusted admission receipt."));
            return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, phase, effect, PrimaryDisposition.Repair, new[] { diagnostic }, requestIdentity, constructionIdentity);
        }
        catch (Exception exception) when (exception is InvalidDataException or InvalidOperationException or FormatException or System.Text.Json.JsonException or YamlDotNet.Core.YamlException)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.InvalidInput,
                phase,
                DisclosureFilter.PublicText("factory-request"),
                DisclosureFilter.Withhold(exception.Message, "construction-failure-detail"),
                DisclosureFilter.PublicText("Construction was refused before trusted admission."));
            return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, phase, effect, PrimaryDisposition.Revise, new[] { diagnostic }, requestIdentity, constructionIdentity);
        }
    }

    private static OperationResult ProviderFailure(
        ResolvedFactoryInput resolved,
        IReadOnlyList<string> diagnosticIds,
        string requestIdentity,
        string constructionIdentity,
        OperationPhase phase,
        EffectState effect)
    {
        Diagnostic[] diagnostics = diagnosticIds.Select(id => DiagnosticFactory.Create(
            id,
            phase,
            DisclosureFilter.PublicText(resolved.ConstructionProvider.Manifest.Identity.StableKey),
            DisclosureFilter.PublicText("The exact provider reported a bounded failure."),
            DisclosureFilter.PublicText("No candidate was admitted or published."))).ToArray();
        return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, phase, effect, DiagnosticFactory.PrimaryDispositionFor(diagnostics), diagnostics, requestIdentity, constructionIdentity);
    }

    private static OperationResult InterruptedResult(string requestIdentity, string constructionIdentity, EffectState effect)
    {
        Diagnostic interrupted = DiagnosticFactory.Create(
            DiagnosticIds.InterruptedPublication,
            OperationPhase.Publication,
            DisclosureFilter.RepositoryRelative(".program-kit/publication.journal.json"),
            DisclosureFilter.PublicText("Unresolved candidate or publication state is present."),
            DisclosureFilter.PublicText("Blind retry is refused; evaluate and submit a fresh authorized repair request."));
        return OperationResultFactory.Failure(PublicCommand.Construct, OperationOutcome.Blocked, OperationPhase.Publication, effect, PrimaryDisposition.Repair, new[] { interrupted }, requestIdentity, constructionIdentity);
    }

    private static void ValidateRepairPrecondition(string workspaceRoot, string expectedLiveState)
    {
        string receiptPath = Path.Combine(workspaceRoot, ".program-kit", "construction-receipt.json");
        if (!File.Exists(receiptPath))
        {
            throw new IOException("Repair requires an exact prior admission receipt.");
        }

        JsonObject receipt = CanonicalJson.Parse(File.ReadAllBytes(receiptPath)) as JsonObject
            ?? throw new InvalidDataException("The prior admission receipt is invalid.");
        IReadOnlyList<ArtifactObservation> observations = new WorkspaceEvaluator().Evaluate(workspaceRoot, receipt);
        string observedLiveState = LiveState.ComputeObserved(observations.Select(static item => (item.LogicalPath, item.ObservedDigest)));
        if (!string.Equals(observedLiveState, expectedLiveState, StringComparison.Ordinal))
        {
            throw new IOException("Repair live-state precondition is stale.");
        }
    }

    private static void ArchivePriorAdmission(string workspaceRoot)
    {
        string stateRoot = Path.Combine(workspaceRoot, ".program-kit");
        string receiptPath = Path.Combine(stateRoot, "construction-receipt.json");
        string historyRoot = Path.Combine(stateRoot, "history");
        Directory.CreateDirectory(historyRoot);
        if (File.Exists(receiptPath))
        {
            string digest = Digests.Sha256(File.ReadAllBytes(receiptPath));
            File.Move(receiptPath, Path.Combine(historyRoot, $"construction-receipt-{digest["sha256:".Length..]}.json"), overwrite: false);
        }

        string snapshotPath = Path.Combine(stateRoot, "workspace.snapshot.json");
        if (File.Exists(snapshotPath))
        {
            string digest = Digests.Sha256(File.ReadAllBytes(snapshotPath));
            File.Move(snapshotPath, Path.Combine(historyRoot, $"workspace-snapshot-{digest["sha256:".Length..]}.json"), overwrite: false);
        }
    }

    private static EvidenceReference ResultEvidence(CandidateArtifactSet candidate, CandidateEvaluation evaluation, ResolvedFactoryInput resolved)
    {
        GovernedIdentity subject = new("orbyss.program-kit", "candidate-artifact-set", candidate.ConstructionIdentity["sha256:".Length..20], "1", candidate.SetDigest);
        ExactSelection profile = resolved.Input.Request.Selections.Single(static item => item.Role == "target-profile");
        return new EvidenceReference(
            ContractJson.StableIdentity("orbyss.program-kit", "candidate-evaluation", candidate.ConstructionIdentity["sha256:".Length..20], "1", evaluation.EvidenceDigest),
            subject,
            profile.Selected,
            evaluation.EvidenceArtifact,
            "current");
    }

    private static ArtifactReference Reference(ArtifactManifestEntry artifact, string constructionIdentity) => new(
        new GovernedIdentity("orbyss.program-kit", "generated-artifact", artifact.LogicalPath, constructionIdentity["sha256:".Length..20], artifact.Digest),
        artifact.MediaType,
        artifact.LogicalPath,
        artifact.Digest,
        artifact.Ownership);
}
