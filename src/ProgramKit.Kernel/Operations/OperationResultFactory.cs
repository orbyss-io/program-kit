using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;

namespace Orbyss.ProgramKit.Kernel.Operations;

public static class OperationResultFactory
{
    public static OperationResult Success(
        PublicCommand command,
        OperationPhase phase,
        EffectState effect,
        string? requestIdentity = null,
        string? constructionIdentity = null,
        JsonObject? explanation = null,
        JsonObject? utility = null,
        IReadOnlyList<ArtifactReference>? artifacts = null,
        IReadOnlyList<ArtifactReference>? receipts = null,
        IReadOnlyList<OperationChange>? changes = null) => new(
            "program-kit.operation-result/v1",
            CanonicalJson.Profile,
            command,
            ProtocolIdentities.Operation(Kebab(command)),
            requestIdentity,
            constructionIdentity,
            OperationOutcome.Succeeded,
            phase,
            effect,
            PrimaryDisposition.Complete,
            changes ?? Array.Empty<OperationChange>(),
            artifacts ?? Array.Empty<ArtifactReference>(),
            receipts ?? Array.Empty<ArtifactReference>(),
            Array.Empty<EvidenceReference>(),
            DiagnosticFactory.View(Array.Empty<Diagnostic>()),
            null,
            explanation,
            utility);

    public static OperationResult Failure(
        PublicCommand command,
        OperationOutcome outcome,
        OperationPhase phase,
        EffectState effect,
        PrimaryDisposition disposition,
        IEnumerable<Diagnostic> diagnostics,
        string? requestIdentity = null,
        string? constructionIdentity = null,
        Continuation? continuation = null) => new(
            "program-kit.operation-result/v1",
            CanonicalJson.Profile,
            command,
            ProtocolIdentities.Operation(Kebab(command)),
            requestIdentity,
            constructionIdentity,
            outcome,
            phase,
            effect,
            disposition,
            Array.Empty<OperationChange>(),
            Array.Empty<ArtifactReference>(),
            Array.Empty<ArtifactReference>(),
            Array.Empty<EvidenceReference>(),
            DiagnosticFactory.View(diagnostics),
            continuation);

    public static OperationResult Fallback(PublicCommand command, EffectState effect) => Failure(
        command,
        OperationOutcome.Faulted,
        OperationPhase.Request,
        effect,
        PrimaryDisposition.Stop,
        new[]
        {
            DiagnosticFactory.Create(
                DiagnosticIds.InternalFailure,
                OperationPhase.Request,
                "public-command",
                "The normal result pipeline could not complete.",
                "No further claim is made; use the safest bounded stop action."),
        });

    private static string Kebab(PublicCommand command) => command.ToString().ToLowerInvariant();
}
