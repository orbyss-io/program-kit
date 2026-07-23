using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Planning;

/// <summary>Validates plan trace completeness, dependency ordering, and parallel-group safety.</summary>
public sealed class ImplementationPlanDocumentValidator : IProgramKitSemanticValidator<ImplementationPlanDocument>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ImplementationPlanDocument value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        PlanningValidation.ValidateReference(value.Design, "$.design", diagnostics);
        PlanningValidation.RequireReferenceKind(
            value.Design,
            "design",
            "$.design",
            diagnostics);
        PlanningValidation.RequireIdentifier(value.OwnerId, "$.ownerId", diagnostics);
        if (!Enum.IsDefined(value.State))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln141,
                "Implementation-plan state must be a defined value.",
                "$.state"));
        }

        PlanningValidation.RequireUniqueText(
            value.RequirementIds,
            "$.requirementIds",
            PlanningDiagnosticIds.Pkpln101,
            "At least one design requirement is required.",
            diagnostics);

        var workUnits = ValidateWorkUnits(value.WorkUnits, diagnostics);
        ValidateDependencies(workUnits, diagnostics);
        ValidateParallelGroups(value.ParallelGroups, workUnits, diagnostics);
        ValidateTrace(value.Trace, value.RequirementIds, workUnits, diagnostics);
        ValidateUnresolvedDecisions(value.UnresolvedDecisions, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates an enveloped implementation plan and rejects exact payload
    /// references back to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<ImplementationPlanDocument> envelope)
    {
        var diagnostics = PlanningEnvelopeValidation.ValidateEnvelope(envelope, this);
        if (!PlanningEnvelopeValidation.TryCreateSelfReference(
                envelope,
                out var selfReference) ||
            envelope.Document is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Design,
            "/document/design",
            diagnostics);
        for (var workUnitIndex = 0;
             workUnitIndex < envelope.Document.WorkUnits.Length;
             workUnitIndex++)
        {
            var workUnit = envelope.Document.WorkUnits[workUnitIndex];
            if (workUnit is null)
            {
                continue;
            }

            var path = string.Concat("/document/workUnits/", workUnitIndex);
            PlanningEnvelopeValidation.RejectAll(
                selfReference,
                workUnit.Inputs,
                string.Concat(path, "/inputs"),
                diagnostics);
            PlanningEnvelopeValidation.RejectAll(
                selfReference,
                workUnit.Outputs,
                string.Concat(path, "/outputs"),
                diagnostics);
            PlanningEnvelopeValidation.RejectDependencies(
                selfReference,
                workUnit.SourceDependencies,
                string.Concat(path, "/sourceDependencies"),
                diagnostics);
            PlanningEnvelopeValidation.RejectDependencies(
                selfReference,
                workUnit.ExternalDependencies,
                string.Concat(path, "/externalDependencies"),
                diagnostics);
            PlanningEnvelopeValidation.RejectAll(
                selfReference,
                workUnit.Migrations,
                string.Concat(path, "/migrations"),
                diagnostics);
            PlanningEnvelopeValidation.RejectSelections(
                selfReference,
                workUnit.SelectedTests,
                string.Concat(path, "/selectedTests"),
                diagnostics);
        }

        for (var traceIndex = 0;
             traceIndex < envelope.Document.Trace.Length;
             traceIndex++)
        {
            var trace = envelope.Document.Trace[traceIndex];
            if (trace is null)
            {
                continue;
            }

            var path = string.Concat("/document/trace/", traceIndex);
            PlanningEnvelopeValidation.Reject(
                selfReference,
                trace.ContractOrArtifact,
                string.Concat(path, "/contractOrArtifact"),
                diagnostics);
            PlanningEnvelopeValidation.RejectAll(
                selfReference,
                trace.DependencyOrExtensionImpact,
                string.Concat(path, "/dependencyOrExtensionImpact"),
                diagnostics);
            PlanningEnvelopeValidation.RejectSelections(
                selfReference,
                trace.Tests,
                string.Concat(path, "/tests"),
                diagnostics);
            PlanningEnvelopeValidation.RejectAll(
                selfReference,
                trace.Evidence,
                string.Concat(path, "/evidence"),
                diagnostics);
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static Dictionary<string, PlanWorkUnit> ValidateWorkUnits(
        ImmutableArray<PlanWorkUnit> values,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var result = new Dictionary<string, PlanWorkUnit>(StringComparer.Ordinal);
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln103, "At least one work unit is required.", "$.workUnits"));
            return result;
        }

        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var path = $"$.workUnits[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln104, "A work unit cannot be null.", path));
                continue;
            }

            PlanningValidation.RequireText(value.WorkUnitId, $"{path}.workUnitId", diagnostics);
            PlanningValidation.RequireText(value.RequiredOutcome, $"{path}.requiredOutcome", diagnostics);
            if (value.Sequence < 0)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln105, "Sequence cannot be negative.", $"{path}.sequence"));
            }

            PlanningValidation.ValidateTextArray(value.DependsOn, $"{path}.dependsOn", diagnostics);
            PlanningValidation.ValidateReferences(value.Inputs, $"{path}.inputs", diagnostics);
            PlanningValidation.ValidateReferences(value.Outputs, $"{path}.outputs", diagnostics);
            PlanningValidation.RequireUniqueText(
                value.AllowedEdits,
                $"{path}.allowedEdits",
                PlanningDiagnosticIds.Pkpln106,
                "At least one allowed-edit boundary is required.",
                diagnostics);
            ValidateDependencies(value.SourceDependencies, $"{path}.sourceDependencies", diagnostics);
            ValidateDependencies(value.ExternalDependencies, $"{path}.externalDependencies", diagnostics);
            PlanningValidation.ValidateReferences(value.Migrations, $"{path}.migrations", diagnostics);
            PlanningValidation.RequireReferenceKinds(
                value.Migrations,
                "migration",
                $"{path}.migrations",
                PlanningDiagnosticIds.Pkpln014,
                diagnostics);
            ValidateCompatibility(value.Compatibility, $"{path}.compatibility", diagnostics);
            PlanningValidation.RequireUniqueText(
                value.StopConditions,
                $"{path}.stopConditions",
                PlanningDiagnosticIds.Pkpln107,
                "At least one stop condition is required.",
                diagnostics);
            ValidateVerification(value.Verification, $"{path}.verification", diagnostics);
            ValidateSelections(value.SelectedTests, $"{path}.selectedTests", diagnostics);

            if (!string.IsNullOrWhiteSpace(value.ParallelGroupId))
            {
                PlanningValidation.RequireText(value.ParallelGroupId, $"{path}.parallelGroupId", diagnostics);
            }

            if (!string.IsNullOrWhiteSpace(value.WorkUnitId) && !result.TryAdd(value.WorkUnitId, value))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln108,
                    $"Work unit ID '{value.WorkUnitId}' occurs more than once.",
                    $"{path}.workUnitId"));
            }
        }

        return result;
    }

    private static void ValidateDependencies(
        Dictionary<string, PlanWorkUnit> workUnits,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var (workUnitId, workUnit) in workUnits)
        {
            if (workUnit.DependsOn.IsDefault)
            {
                continue;
            }

            foreach (var dependencyId in workUnit.DependsOn)
            {
                if (!workUnits.TryGetValue(dependencyId, out var dependency))
                {
                    diagnostics.Add(PlanningValidation.Error(
                        PlanningDiagnosticIds.Pkpln109,
                        $"Dependency '{dependencyId}' does not name a plan work unit.",
                        $"$.workUnits['{workUnitId}'].dependsOn"));
                    continue;
                }

                if (string.Equals(workUnitId, dependencyId, StringComparison.Ordinal))
                {
                    diagnostics.Add(PlanningValidation.Error(
                        PlanningDiagnosticIds.Pkpln110,
                        "A work unit cannot depend on itself.",
                        $"$.workUnits['{workUnitId}'].dependsOn"));
                }
                else if (dependency.Sequence >= workUnit.Sequence)
                {
                    diagnostics.Add(PlanningValidation.Error(
                        PlanningDiagnosticIds.Pkpln111,
                        $"Dependency '{dependencyId}' must have a lower sequence than '{workUnitId}'.",
                        $"$.workUnits['{workUnitId}'].sequence"));
                }
            }
        }

        var visiting = new HashSet<string>(StringComparer.Ordinal);
        var visited = new HashSet<string>(StringComparer.Ordinal);
        foreach (var workUnitId in workUnits.Keys.Order(StringComparer.Ordinal))
        {
            DetectCycle(workUnitId, workUnits, visiting, visited, diagnostics);
        }
    }

    private static void DetectCycle(
        string workUnitId,
        Dictionary<string, PlanWorkUnit> workUnits,
        HashSet<string> visiting,
        HashSet<string> visited,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (visited.Contains(workUnitId) || !workUnits.TryGetValue(workUnitId, out var workUnit))
        {
            return;
        }

        if (!visiting.Add(workUnitId))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln112,
                $"Dependency cycle detected at work unit '{workUnitId}'.",
                "$.workUnits"));
            return;
        }

        if (!workUnit.DependsOn.IsDefault)
        {
            foreach (var dependencyId in workUnit.DependsOn.Order(StringComparer.Ordinal))
            {
                DetectCycle(dependencyId, workUnits, visiting, visited, diagnostics);
            }
        }

        visiting.Remove(workUnitId);
        visited.Add(workUnitId);
    }

    private static void ValidateParallelGroups(
        ImmutableArray<PlanParallelGroup> values,
        Dictionary<string, PlanWorkUnit> workUnits,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln113, "Parallel groups must be initialized.", "$.parallelGroups"));
            return;
        }

        var groups = new Dictionary<string, PlanParallelGroup>(StringComparer.Ordinal);
        var assignedWorkUnits = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var group = values[index];
            var path = $"$.parallelGroups[{index}]";
            if (group is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln114, "A parallel group cannot be null.", path));
                continue;
            }

            PlanningValidation.RequireText(group.ParallelGroupId, $"{path}.parallelGroupId", diagnostics);
            PlanningValidation.RequireUniqueText(
                group.WorkUnitIds,
                $"{path}.workUnitIds",
                PlanningDiagnosticIds.Pkpln115,
                "A parallel group requires at least one work unit.",
                diagnostics);
            if (!string.IsNullOrWhiteSpace(group.ParallelGroupId)
                && !groups.TryAdd(group.ParallelGroupId, group))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln116,
                    $"Parallel group '{group.ParallelGroupId}' occurs more than once.",
                    $"{path}.parallelGroupId"));
            }

            if (group.WorkUnitIds.IsDefault)
            {
                continue;
            }

            foreach (var workUnitId in group.WorkUnitIds)
            {
                if (!workUnits.TryGetValue(workUnitId, out var workUnit))
                {
                    diagnostics.Add(PlanningValidation.Error(
                        PlanningDiagnosticIds.Pkpln117,
                        $"Parallel-group member '{workUnitId}' does not name a work unit.",
                        $"{path}.workUnitIds"));
                    continue;
                }

                if (!assignedWorkUnits.Add(workUnitId))
                {
                    diagnostics.Add(PlanningValidation.Error(
                        PlanningDiagnosticIds.Pkpln118,
                        $"Work unit '{workUnitId}' belongs to more than one parallel group.",
                        $"{path}.workUnitIds"));
                }

                if (!string.Equals(workUnit.ParallelGroupId, group.ParallelGroupId, StringComparison.Ordinal))
                {
                    diagnostics.Add(PlanningValidation.Error(
                        PlanningDiagnosticIds.Pkpln119,
                        $"Work unit '{workUnitId}' does not bind back to parallel group '{group.ParallelGroupId}'.",
                        $"{path}.workUnitIds"));
                }

                foreach (var otherId in group.WorkUnitIds)
                {
                    if (!string.Equals(workUnitId, otherId, StringComparison.Ordinal)
                        && IsDependencyReachable(workUnitId, otherId, workUnits, []))
                    {
                        diagnostics.Add(PlanningValidation.Error(
                            PlanningDiagnosticIds.Pkpln120,
                            $"Parallel work units '{workUnitId}' and '{otherId}' have a dependency path.",
                            $"{path}.workUnitIds"));
                    }
                }
            }
        }

        foreach (var workUnit in workUnits.Values)
        {
            if (!string.IsNullOrWhiteSpace(workUnit.ParallelGroupId)
                && (!groups.TryGetValue(workUnit.ParallelGroupId, out var group)
                    || group.WorkUnitIds.IsDefault
                    || !group.WorkUnitIds.Contains(workUnit.WorkUnitId, StringComparer.Ordinal)))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln121,
                    $"Work unit '{workUnit.WorkUnitId}' names an undeclared or incomplete parallel group.",
                    $"$.workUnits['{workUnit.WorkUnitId}'].parallelGroupId"));
            }
        }
    }

    private static bool IsDependencyReachable(
        string sourceId,
        string targetId,
        Dictionary<string, PlanWorkUnit> workUnits,
        HashSet<string> visited)
    {
        if (!visited.Add(sourceId) || !workUnits.TryGetValue(sourceId, out var source) || source.DependsOn.IsDefault)
        {
            return false;
        }

        return source.DependsOn.Any(dependencyId =>
            string.Equals(dependencyId, targetId, StringComparison.Ordinal)
            || IsDependencyReachable(dependencyId, targetId, workUnits, visited));
    }

    private static void ValidateTrace(
        ImmutableArray<RequirementTrace> values,
        ImmutableArray<string> requirementIds,
        Dictionary<string, PlanWorkUnit> workUnits,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln122, "Requirement trace is required.", "$.trace"));
            return;
        }

        var traced = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var trace = values[index];
            var path = $"$.trace[{index}]";
            if (trace is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln123, "A trace entry cannot be null.", path));
                continue;
            }

            PlanningValidation.RequireText(trace.RequirementId, $"{path}.requirementId", diagnostics);
            PlanningValidation.RequireIdentifier(trace.OwnerId, $"{path}.ownerId", diagnostics);
            PlanningValidation.ValidateReference(trace.ContractOrArtifact, $"{path}.contractOrArtifact", diagnostics);
            PlanningValidation.RequireUniqueText(
                trace.WorkUnitIds,
                $"{path}.workUnitIds",
                PlanningDiagnosticIds.Pkpln124,
                "Trace must name at least one implementation work unit.",
                diagnostics);
            PlanningValidation.RequireText(trace.ImplementationOutcome, $"{path}.implementationOutcome", diagnostics);
            PlanningValidation.ValidateReferences(
                trace.DependencyOrExtensionImpact,
                $"{path}.dependencyOrExtensionImpact",
                diagnostics);
            ValidateSelections(trace.Tests, $"{path}.tests", diagnostics);
            PlanningValidation.ValidateReferences(trace.Evidence, $"{path}.evidence", diagnostics);
            PlanningValidation.RequireText(
                trace.ObservableAcceptanceOutcome,
                $"{path}.observableAcceptanceOutcome",
                diagnostics);

            if (!string.IsNullOrWhiteSpace(trace.RequirementId) && !traced.Add(trace.RequirementId))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln125,
                    $"Requirement '{trace.RequirementId}' has more than one trace entry.",
                    $"{path}.requirementId"));
            }

            if (!trace.WorkUnitIds.IsDefault)
            {
                foreach (var workUnitId in trace.WorkUnitIds)
                {
                    if (!workUnits.ContainsKey(workUnitId))
                    {
                        diagnostics.Add(PlanningValidation.Error(
                            PlanningDiagnosticIds.Pkpln126,
                            $"Trace work unit '{workUnitId}' does not exist.",
                            $"{path}.workUnitIds"));
                    }
                }
            }
        }

        if (!requirementIds.IsDefault)
        {
            foreach (var requirementId in requirementIds)
            {
                if (!traced.Contains(requirementId))
                {
                    diagnostics.Add(PlanningValidation.Error(
                        PlanningDiagnosticIds.Pkpln127,
                        $"Requirement '{requirementId}' has no complete trace.",
                        "$.trace"));
                }
            }
        }

        foreach (var requirementId in traced)
        {
            if (requirementIds.IsDefault
                || !requirementIds.Contains(requirementId, StringComparer.Ordinal))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln128,
                    $"Trace contains undeclared requirement '{requirementId}'.",
                    "$.trace"));
            }
        }
    }

    private static void ValidateUnresolvedDecisions(
        ImmutableArray<PlanUnresolvedDecision> values,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln129,
                "Unresolved decisions must be initialized.",
                "$.unresolvedDecisions"));
            return;
        }

        var ids = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var path = $"$.unresolvedDecisions[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln130, "An unresolved decision cannot be null.", path));
                continue;
            }

            PlanningValidation.RequireText(value.DecisionId, $"{path}.decisionId", diagnostics);
            PlanningValidation.RequireText(value.Question, $"{path}.question", diagnostics);
            if (!string.IsNullOrWhiteSpace(value.DecisionId) && !ids.Add(value.DecisionId))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln131,
                    $"Unresolved decision '{value.DecisionId}' occurs more than once.",
                    $"{path}.decisionId"));
            }
        }
    }

    private static void ValidateDependencies(
        ImmutableArray<PlanDependency> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln132, "Dependencies must be initialized.", path));
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var itemPath = $"{path}[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln133, "A dependency cannot be null.", itemPath));
                continue;
            }

            PlanningValidation.ValidateReference(value.Artifact, $"{itemPath}.artifact", diagnostics);
            PlanningValidation.RequireText(value.Purpose, $"{itemPath}.purpose", diagnostics);
        }
    }

    private static void ValidateCompatibility(
        ImmutableArray<PlanCompatibilityRequirement> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln134, "Compatibility must be initialized.", path));
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var itemPath = $"{path}[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln135, "A compatibility entry cannot be null.", itemPath));
                continue;
            }

            PlanningValidation.RequireIdentifier(value.SubjectId, $"{itemPath}.subjectId", diagnostics);
            if (string.IsNullOrWhiteSpace(value.AcceptedVersions.Value))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln136,
                    "An explicit accepted-version range is required.",
                    $"{itemPath}.acceptedVersions"));
            }

            PlanningValidation.RequireText(value.ExpectedDisposition, $"{itemPath}.expectedDisposition", diagnostics);
        }
    }

    private static void ValidateVerification(
        ImmutableArray<PlanVerificationCommand> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln137, "At least one verification command is required.", path));
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var itemPath = $"{path}[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln138, "A verification command cannot be null.", itemPath));
                continue;
            }

            PlanningValidation.RequireText(value.Executable, $"{itemPath}.executable", diagnostics);
            PlanningValidation.ValidateTextArray(value.Arguments, $"{itemPath}.arguments", diagnostics, allowDuplicates: true);
            PlanningValidation.RequireText(value.WorkingDirectory, $"{itemPath}.workingDirectory", diagnostics);
            PlanningValidation.RequireText(value.ExpectedObservation, $"{itemPath}.expectedObservation", diagnostics);
        }
    }

    private static void ValidateSelections(
        ImmutableArray<Quality.TestSpecificationSelection> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln139, "Test selections must be initialized.", path));
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var itemPath = $"{path}[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln140, "A test selection cannot be null.", itemPath));
                continue;
            }

            PlanningValidation.ValidateReference(value.Specification, $"{itemPath}.specification", diagnostics);
            PlanningValidation.RequireReferenceKind(
                value.Specification,
                "test",
                $"{itemPath}.specification",
                diagnostics,
                PlanningDiagnosticIds.Pkpln015);
            PlanningValidation.ValidateProfileReference(value.Profile, $"{itemPath}.profile", diagnostics);
        }
    }
}

