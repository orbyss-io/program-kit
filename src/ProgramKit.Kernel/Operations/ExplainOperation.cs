using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
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

    public OperationResult Execute(string requestPath)
    {
        System.Text.Json.Nodes.JsonObject document;
        try
        {
            document = intake.Load(requestPath);
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
            MissingInput[] needs = missing
                .OrderBy(static value => value, StringComparer.Ordinal)
                .Select(static value => new MissingInput(value.Replace('.', '-'), "string-or-object", "human", ProtocolIdentities.Rule("request.required-input")))
                .ToArray();
            string continuationDigest = Digests.Sha256(Encoding.UTF8.GetBytes($"{requestDigest}\n{string.Join('\n', missing)}"));
            Continuation continuation = new(
                "program-kit.continuation/v1",
                CanonicalJson.Profile,
                requestDigest,
                needs,
                new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal),
                Array.Empty<string>(),
                Digests.Sha256(Array.Empty<byte>()),
                Digests.Sha256(Array.Empty<byte>()),
                continuationDigest);
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
                continuation: continuation);
        }

        try
        {
            FactoryInput input = intake.Bind(document);
            if (input.Operation != FactoryOperation.Explain || input.RequestedEffect != RequestedEffect.None)
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
            return OperationResultFactory.Success(
                PublicCommand.Explain,
                OperationPhase.Explanation,
                EffectState.None,
                resolved.Lock.RequestDigest,
                resolved.Lock.ConstructionIdentity,
                resolved.Explanation.CanonicalDocument);
        }
        catch (KeyNotFoundException exception)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.MissingSelection,
                OperationPhase.Resolution,
                "selections.provider",
                exception.Message,
                "No exact provider or profile was selected; no integration result was issued.");
            return OperationResultFactory.Failure(PublicCommand.Explain, OperationOutcome.NeedsInput, OperationPhase.Resolution, EffectState.None, PrimaryDisposition.ProvideInput, new[] { diagnostic }, CanonicalJson.Digest(document));
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
