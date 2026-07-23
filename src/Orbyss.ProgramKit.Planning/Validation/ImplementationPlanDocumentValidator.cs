using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Diagnostics;
using Orbyss.ProgramKit.Planning.Plans;
using Orbyss.ProgramKit.Quality.Execution;

namespace Orbyss.ProgramKit.Planning.Validation;

/// <summary>Validates plan trace completeness, dependency ordering, and parallel-group safety.</summary>
public sealed class ImplementationPlanDocumentValidator :
    IArtifactEnvelopeSemanticValidator<ImplementationPlanDocument>
{
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates a plan validator with explicit envelope validation.</summary>
    public ImplementationPlanDocumentValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(envelopeValidator);
        _envelopeValidator = envelopeValidator;
    }

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
        var diagnostics = PlanningEnvelopeValidation.ValidateEnvelope(
            envelope,
            this,
            _envelopeValidator);
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
        ImmutableArray<TestSpecificationSelection> values,
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