/// <summary>Validates a human-supplied design/plan approval record without originating a decision.</summary>
public sealed class DesignPlanApprovalRecordValidator : IProgramKitSemanticValidator<DesignPlanApprovalRecord>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(DesignPlanApprovalRecord value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        PlanningValidation.ValidateReference(value.Design, "$.design", diagnostics);
        PlanningValidation.ValidateReference(value.Plan, "$.plan", diagnostics);
        PlanningValidation.RequireReferenceKind(value.Design, "design", "$.design", diagnostics);
        PlanningValidation.RequireReferenceKind(value.Plan, "plan", "$.plan", diagnostics);
        PlanningValidation.RequireText(value.AcceptedScope, "$.acceptedScope", diagnostics);
        ValidatePrincipal(value.ApprovingPrincipal, diagnostics);
        ValidateAuthority(value.Authority, diagnostics);
        ValidateDecisionEvidence(value.DecisionEvidence, diagnostics);
        PlanningValidation.RequireText(value.CorrelationId, "$.correlationId", diagnostics);
        if (!Enum.IsDefined(value.Decision))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln216,
                "Approval decision must be a defined value.",
                "$.decision"));
        }

        if (value.DecisionTime == default)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln201,
                "A decision time supplied by the human-session boundary is required.",
                "$.decisionTime"));
        }

        ValidateConditions(value.Conditions, diagnostics);
        ValidateSupersession(value, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates an enveloped approval and rejects exact payload references,
    /// including <c>supersededBy</c>, back to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<DesignPlanApprovalRecord> envelope)
    {
        var diagnostics = PlanningEnvelopeValidation.ValidateEnvelope(envelope, this);
        if (!PlanningEnvelopeValidation.TryCreateSelfReference(
                envelope,
                out var selfReference) ||
            envelope.Document is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Design,
            "/document/design",
            diagnostics);
        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Plan,
            "/document/plan",
            diagnostics);
        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Authority?.Source,
            "/document/authority/source",
            diagnostics);
        for (var index = 0; index < envelope.Document.Conditions.Length; index++)
        {
            PlanningEnvelopeValidation.Reject(
                selfReference,
                envelope.Document.Conditions[index]?.ResolutionEvidence,
                $"/document/conditions/{index}/resolutionEvidence",
                diagnostics);
        }

        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Supersession?.SupersededBy,
            "/document/supersession/supersededBy",
            diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidatePrincipal(
        PrincipalReference? value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln202,
                "An approving principal supplied by the human session is required.",
                "$.approvingPrincipal"));
            return;
        }

        PlanningValidation.RequireText(value.Kind, "$.approvingPrincipal.kind", diagnostics);
        PlanningValidation.RequireText(value.Provider, "$.approvingPrincipal.provider", diagnostics);
        PlanningValidation.RequireText(value.Identifier, "$.approvingPrincipal.identifier", diagnostics);
        PlanningValidation.RequireText(value.Role, "$.approvingPrincipal.role", diagnostics);
    }

    private static void ValidateAuthority(
        AuthorityReference? value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln203,
                "A separate authority reference supplied by the human session is required.",
                "$.authority"));
            return;
        }

        PlanningValidation.RequireText(value.Kind, "$.authority.kind", diagnostics);
        PlanningValidation.ValidateReference(value.Source, "$.authority.source", diagnostics);
        PlanningValidation.RequireText(value.JsonPointer, "$.authority.jsonPointer", diagnostics);
        if (!string.IsNullOrWhiteSpace(value.JsonPointer)
            && value.JsonPointer[0] != '/')
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln204,
                "An authority JSON Pointer must be absolute.",
                "$.authority.jsonPointer"));
        }

        PlanningValidation.RequireIdentifier(value.OwnerId, "$.authority.ownerId", diagnostics);
    }

    private static void ValidateDecisionEvidence(
        ImmutableArray<HumanDecisionEvidence> values,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln205,
                "At least one human-decision evidence reference is required.",
                "$.decisionEvidence"));
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var path = $"$.decisionEvidence[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln206, "Decision evidence cannot be null.", path));
                continue;
            }

            PlanningValidation.RequireText(value.Kind, $"{path}.kind", diagnostics);
            PlanningValidation.RequireText(value.Provider, $"{path}.provider", diagnostics);
            PlanningValidation.RequireText(value.ReferenceId, $"{path}.referenceId", diagnostics);
            if (value.Digest is { } digest && string.IsNullOrWhiteSpace(digest.Value))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln207,
                    "A supplied evidence digest must be an exact SHA-256 digest.",
                    $"{path}.digest"));
            }
        }
    }

    private static void ValidateConditions(
        ImmutableArray<ApprovalCondition> values,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln208,
                "Approval conditions must be initialized.",
                "$.conditions"));
            return;
        }

        var ids = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var path = $"$.conditions[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln209, "An approval condition cannot be null.", path));
                continue;
            }

            PlanningValidation.RequireText(value.ConditionId, $"{path}.conditionId", diagnostics);
            PlanningValidation.RequireText(value.Description, $"{path}.description", diagnostics);
            if (!Enum.IsDefined(value.State))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln217,
                    "Approval-condition state must be a defined value.",
                    $"{path}.state"));
            }

            if (!string.IsNullOrWhiteSpace(value.ConditionId) && !ids.Add(value.ConditionId))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln210,
                    $"Approval condition '{value.ConditionId}' occurs more than once.",
                    $"{path}.conditionId"));
            }

            if (value.State == ApprovalConditionState.Open && value.ResolutionEvidence is not null)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln211,
                    "An open condition cannot carry resolution evidence.",
                    $"{path}.resolutionEvidence"));
            }
            else if (value.State != ApprovalConditionState.Open && value.ResolutionEvidence is null)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln212,
                    "A satisfied or waived condition requires exact resolution evidence.",
                    $"{path}.resolutionEvidence"));
            }
            else if (value.ResolutionEvidence is not null)
            {
                PlanningValidation.ValidateReference(
                    value.ResolutionEvidence,
                    $"{path}.resolutionEvidence",
                    diagnostics);
            }
        }
    }

    private static void ValidateSupersession(
        DesignPlanApprovalRecord approval,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (approval.Supersession is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln213,
                "Explicit supersession state is required.",
                "$.supersession"));
            return;
        }

        if (!Enum.IsDefined(approval.Supersession.State))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln218,
                "Approval supersession state must be a defined value.",
                "$.supersession.state"));
            return;
        }

        if (approval.Supersession.State == ApprovalSupersessionState.Active
            && approval.Supersession.SupersededBy is not null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln214,
                "An active approval cannot name a superseding record.",
                "$.supersession.supersededBy"));
        }
        else if (approval.Supersession.State == ApprovalSupersessionState.Superseded)
        {
            if (approval.Supersession.SupersededBy is null)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln215,
                    "A superseded approval must name its exact successor.",
                    "$.supersession.supersededBy"));
            }
            else
            {
                PlanningValidation.ValidateReference(
                    approval.Supersession.SupersededBy,
                    "$.supersession.supersededBy",
                    diagnostics);
                PlanningValidation.RequireReferenceKind(
                    approval.Supersession.SupersededBy,
                    "approval",
                    "$.supersession.supersededBy",
                    diagnostics);
            }
        }
    }
}

