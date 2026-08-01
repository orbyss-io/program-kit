using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Evaluation;
using Orbyss.ProgramKit.Kernel.Evidence;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Publication;
using Orbyss.ProgramKit.Kernel.Resolution;
using Orbyss.ProgramKit.Kernel.Validation;
using static Orbyss.ProgramKit.Kernel.Operations.PublicationRepairGuidance;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class EvaluateOperation
{
    private const string ReceiptSchema = "https://schemas.program-kit.dev/v1/construction-receipt.schema.json";
    private readonly IntakePipeline intake;
    private readonly ResolutionEngine resolution;
    private readonly WorkspaceEvaluator evaluator = new();
    private readonly PublicationRecovery recovery = new();
    private readonly StructuralSchemaValidator structural = new(new SchemaRegistry());
    private readonly TypedContractBinder binder = new();

    public EvaluateOperation(IntakePipeline intake, ResolutionEngine resolution)
    {
        this.intake = intake;
        this.resolution = resolution;
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        OperationPhase phase = OperationPhase.Request;
        string? requestIdentity = null;
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
                    "factory-request",
                    $"Missing required input fields: {string.Join(", ", missing)}",
                    "Evaluation did not mutate the workspace.");
                return OperationResultFactory.Failure(
                    PublicCommand.Evaluate,
                    OperationOutcome.NeedsInput,
                    OperationPhase.Validation,
                    EffectState.None,
                    PrimaryDisposition.ProvideInput,
                    new[] { missingDiagnostic },
                    requestIdentity,
                    continuation: ContinuationBuilder.ForMissing(requestIdentity, missing));
            }

            phase = OperationPhase.Intake;
            OperationExecutionTracker.Advance(phase, EffectState.None);
            FactoryInput input = intake.AdmitAndMap(workspaceRoot, document);
            requestIdentity = input.RequestDigest;
            if (input.Request.Operation != FactoryOperation.Evaluate || input.Request.RequestedEffect != RequestedEffect.None)
            {
                throw new InvalidDataException("The request operation/effect conflicts with evaluate.");
            }

            phase = OperationPhase.Resolution;
            OperationExecutionTracker.Advance(phase, EffectState.None);
            ResolvedFactoryInput resolved = resolution.Resolve(input);
            ProviderEvaluationResult providerEvaluation = resolved.EvaluationProvider.EvaluateAsync(new ProviderEvaluationContext(
                workspaceRoot,
                input.Definition,
                resolved.Lock.ClosureDigest,
                null,
                System.Threading.CancellationToken.None)).GetAwaiter().GetResult();
            if (!providerEvaluation.Succeeded)
            {
                Diagnostic unsupported = DiagnosticFactory.Create(
                    DiagnosticIds.Incompatible,
                    OperationPhase.Evaluation,
                    resolved.EvaluationProvider.Manifest.Identity.StableKey,
                    "The exact selected evaluation provider cannot evaluate the resolved input.",
                    "Workspace support is unsupported; evaluation made no changes.");
                return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Revise, new[] { unsupported }, requestIdentity);
            }

            phase = OperationPhase.Evaluation;
            OperationExecutionTracker.Advance(phase, EffectState.None);
            PublicationRecoveryState? publicationState = recovery.Inspect(workspaceRoot);
            if (publicationState?.State is "prepared" or "publishing" or "incomplete" or "published-unadmitted")
            {
                JsonObject recoveryRequest = BuildRepair(workspaceRoot, document, ObservedPublicationLiveState(workspaceRoot));
                Diagnostic interrupted = DiagnosticFactory.Create(
                    DiagnosticIds.InterruptedPublication,
                    OperationPhase.Evaluation,
                    ".program-kit/publication.journal.json",
                    "The durable publication journal is incomplete.",
                    "Evaluation is read-only; a fresh explicitly authorized repair must recover or roll back publication.",
                    remediations: new[] { RecoveryRemediation(recoveryRequest) });
                return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Repair, new[] { interrupted }, requestIdentity, publicationState.ConstructionIdentity);
            }

            string receiptPath = Path.Combine(workspaceRoot, ".program-kit", "construction-receipt.json");
            if (!File.Exists(receiptPath))
            {
                Diagnostic unavailable = DiagnosticFactory.Create(
                    DiagnosticIds.ExternalUnavailable,
                    OperationPhase.Evaluation,
                    ".program-kit/construction-receipt.json",
                    "No admitted construction receipt is available.",
                    "Current trusted workspace state cannot be proven.");
                return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Stop, new[] { unavailable }, requestIdentity);
            }

            JsonObject receipt = CanonicalJson.Parse(File.ReadAllBytes(receiptPath)) as JsonObject
                ?? throw new InvalidDataException("Construction receipt is invalid.");
            if (structural.Validate(ReceiptSchema, receipt).Count > 0)
            {
                throw new InvalidDataException("Construction receipt does not conform to its exact public contract.");
            }

            WorkspaceEvaluation evaluation = evaluator.EvaluateDetailed(workspaceRoot, receipt);
            string constructionIdentity = receipt["constructionIdentity"]?.GetValue<string>()
                ?? throw new InvalidDataException("Construction receipt identity is unavailable.");
            ArtifactReference receiptReference = new(
                new GovernedIdentity("orbyss.program-kit", "construction-receipt", constructionIdentity["sha256:".Length..20], "1", Digests.Sha256(File.ReadAllBytes(receiptPath))),
                "application/json",
                ".program-kit/construction-receipt.json",
                Digests.Sha256(File.ReadAllBytes(receiptPath)),
                ArtifactOwnership.GeneratedOwned);
            EvidenceReference[] evidence = ReceiptEvidence(receipt);

            string snapshotPath = Path.Combine(workspaceRoot, ".program-kit", "workspace.snapshot.json");
            if (!File.Exists(snapshotPath))
            {
                Diagnostic unavailable = DiagnosticFactory.Create(
                    DiagnosticIds.ExternalUnavailable,
                    OperationPhase.Evaluation,
                    ".program-kit/workspace.snapshot.json",
                    "The admitted workspace snapshot is unavailable.",
                    "Orientation and freshness cannot be proven; evaluation made no changes.");
                return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Stop, new[] { unavailable }, requestIdentity, constructionIdentity, receipts: new[] { receiptReference }, evidence: evidence);
            }

            JsonObject snapshot = CanonicalJson.Parse(File.ReadAllBytes(snapshotPath)) as JsonObject
                ?? throw new InvalidDataException("Workspace snapshot is invalid.");
            string lockPath = Path.Combine(workspaceRoot, ".program-kit", "resolution.lock.json");
            if (!File.Exists(lockPath)
                || !string.Equals(Digests.Sha256(File.ReadAllBytes(lockPath)), receipt["lockDigest"]?.GetValue<string>(), StringComparison.Ordinal))
            {
                Diagnostic stale = DiagnosticFactory.Create(
                    DiagnosticIds.StaleSnapshot,
                    OperationPhase.Evaluation,
                    ".program-kit/resolution.lock.json",
                    "The authoritative resolution lock is unavailable or changed.",
                    "The prior snapshot is stale and evaluation made no changes.");
                return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Retry, new[] { stale }, requestIdentity, constructionIdentity, receipts: new[] { receiptReference }, evidence: evidence);
            }

            JsonObject admittedLock = CanonicalJson.Parse(File.ReadAllBytes(lockPath)) as JsonObject
                ?? throw new InvalidDataException("Resolution lock is invalid.");
            string closureDigest = admittedLock["closureDigest"]?.GetValue<string>()
                ?? throw new InvalidDataException("Resolution lock closure is unavailable.");
            string freshness = WorkspaceSnapshotBuilder.RecomputeFreshness(
                snapshot,
                closureDigest,
                evaluation.EvidenceDigest,
                evaluation.Artifacts,
                evaluation.SupportAvailable,
                evaluation.ReceiptAvailable,
                evaluation.Interrupted);
            ArtifactObservation[] nonExact = evaluation.Artifacts.Where(static item => item.State != "exact").ToArray();
            if (nonExact.Length == 0 && freshness == "current")
            {
                return OperationResultFactory.Success(
                    PublicCommand.Evaluate,
                    OperationPhase.Completion,
                    EffectState.None,
                    requestIdentity,
                    constructionIdentity,
                    receipts: new[] { receiptReference },
                    evidence: evidence);
            }

            if (nonExact.Length == 0)
            {
                string id = freshness == "stale" ? DiagnosticIds.StaleSnapshot : DiagnosticIds.ExternalUnavailable;
                PrimaryDisposition disposition = freshness == "stale" ? PrimaryDisposition.Retry : PrimaryDisposition.Stop;
                Diagnostic diagnostic = DiagnosticFactory.Create(
                    id,
                    OperationPhase.Evaluation,
                    ".program-kit/workspace.snapshot.json",
                    $"Workspace snapshot freshness is {freshness}.",
                    "The snapshot was not rewritten; currentness must be re-established from authoritative records.");
                return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, disposition, new[] { diagnostic }, requestIdentity, constructionIdentity, receipts: new[] { receiptReference }, evidence: evidence);
            }

            bool repairable = nonExact.All(static item => item.State is "missing" or "modified" && item.Ownership == "generated-owned");
            JsonObject? repairRequest = repairable ? BuildRepair(workspaceRoot, document, evaluation.LiveStateDigest) : null;
            Diagnostic[] diagnostics = nonExact.Select(item => DiagnosticFactory.Create(
                item.State switch
                {
                    "colliding" => DiagnosticIds.Collision,
                    "unavailable" or "unsupported" => DiagnosticIds.ExternalUnavailable,
                    "stale" => DiagnosticIds.StaleSnapshot,
                    _ => DiagnosticIds.GeneratedDrift,
                },
                OperationPhase.Evaluation,
                item.LogicalPath,
                $"Expected {item.ExpectedDigest}; observed {item.ObservedDigest ?? item.State}.",
                repairable
                    ? "The admitted construction is no longer exact and requires a separately authorized repair."
                    : "The state cannot be overwritten safely; revise consumer intent or restore authoritative evidence.",
                remediations: repairRequest is null ? null : new[] { RepairRemediation(item.LogicalPath, repairRequest) })).ToArray();
            return OperationResultFactory.Failure(
                PublicCommand.Evaluate,
                OperationOutcome.Blocked,
                OperationPhase.Evaluation,
                EffectState.None,
                repairable ? PrimaryDisposition.Repair : PrimaryDisposition.Revise,
                diagnostics,
                requestIdentity,
                constructionIdentity,
                receipts: new[] { receiptReference },
                evidence: evidence);
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or InvalidOperationException or KeyNotFoundException or System.Text.Json.JsonException or YamlDotNet.Core.YamlException)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.InvalidInput,
                phase,
                "factory-request",
                exception.Message,
                "Evaluation returned no mutation and no trusted exact-state claim.");
            return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, phase, EffectState.None, PrimaryDisposition.Revise, new[] { diagnostic }, requestIdentity);
        }
    }

    private JsonObject BuildRepair(string workspaceRoot, JsonObject evaluationRequest, string liveStateDigest)
    {
        JsonObject repair = RepairProposalBuilder.Build(evaluationRequest, Digests.Sha256(Array.Empty<byte>()), liveStateDigest);
        FactoryInput repairInput = intake.AdmitAndMap(workspaceRoot, repair);
        ResolvedFactoryInput repairResolution = resolution.Resolve(repairInput);
        ((JsonObject)repair["expectedState"]!)["closureDigest"] = repairResolution.Lock.ClosureDigest;
        return repair;
    }

    private static Remediation RepairRemediation(string logicalPath, JsonObject repairRequest) => new(
        "repair",
        new[] { logicalPath },
        new[] { "fresh-evaluation", "generated-owned-only", "exact-authority-required" },
        RequestedEffect.Committed,
        new[] { "human-approved-repository-record" },
        repairRequest,
        null,
        new[] { "generated-owned-artifacts-match-new-receipt", "consumer-owned-bytes-unchanged" },
        OperationPhase.Construction);

    private EvidenceReference[] ReceiptEvidence(JsonObject receipt)
    {
        JsonObject? verification = (receipt["artifacts"] as JsonArray)?.OfType<JsonObject>().Select(static entry => entry["verification"] as JsonObject).FirstOrDefault(static item => item is not null);
        if (verification is null)
        {
            return Array.Empty<EvidenceReference>();
        }

        return new[]
        {
            new EvidenceReference(
                binder.BindIdentity((JsonObject)verification["identity"]!),
                binder.BindIdentity((JsonObject)verification["subject"]!),
                binder.BindIdentity((JsonObject)verification["profile"]!),
                binder.BindArtifact((JsonObject)verification["artifact"]!),
                verification["freshness"]!.GetValue<string>()),
        };
    }
}
