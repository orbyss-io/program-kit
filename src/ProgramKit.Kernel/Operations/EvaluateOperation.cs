using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Evaluation;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Resolution;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class EvaluateOperation
{
    private readonly IntakePipeline intake;
    private readonly ResolutionEngine resolution;
    private readonly WorkspaceEvaluator evaluator = new();

    public EvaluateOperation(IntakePipeline intake, ResolutionEngine resolution)
    {
        this.intake = intake;
        this.resolution = resolution;
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        try
        {
            JsonObject document = intake.Load(requestPath);
            FactoryInput input = intake.Bind(document);
            if (input.Operation != FactoryOperation.Evaluate || input.RequestedEffect != RequestedEffect.None)
            {
                throw new InvalidDataException("The request operation/effect conflicts with evaluate.");
            }

            ResolvedFactoryInput resolved = resolution.Resolve(input);
            string receiptPath = Path.Combine(workspaceRoot, ".program-kit", "construction-receipt.json");
            if (!File.Exists(receiptPath))
            {
                Diagnostic unavailable = DiagnosticFactory.Create(
                    DiagnosticIds.ExternalUnavailable,
                    OperationPhase.Evaluation,
                    ".program-kit/construction-receipt.json",
                    "No admitted construction receipt is available.",
                    "Current trusted workspace state cannot be proven.");
                return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Stop, new[] { unavailable }, resolved.Lock.RequestDigest);
            }

            JsonObject receipt = CanonicalJson.Parse(File.ReadAllBytes(receiptPath)) as JsonObject
                ?? throw new InvalidDataException("Construction receipt is invalid.");
            IReadOnlyList<ArtifactObservation> observations = evaluator.Evaluate(workspaceRoot, receipt);
            ArtifactObservation[] drifted = observations.Where(static item => item.State != "exact").ToArray();
            if (drifted.Length == 0)
            {
                return OperationResultFactory.Success(
                    PublicCommand.Evaluate,
                    OperationPhase.Completion,
                    EffectState.None,
                    resolved.Lock.RequestDigest,
                    receipt["constructionIdentity"]?.GetValue<string>());
            }

            JsonObject repairRequest = RepairProposalBuilder.Build(document);
            Remediation remediation = new(
                "repair",
                drifted.Select(static item => item.LogicalPath).ToArray(),
                new[] { "fresh-evaluation", "generated-owned-only", "exact-authority-required" },
                RequestedEffect.Committed,
                new[] { "human-approved-repository-record" },
                repairRequest,
                null,
                new[] { "all-generated-owned-artifacts-match-new-receipt", "consumer-owned-bytes-unchanged" },
                OperationPhase.Construction);
            Diagnostic[] diagnostics = drifted.Select(item => DiagnosticFactory.Create(
                DiagnosticIds.GeneratedDrift,
                OperationPhase.Evaluation,
                item.LogicalPath,
                $"Expected {item.ExpectedDigest}; observed {item.ObservedDigest ?? "missing"}.",
                "The admitted construction is no longer exact and cannot be silently repaired.",
                remediations: new[] { remediation })).ToArray();
            return OperationResultFactory.Failure(
                PublicCommand.Evaluate,
                OperationOutcome.Blocked,
                OperationPhase.Evaluation,
                EffectState.None,
                PrimaryDisposition.Repair,
                diagnostics,
                resolved.Lock.RequestDigest,
                receipt["constructionIdentity"]?.GetValue<string>());
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or InvalidOperationException or System.Text.Json.JsonException or YamlDotNet.Core.YamlException)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.InvalidInput,
                OperationPhase.Evaluation,
                "factory-request",
                exception.Message,
                "Evaluation returned no mutation and no trusted exact-state claim.");
            return OperationResultFactory.Failure(PublicCommand.Evaluate, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Revise, new[] { diagnostic });
        }
    }
}