/// <summary>
/// Validates the relationship among a plan payload, externally verified exact plan/design
/// references, and a supplied human approval. This validator does not verify canonical bytes and
/// does not itself grant implementation authority.
/// </summary>
public static class DesignPlanApprovalRelationshipValidator
{
    /// <summary>
    /// Validates approval eligibility after the caller has independently verified the supplied
    /// plan and design references against canonical artifact bytes.
    /// </summary>
    public static ProgramKitValidationResult Validate(
        ImplementationPlanDocument plan,
        ArtifactReference observedPlan,
        ArtifactReference observedDesign,
        DesignPlanApprovalRecord? suppliedApproval)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(observedPlan);
        ArgumentNullException.ThrowIfNull(observedDesign);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(new ImplementationPlanDocumentValidator().Validate(plan).Diagnostics);
        PlanningValidation.ValidateReference(observedPlan, "$.planReference", diagnostics);
        PlanningValidation.ValidateReference(observedDesign, "$.designReference", diagnostics);
        if (plan.Design != observedDesign)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln301,
                "The observed design does not match the plan's exact design ID, version, and digest.",
                "$.design"));
        }

        if (plan.State != ImplementationPlanState.ReadyForHumanDecision)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln302,
                "Only a plan ready for human decision can be implementable.",
                "$.state"));
        }

        if (!plan.UnresolvedDecisions.IsDefault
            && plan.UnresolvedDecisions.Any(decision => decision is { BlocksImplementation: true }))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln303,
                "A blocking unresolved decision prevents implementation.",
                "$.unresolvedDecisions"));
        }

        if (suppliedApproval is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln304,
                "An exact human-supplied approval record is required.",
                "$.approval"));
        }
        else
        {
            diagnostics.AddRange(new DesignPlanApprovalRecordValidator().Validate(suppliedApproval).Diagnostics);
            if (suppliedApproval.Design != observedDesign)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln305,
                    "Approval does not bind the exact observed design.",
                    "$.approval.design"));
            }

            if (suppliedApproval.Plan != observedPlan)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln306,
                    "Approval does not bind the exact implementation plan.",
                    "$.approval.plan"));
            }

            if (suppliedApproval.Decision != DesignPlanApprovalDecision.Approved)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln307,
                    "Only an explicitly supplied approved decision permits implementation.",
                    "$.approval.decision"));
            }

            if (!suppliedApproval.Conditions.IsDefault
                && suppliedApproval.Conditions.Any(condition => condition is { State: ApprovalConditionState.Open }))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln308,
                    "An open approval condition prevents implementation.",
                    "$.approval.conditions"));
            }

            if (suppliedApproval.Supersession is not { State: ApprovalSupersessionState.Active })
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln309,
                    "A missing or superseded approval prevents implementation.",
                    "$.approval.supersession"));
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}

