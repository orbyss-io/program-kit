using System;
using System.Collections.Generic;
using System.IO;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Resolution;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class ExplainOperation
{
    private readonly IntakePipeline intake;
    private readonly ResolutionEngine resolution;

    public ExplainOperation(IntakePipeline intake, ResolutionEngine resolution)
    {
        this.intake = intake;
        this.resolution = resolution;
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        System.Text.Json.Nodes.JsonObject document;
        try
        {
            document = intake.Load(requestPath);
            OperationExecutionTracker.Advance(OperationPhase.Intake, EffectState.None);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or System.Text.Json.JsonException or YamlDotNet.Core.YamlException)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.InvalidInput,
                OperationPhase.Intake,
                Path.GetFileName(requestPath),
                exception.Message,
                "The request could not be admitted for semantic validation.");
            return OperationResultFactory.Failure(PublicCommand.Explain, OperationOutcome.Blocked, OperationPhase.Intake, EffectState.None, PrimaryDisposition.Revise, new[] { diagnostic });
        }

        IReadOnlyList<string> missing = intake.MissingFields(document);
        if (missing.Count > 0)
        {
            string requestDigest = CanonicalJson.Digest(document);
            OperationExecutionTracker.Advance(OperationPhase.Validation, EffectState.None);
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.MissingSelection,
                OperationPhase.Validation,
                "factory-request",
                $"Missing required input fields: {string.Join(", ", missing)}",
                "No exact integration resolution can be issued until the fields are supplied.");
            return OperationResultFactory.Failure(
                PublicCommand.Explain,
                OperationOutcome.NeedsInput,
                OperationPhase.Validation,
                EffectState.None,
                PrimaryDisposition.ProvideInput,
                new[] { diagnostic },
                requestDigest,
                continuation: ContinuationBuilder.ForMissing(requestDigest, missing));
        }

        try
        {
            FactoryInput input = intake.AdmitAndMap(workspaceRoot, document);
            OperationExecutionTracker.Advance(OperationPhase.Validation, EffectState.None);
            if (input.Request.Operation != FactoryOperation.Explain || input.Request.RequestedEffect != RequestedEffect.None)
            {
                Diagnostic conflict = DiagnosticFactory.Create(
                    DiagnosticIds.ConflictingInput,
                    OperationPhase.Validation,
                    "factory-request.operation",
                    "The request operation/effect does not agree with the explain command.",
                    "The public command refuses the conflicting request without live writes.");
                return OperationResultFactory.Failure(PublicCommand.Explain, OperationOutcome.Blocked, OperationPhase.Validation, EffectState.None, PrimaryDisposition.Revise, new[] { conflict }, CanonicalJson.Digest(document));
            }

            ResolvedFactoryInput resolved = resolution.Resolve(input);
            OperationExecutionTracker.Advance(OperationPhase.Explanation, EffectState.None);
            return OperationResultFactory.Success(
                PublicCommand.Explain,
                OperationPhase.Explanation,
                EffectState.None,
                resolved.Lock.RequestDigest,
                resolved.Lock.ConstructionIdentity,
                resolved.Explanation.CanonicalDocument);
        }
        catch (ProgramKitDiagnosticException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                exception.DiagnosticId,
                exception.Phase,
                "factory-request",
                exception.Message,
                "The exact request was refused without live writes.");
            OperationExecutionTracker.Advance(exception.Phase, EffectState.None);
            return OperationResultFactory.Failure(
                PublicCommand.Explain,
                OperationOutcome.Blocked,
                exception.Phase,
                EffectState.None,
                exception.Disposition,
                new[] { diagnostic },
                CanonicalJson.Digest(document));
        }
        catch (KeyNotFoundException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.MissingSelection,
                OperationPhase.Resolution,
                "selections.provider",
                exception.Message,
                "No exact provider or profile was selected; no integration result was issued.");
            string requestDigest = CanonicalJson.Digest(document);
            OperationExecutionTracker.Advance(OperationPhase.Resolution, EffectState.None);
            return OperationResultFactory.Failure(
                PublicCommand.Explain,
                OperationOutcome.NeedsInput,
                OperationPhase.Resolution,
                EffectState.None,
                PrimaryDisposition.ProvideInput,
                new[] { diagnostic },
                requestDigest,
                continuation: ContinuationBuilder.ForMissing(requestDigest, new[] { "selections.provider" }));
        }
        catch (Exception exception) when (exception is InvalidDataException or InvalidOperationException or FormatException)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.IncompleteMeaning,
                OperationPhase.Validation,
                "factory-request",
                exception.Message,
                "The request must be revised before exact resolution.");
            return OperationResultFactory.Failure(PublicCommand.Explain, OperationOutcome.Blocked, OperationPhase.Validation, EffectState.None, PrimaryDisposition.Revise, new[] { diagnostic }, CanonicalJson.Digest(document));
        }
    }
}
