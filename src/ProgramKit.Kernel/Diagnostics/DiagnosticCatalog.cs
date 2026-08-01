using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using Orbyss.ProgramKit.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public sealed record DiagnosticDefinition(
    string Id,
    DiagnosticCategory Category,
    DiagnosticSeverity Severity,
    string MessageKey,
    string Disposition);

public static class DiagnosticCatalog
{
    public static IReadOnlyDictionary<string, DiagnosticDefinition> Entries { get; } =
        new ReadOnlyDictionary<string, DiagnosticDefinition>(new Dictionary<string, DiagnosticDefinition>(StringComparer.Ordinal)
        {
            [DiagnosticIds.MissingInput] = new(DiagnosticIds.MissingInput, DiagnosticCategory.Request, DiagnosticSeverity.Error, "request.missing-input", "provide-input"),
            [DiagnosticIds.InvalidInput] = new(DiagnosticIds.InvalidInput, DiagnosticCategory.Request, DiagnosticSeverity.Error, "request.invalid-input", "revise"),
            [DiagnosticIds.ConflictingInput] = new(DiagnosticIds.ConflictingInput, DiagnosticCategory.Request, DiagnosticSeverity.Error, "request.conflicting-input", "revise"),
            [DiagnosticIds.ConflictingIdentity] = new(DiagnosticIds.ConflictingIdentity, DiagnosticCategory.Semantic, DiagnosticSeverity.Error, "semantic.conflicting-identity", "revise"),
            [DiagnosticIds.IncompleteMeaning] = new(DiagnosticIds.IncompleteMeaning, DiagnosticCategory.Semantic, DiagnosticSeverity.Error, "semantic.incomplete-meaning", "revise"),
            [DiagnosticIds.MissingSelection] = new(DiagnosticIds.MissingSelection, DiagnosticCategory.Resolution, DiagnosticSeverity.Error, "resolution.missing-selection", "provide-input"),
            [DiagnosticIds.AmbiguousSelection] = new(DiagnosticIds.AmbiguousSelection, DiagnosticCategory.Resolution, DiagnosticSeverity.Error, "resolution.ambiguous-selection", "provide-input"),
            [DiagnosticIds.Incompatible] = new(DiagnosticIds.Incompatible, DiagnosticCategory.Resolution, DiagnosticSeverity.Error, "resolution.incompatible", "revise"),
            [DiagnosticIds.MissingAuthority] = new(DiagnosticIds.MissingAuthority, DiagnosticCategory.Policy, DiagnosticSeverity.Error, "policy.missing-authority", "request-approval"),
            [DiagnosticIds.InvalidWaiver] = new(DiagnosticIds.InvalidWaiver, DiagnosticCategory.Policy, DiagnosticSeverity.Error, "policy.invalid-waiver", "stop"),
            [DiagnosticIds.GateFailed] = new(DiagnosticIds.GateFailed, DiagnosticCategory.Conformance, DiagnosticSeverity.Error, "conformance.gate-failed", "revise"),
            [DiagnosticIds.DeterminismMismatch] = new(DiagnosticIds.DeterminismMismatch, DiagnosticCategory.Conformance, DiagnosticSeverity.Error, "conformance.determinism-mismatch", "stop"),
            [DiagnosticIds.GeneratedDrift] = new(DiagnosticIds.GeneratedDrift, DiagnosticCategory.Workspace, DiagnosticSeverity.Error, "workspace.generated-drift", "repair"),
            [DiagnosticIds.Collision] = new(DiagnosticIds.Collision, DiagnosticCategory.Workspace, DiagnosticSeverity.Error, "workspace.collision", "repair"),
            [DiagnosticIds.InterruptedPublication] = new(DiagnosticIds.InterruptedPublication, DiagnosticCategory.Workspace, DiagnosticSeverity.Error, "workspace.interrupted-publication", "repair"),
            [DiagnosticIds.StaleSnapshot] = new(DiagnosticIds.StaleSnapshot, DiagnosticCategory.Workspace, DiagnosticSeverity.Error, "workspace.stale-snapshot", "retry"),
            [DiagnosticIds.ExternalFailure] = new(DiagnosticIds.ExternalFailure, DiagnosticCategory.External, DiagnosticSeverity.Error, "external.failure", "retry"),
            [DiagnosticIds.ExternalUnavailable] = new(DiagnosticIds.ExternalUnavailable, DiagnosticCategory.External, DiagnosticSeverity.Error, "external.unavailable", "stop"),
            [DiagnosticIds.InternalFailure] = new(DiagnosticIds.InternalFailure, DiagnosticCategory.Internal, DiagnosticSeverity.Fatal, "internal.pipeline-failure", "stop"),
            [DiagnosticIds.DuplicateRoute] = new(DiagnosticIds.DuplicateRoute, DiagnosticCategory.Conformance, DiagnosticSeverity.Error, "dotnet.duplicate-route", "revise"),
            [DiagnosticIds.MissingAssembler] = new(DiagnosticIds.MissingAssembler, DiagnosticCategory.Conformance, DiagnosticSeverity.Error, "dotnet.missing-assembler", "provide-input"),
            [DiagnosticIds.AmbiguousOrder] = new(DiagnosticIds.AmbiguousOrder, DiagnosticCategory.Conformance, DiagnosticSeverity.Error, "dotnet.ambiguous-order", "provide-input"),
            [DiagnosticIds.CShellsConformance] = new(DiagnosticIds.CShellsConformance, DiagnosticCategory.Conformance, DiagnosticSeverity.Error, "dotnet.cshells-conformance", "stop"),
            [DiagnosticIds.PackageMismatch] = new(DiagnosticIds.PackageMismatch, DiagnosticCategory.Resolution, DiagnosticSeverity.Error, "dotnet.package-mismatch", "stop"),
            [DiagnosticIds.DotNetToolFailure] = new(DiagnosticIds.DotNetToolFailure, DiagnosticCategory.External, DiagnosticSeverity.Error, "dotnet.tool-failure", "retry"),
            [DiagnosticIds.ForbiddenRuntimeDependency] = new(DiagnosticIds.ForbiddenRuntimeDependency, DiagnosticCategory.Conformance, DiagnosticSeverity.Error, "dotnet.forbidden-runtime-dependency", "stop"),
        });
}