internal static class PlanningEnvelopeValidation
{
    internal static ImmutableArray<ProgramKitDiagnostic>.Builder ValidateEnvelope<TDocument>(
        ArtifactEnvelope<TDocument> envelope,
        IProgramKitSemanticValidator<TDocument> validator)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(
            new ArtifactEnvelopeValidator<TDocument>(validator)
                .Validate(envelope)
                .Diagnostics);
        return diagnostics;
    }

    internal static bool TryCreateSelfReference<TDocument>(
        ArtifactEnvelope<TDocument>? envelope,
        out ArtifactReference selfReference)
    {
        if (envelope?.Artifact is null || envelope.Integrity is null)
        {
            selfReference = null!;
            return false;
        }

        selfReference = new ArtifactReference(
            envelope.Artifact.Id,
            envelope.Artifact.Version,
            envelope.Integrity.Digest);
        return true;
    }

    internal static void Reject(
        ArtifactReference selfReference,
        ArtifactReference? candidate,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (candidate == selfReference)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln219,
                "A planning artifact must not embed its own exact identity, version, and digest reference.",
                path));
        }
    }

    internal static void Reject(
        ArtifactReference selfReference,
        ProfileReference? candidate,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (candidate is not null &&
            candidate.Identity == selfReference.Identity &&
            candidate.Version == selfReference.Version &&
            candidate.Digest == selfReference.Digest)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln219,
                "A planning artifact must not embed its own exact identity, version, and digest reference.",
                path));
        }
    }

    internal static void RejectAll(
        ArtifactReference selfReference,
        ImmutableArray<ArtifactReference> candidates,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (candidates.IsDefault)
        {
            return;
        }

        for (var index = 0; index < candidates.Length; index++)
        {
            Reject(
                selfReference,
                candidates[index],
                string.Concat(path, "/", index),
                diagnostics);
        }
    }

    internal static void RejectDependencies(
        ArtifactReference selfReference,
        ImmutableArray<PlanDependency> dependencies,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (dependencies.IsDefault)
        {
            return;
        }

        for (var index = 0; index < dependencies.Length; index++)
        {
            Reject(
                selfReference,
                dependencies[index]?.Artifact,
                string.Concat(path, "/", index, "/artifact"),
                diagnostics);
        }
    }

    internal static void RejectSelections(
        ArtifactReference selfReference,
        ImmutableArray<Quality.TestSpecificationSelection> selections,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (selections.IsDefault)
        {
            return;
        }

        for (var index = 0; index < selections.Length; index++)
        {
            var selection = selections[index];
            Reject(
                selfReference,
                selection?.Specification,
                string.Concat(path, "/", index, "/specification"),
                diagnostics);
            Reject(
                selfReference,
                selection?.Profile,
                string.Concat(path, "/", index, "/profile"),
                diagnostics);
        }
    }
}

