using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public sealed record DiagnosticDefinition(
    string Id,
    DiagnosticCategory Category,
    DiagnosticSeverity Severity,
    string MessageKey,
    PrimaryDisposition Disposition,
    string Expected,
    string Observed);

public static class DiagnosticCatalog
{
    public static IReadOnlyDictionary<string, DiagnosticDefinition> Entries { get; } =
        new ReadOnlyDictionary<string, DiagnosticDefinition>(new Dictionary<string, DiagnosticDefinition>(StringComparer.Ordinal)
        {
            [DiagnosticIds.MissingInput] = Definition(DiagnosticIds.MissingInput, DiagnosticCategory.Request, "request.missing-input", PrimaryDisposition.ProvideInput, "required-input-present", "required-input-absent"),
            [DiagnosticIds.InvalidInput] = Definition(DiagnosticIds.InvalidInput, DiagnosticCategory.Request, "request.invalid-input", PrimaryDisposition.Revise, "input-conforms-to-declared-contract", "input-invalid"),
            [DiagnosticIds.ConflictingInput] = Definition(DiagnosticIds.ConflictingInput, DiagnosticCategory.Request, "request.conflicting-input", PrimaryDisposition.Revise, "one-consistent-request-binding", "conflicting-request-binding"),
            [DiagnosticIds.ConflictingIdentity] = Definition(DiagnosticIds.ConflictingIdentity, DiagnosticCategory.Semantic, "semantic.conflicting-identity", PrimaryDisposition.Revise, "identity-content-agrees", "identity-content-conflicts"),
            [DiagnosticIds.IncompleteMeaning] = Definition(DiagnosticIds.IncompleteMeaning, DiagnosticCategory.Semantic, "semantic.incomplete-meaning", PrimaryDisposition.Revise, "meaning-complete-and-supported", "meaning-incomplete-or-unsupported"),
            [DiagnosticIds.MissingSelection] = Definition(DiagnosticIds.MissingSelection, DiagnosticCategory.Resolution, "resolution.missing-selection", PrimaryDisposition.ProvideInput, "one-exact-selection", "selection-absent"),
            [DiagnosticIds.AmbiguousSelection] = Definition(DiagnosticIds.AmbiguousSelection, DiagnosticCategory.Resolution, "resolution.ambiguous-selection", PrimaryDisposition.ProvideInput, "one-exact-selection", "multiple-selections"),
            [DiagnosticIds.Incompatible] = Definition(DiagnosticIds.Incompatible, DiagnosticCategory.Resolution, "resolution.incompatible", PrimaryDisposition.Revise, "selected-contracts-compatible", "selected-contracts-incompatible"),
            [DiagnosticIds.MissingAuthority] = Definition(DiagnosticIds.MissingAuthority, DiagnosticCategory.Policy, "policy.missing-authority", PrimaryDisposition.RequestApproval, "current-exact-authority", "authority-absent-or-insufficient"),
            [DiagnosticIds.InvalidWaiver] = Definition(DiagnosticIds.InvalidWaiver, DiagnosticCategory.Policy, "policy.invalid-waiver", PrimaryDisposition.Stop, "finite-valid-waiver-on-waivable-rule", "waiver-invalid-or-prohibited"),
            [DiagnosticIds.GateFailed] = Definition(DiagnosticIds.GateFailed, DiagnosticCategory.Conformance, "conformance.gate-failed", PrimaryDisposition.Revise, "mandatory-gates-passed", "mandatory-gate-not-passed"),
            [DiagnosticIds.DeterminismMismatch] = Definition(DiagnosticIds.DeterminismMismatch, DiagnosticCategory.Conformance, "conformance.determinism-mismatch", PrimaryDisposition.Stop, "equal-identity-equal-canonical-bytes", "equal-identity-different-canonical-bytes"),
            [DiagnosticIds.GeneratedDrift] = Definition(DiagnosticIds.GeneratedDrift, DiagnosticCategory.Workspace, "workspace.generated-drift", PrimaryDisposition.Repair, "admitted-generated-bytes", "generated-bytes-drifted"),
            [DiagnosticIds.Collision] = Definition(DiagnosticIds.Collision, DiagnosticCategory.Workspace, "workspace.collision", PrimaryDisposition.Repair, "publication-preconditions-exact", "publication-collision"),
            [DiagnosticIds.InterruptedPublication] = Definition(DiagnosticIds.InterruptedPublication, DiagnosticCategory.Workspace, "workspace.interrupted-publication", PrimaryDisposition.Repair, "complete-admitted-publication", "publication-incomplete"),
            [DiagnosticIds.StaleSnapshot] = Definition(DiagnosticIds.StaleSnapshot, DiagnosticCategory.Workspace, "workspace.stale-snapshot", PrimaryDisposition.Retry, "snapshot-bindings-current", "snapshot-bindings-stale"),
            [DiagnosticIds.ExternalFailure] = Definition(DiagnosticIds.ExternalFailure, DiagnosticCategory.External, "external.failure", PrimaryDisposition.Retry, "external-operation-succeeds", "external-operation-failed"),
            [DiagnosticIds.ExternalUnavailable] = Definition(DiagnosticIds.ExternalUnavailable, DiagnosticCategory.External, "external.unavailable", PrimaryDisposition.Stop, "exact-external-bytes-available", "external-bytes-unavailable"),
            [DiagnosticIds.InternalFailure] = Definition(DiagnosticIds.InternalFailure, DiagnosticCategory.Internal, "internal.pipeline-failure", PrimaryDisposition.Stop, "normal-result-pipeline-completes", "normal-result-pipeline-failed", DiagnosticSeverity.Fatal),
            [DiagnosticIds.DuplicateRoute] = Definition(DiagnosticIds.DuplicateRoute, DiagnosticCategory.Conformance, "dotnet.duplicate-route", PrimaryDisposition.Revise, "route-identities-unique", "duplicate-route-identity"),
            [DiagnosticIds.MissingAssembler] = Definition(DiagnosticIds.MissingAssembler, DiagnosticCategory.Conformance, "dotnet.missing-assembler", PrimaryDisposition.ProvideInput, "one-owning-assembler-selected", "owning-assembler-absent"),
            [DiagnosticIds.AmbiguousOrder] = Definition(DiagnosticIds.AmbiguousOrder, DiagnosticCategory.Conformance, "dotnet.ambiguous-order", PrimaryDisposition.ProvideInput, "meaningful-order-complete", "meaningful-order-ambiguous"),
            [DiagnosticIds.CShellsConformance] = Definition(DiagnosticIds.CShellsConformance, DiagnosticCategory.Conformance, "dotnet.cshells-conformance", PrimaryDisposition.Stop, "generated-code-conforms-to-cshells", "generated-code-nonconforming"),
            [DiagnosticIds.PackageMismatch] = Definition(DiagnosticIds.PackageMismatch, DiagnosticCategory.Resolution, "dotnet.package-mismatch", PrimaryDisposition.Stop, "package-identity-and-hashes-agree", "package-identity-or-hash-mismatch"),
            [DiagnosticIds.DotNetToolFailure] = Definition(DiagnosticIds.DotNetToolFailure, DiagnosticCategory.External, "dotnet.tool-failure", PrimaryDisposition.Retry, "locked-dotnet-operation-succeeds", "locked-dotnet-operation-failed"),
            [DiagnosticIds.ForbiddenRuntimeDependency] = Definition(DiagnosticIds.ForbiddenRuntimeDependency, DiagnosticCategory.Conformance, "dotnet.forbidden-runtime-dependency", PrimaryDisposition.Stop, "runtime-dependencies-allowlisted", "forbidden-runtime-dependency-present"),
        });

    private static DiagnosticDefinition Definition(
        string id,
        DiagnosticCategory category,
        string messageKey,
        PrimaryDisposition disposition,
        string expected,
        string observed,
        DiagnosticSeverity severity = DiagnosticSeverity.Error) =>
        new(id, category, severity, messageKey, disposition, expected, observed);
}
