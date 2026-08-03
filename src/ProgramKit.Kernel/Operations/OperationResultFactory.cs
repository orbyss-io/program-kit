using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
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
        IReadOnlyList<EvidenceReference>? evidence = null,
        IReadOnlyList<OperationChange>? changes = null,
        JsonObject? session = null,
        IReadOnlyList<DisclosureEntry>? disclosure = null,
        JsonObject? payload = null)
    {
        if (phase == OperationPhase.Completion && effect == EffectState.Indeterminate)
        {
            throw new InvalidOperationException("A successful completion cannot have indeterminate effect.");
        }

        if (command == PublicCommand.Explain && explanation is null
            || command is PublicCommand.Help or PublicCommand.Version && utility is null
            || command is PublicCommand.SessionExplain or PublicCommand.SessionInstall or PublicCommand.SessionVerify or PublicCommand.SessionRemove && session is null
            || command is PublicCommand.Init or PublicCommand.CatalogList or PublicCommand.Restore or PublicCommand.Prepare or PublicCommand.AuthorityRecord && payload is null)
        {
            throw new InvalidOperationException("The successful command-specific inline result is required.");
        }

        OperationResult result = new(
            "program-kit.operation-result/v2",
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
            evidence ?? Array.Empty<EvidenceReference>(),
            DiagnosticFactory.View(Array.Empty<Diagnostic>()),
            null,
            explanation,
            utility,
            session,
            disclosure,
            payload);
        OperationExecutionTracker.Complete(result);
        return result;
    }

    public static OperationResult Failure(
        PublicCommand command,
        OperationOutcome outcome,
        OperationPhase phase,
        EffectState effect,
        PrimaryDisposition disposition,
        IEnumerable<Diagnostic> diagnostics,
        string? requestIdentity = null,
        string? constructionIdentity = null,
        Continuation? continuation = null,
        IReadOnlyList<ArtifactReference>? artifacts = null,
        IReadOnlyList<ArtifactReference>? receipts = null,
        IReadOnlyList<EvidenceReference>? evidence = null,
        IReadOnlyList<OperationChange>? changes = null,
        JsonObject? payload = null)
    {
        Diagnostic[] materializedDiagnostics = diagnostics.ToArray();
        if (materializedDiagnostics.Length == 0
            || DiagnosticFactory.PrimaryDispositionFor(materializedDiagnostics) != disposition)
        {
            throw new InvalidOperationException("A failure result requires diagnostics whose typed disposition determines the primary disposition.");
        }

        if (outcome == OperationOutcome.Succeeded || disposition == PrimaryDisposition.Complete)
        {
            throw new InvalidOperationException("A failure result cannot claim success or completion.");
        }

        if (outcome == OperationOutcome.NeedsInput && continuation is null)
        {
            throw new InvalidOperationException("A needs-input result requires a stateless continuation.");
        }

        OperationResult result = new(
            "program-kit.operation-result/v2",
            CanonicalJson.Profile,
            command,
            ProtocolIdentities.Operation(Kebab(command)),
            requestIdentity,
            constructionIdentity,
            outcome,
            phase,
            effect,
            disposition,
            changes ?? Array.Empty<OperationChange>(),
            artifacts ?? Array.Empty<ArtifactReference>(),
            receipts ?? Array.Empty<ArtifactReference>(),
            evidence ?? Array.Empty<EvidenceReference>(),
            DiagnosticFactory.View(materializedDiagnostics),
            continuation,
            Payload: payload);
        OperationExecutionTracker.Complete(result);
        return result;
    }

    public static OperationResult Fallback(PublicCommand command, OperationPhase phase, EffectState effect) => Failure(
        command,
        OperationOutcome.Faulted,
        phase,
        effect,
        PrimaryDisposition.Stop,
        new[]
        {
            DiagnosticFactory.Create(
                DiagnosticIds.InternalFailure,
                phase,
                DisclosureFilter.PublicText("public-command"),
                DisclosureFilter.PublicText("The normal result pipeline could not complete."),
                DisclosureFilter.PublicText("No further claim is made; use the safest bounded stop action.")),
        });

    public static OperationResult Fallback(PublicCommand command, EffectState effect) =>
        Fallback(command, OperationPhase.Request, effect);

    private static string Kebab(PublicCommand command) => command switch
    {
        PublicCommand.CatalogList => "catalog-list",
        PublicCommand.AuthorityRecord => "authority-record",
        PublicCommand.SessionExplain => "session-explain",
        PublicCommand.SessionInstall => "session-install",
        PublicCommand.SessionVerify => "session-verify",
        PublicCommand.SessionRemove => "session-remove",
        _ => command.ToString().ToLowerInvariant(),
    };
}