internal static class PlanningValidation
{
    internal static ProgramKitDiagnostic Error(string id, string message, string path) =>
        new(id, ProgramKitDiagnosticSeverity.Error, message, path);

    internal static void RequireText(
        string? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln001, "A non-empty value is required.", path));
        }
    }

    internal static void RequireIdentifier(
        ProgramKitIdentifier value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln002, "A Program Kit identifier is required.", path));
        }
    }

    internal static void ValidateReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln003, "An exact artifact reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln004, "An exact semantic version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln005, "An exact SHA-256 digest is required.", $"{path}.digest"));
        }
    }

    internal static void ValidateProfileReference(
        ProfileReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln006, "An exact profile reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln007, "An exact profile version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln008, "An exact profile digest is required.", $"{path}.digest"));
        }

        if (!string.Equals(value.Identity.Kind, "profile", StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                PlanningDiagnosticIds.Pkpln016,
                "The exact reference must have PKID kind 'profile'.",
                $"{path}.identity"));
        }
    }

    internal static void ValidateReferences(
        ImmutableArray<ArtifactReference> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln009, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<ArtifactReference>();
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            ValidateReference(value, $"{path}[{index}]", diagnostics);
            if (value is not null && !seen.Add(value))
            {
                diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln010, "Exact artifact references must be unique.", $"{path}[{index}]"));
            }
        }
    }

    internal static void RequireReferenceKind(
        ArtifactReference? value,
        string expectedKind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string diagnosticId = PlanningDiagnosticIds.Pkpln013)
    {
        if (value is not null
            && !string.Equals(value.Identity.Kind, expectedKind, StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                diagnosticId,
                $"The exact reference must have PKID kind '{expectedKind}'.",
                $"{path}.identity"));
        }
    }

    internal static void RequireReferenceKinds(
        ImmutableArray<ArtifactReference> values,
        string expectedKind,
        string path,
        string diagnosticId,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            RequireReferenceKind(
                values[index],
                expectedKind,
                $"{path}[{index}]",
                diagnostics,
                diagnosticId);
        }
    }

    internal static void RequireUniqueText(
        ImmutableArray<string> values,
        string path,
        string emptyDiagnosticId,
        string emptyMessage,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(Error(emptyDiagnosticId, emptyMessage, path));
            return;
        }

        ValidateTextArray(values, path, diagnostics);
    }

    internal static void ValidateTextArray(
        ImmutableArray<string> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        bool allowDuplicates = false)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln011, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            RequireText(value, $"{path}[{index}]", diagnostics);
            if (!allowDuplicates && !string.IsNullOrWhiteSpace(value) && !seen.Add(value))
            {
                diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln012, $"Value '{value}' occurs more than once.", $"{path}[{index}]"));
            }
        }
    }
}
