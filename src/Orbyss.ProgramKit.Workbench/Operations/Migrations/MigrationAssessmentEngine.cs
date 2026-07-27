using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

namespace Orbyss.ProgramKit.Workbench.Operations.Migrations;

/// <summary>Default fixed-point reverse-closure migration engine.</summary>
public sealed class MigrationAssessmentEngine : IMigrationAssessmentEngine
{
    private readonly IProgramKitSemanticValidator<VersionMapDocument> mapValidator;
    private readonly IProgramKitSemanticValidator<VersionSelectionDocument> selectionValidator;
    private readonly IProgramKitSemanticValidator<MigrationAssessment> assessmentValidator;

    /// <summary>Initializes the engine with contract-owned validators.</summary>
    public MigrationAssessmentEngine(
        IProgramKitSemanticValidator<VersionMapDocument> mapValidator,
        IProgramKitSemanticValidator<VersionSelectionDocument> selectionValidator,
        IProgramKitSemanticValidator<MigrationAssessment> assessmentValidator)
    {
        this.mapValidator = mapValidator ??
            throw new ArgumentNullException(nameof(mapValidator));
        this.selectionValidator = selectionValidator ??
            throw new ArgumentNullException(nameof(selectionValidator));
        this.assessmentValidator = assessmentValidator ??
            throw new ArgumentNullException(nameof(assessmentValidator));
    }

    /// <inheritdoc />
    public WorkbenchResult<MigrationAssessment> Assess(
        MigrationAssessmentRequest request)
    {
        ArgumentNullException.ThrowIfNull(request);
        var requestValidation = ValidateRequest(request);
        if (!requestValidation.IsValid)
        {
            return new WorkbenchResult<MigrationAssessment>(default, requestValidation);
        }

        var nodes = request.VersionMap.Nodes.ToDictionary(
            static node => ExactKey(node.Revision),
            StringComparer.Ordinal);
        var selections = request.VersionSelection.Selections.ToDictionary(
            static selection => selection.Identity.Value,
            StringComparer.Ordinal);
        var changedRoots = request.VersionSelection.Selections
            .Where(static selection => selection.Observed != selection.Target)
            .Select(static selection => selection.Observed)
            .OrderBy(ExactKey, StringComparer.Ordinal)
            .ToImmutableArray();
        var pathResult = FindCausalPaths(
            request.VersionMap,
            nodes,
            changedRoots,
            request.Limits);
        if (!pathResult.Validation.IsValid || pathResult.Value is null)
        {
            return new WorkbenchResult<MigrationAssessment>(
                default,
                pathResult.Validation);
        }

        var pathsByNode = pathResult.Value;
        var closureValidation = ValidateClosureInputs(
            request,
            pathsByNode.Keys,
            nodes,
            selections);
        if (!closureValidation.IsValid)
        {
            return new WorkbenchResult<MigrationAssessment>(
                default,
                closureValidation);
        }

        var decisions = request.Decisions.ToDictionary(
            static decision => decision.Identity.Value,
            StringComparer.Ordinal);
        var impacts = pathsByNode
            .OrderBy(static pair => pair.Key, StringComparer.Ordinal)
            .Select(pair => CreateImpact(
                nodes[pair.Key],
                selections,
                decisions,
                pair.Value))
            .ToImmutableArray();
        var waves = CreateWaves(
            request.VersionMap,
            pathsByNode.Keys.ToHashSet(StringComparer.Ordinal),
            selections);
        var assessment = new MigrationAssessment(
            request.VersionMapReference,
            request.VersionSelectionReference,
            changedRoots,
            impacts,
            waves);
        var validation = assessmentValidator.Validate(assessment);
        return validation.IsValid
            ? new WorkbenchResult<MigrationAssessment>(assessment, validation)
            : new WorkbenchResult<MigrationAssessment>(default, validation);
    }

    private ProgramKitValidationResult ValidateRequest(
        MigrationAssessmentRequest request)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (request.VersionMapReference is null ||
            request.VersionSelectionReference is null ||
            request.VersionMap is null ||
            request.VersionSelection is null ||
            request.Limits is null ||
            request.Limits.MaxImpactedNodes <= 0 ||
            request.Limits.MaxCausalPaths <= 0)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidMigrationRequest,
                "Migration assessment requires exact inputs and positive finite limits.",
                string.Empty));
            return ProgramKitValidationResult.From(diagnostics);
        }

        diagnostics.AddRange(mapValidator.Validate(request.VersionMap).Diagnostics);
        diagnostics.AddRange(selectionValidator.Validate(request.VersionSelection).Diagnostics);
        if (request.VersionSelection.InputVersionMap != request.VersionMapReference)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidMigrationRequest,
                "The exact selection must bind the supplied Version Map revision.",
                "/versionSelection/inputVersionMap"));
        }

        if (request.Decisions.IsDefault)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidMigrationRequest,
                "The terminal decision collection must be initialized.",
                "/decisions"));
        }

        var mapIdentities = new HashSet<string>(StringComparer.Ordinal);
        foreach (var node in request.VersionMap.Nodes)
        {
            if (node is not null && !mapIdentities.Add(node.Revision.Identity.Value))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidMigrationRequest,
                    "Migration assessment requires one selected map revision per semantic identity.",
                    "/versionMap/nodes"));
            }
        }

        if (!request.VersionSelection.Selections.Any(static selection =>
                selection is not null && selection.Observed != selection.Target))
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidMigrationRequest,
                "At least one observed revision must differ from its selected target.",
                "/versionSelection/selections"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static WorkbenchResult<Dictionary<string, ImmutableArray<MigrationCausalPath>>>
        FindCausalPaths(
            VersionMapDocument map,
            Dictionary<string, VersionRevisionNode> nodes,
            ImmutableArray<ArtifactReference> changedRoots,
            MigrationAnalysisLimits limits)
    {
        var reverse = map.Edges
            .GroupBy(static edge => ExactKey(edge.Resolution), StringComparer.Ordinal)
            .ToDictionary(
                static group => group.Key,
                static group => group
                    .OrderBy(static edge => edge.Id.Value, StringComparer.Ordinal)
                    .ToImmutableArray(),
                StringComparer.Ordinal);
        var collected = new Dictionary<
            string,
            Dictionary<string, MigrationCausalPath>>(StringComparer.Ordinal);
        var queue = new Queue<(
            string NodeKey,
            ArtifactReference Root,
            ImmutableArray<ProgramKitIdentifier> EdgeIds,
            ImmutableHashSet<string> Visited)>();
        var pathCount = 0;
        foreach (var root in changedRoots)
        {
            var rootKey = ExactKey(root);
            if (!nodes.ContainsKey(rootKey))
            {
                return LimitOrGraphFailure(
                    "Every changed observed revision must be an exact Version Map node.",
                    "/versionSelection/selections");
            }

            queue.Enqueue((rootKey, root, [], ImmutableHashSet.Create(
                StringComparer.Ordinal,
                rootKey)));
        }

        while (queue.Count > 0)
        {
            var state = queue.Dequeue();
            var path = new MigrationCausalPath(state.Root, state.EdgeIds);
            if (!collected.TryGetValue(state.NodeKey, out var nodePaths))
            {
                nodePaths = new Dictionary<string, MigrationCausalPath>(StringComparer.Ordinal);
                collected.Add(state.NodeKey, nodePaths);
            }

            var pathKey = PathKey(path);
            if (!nodePaths.TryAdd(pathKey, path))
            {
                continue;
            }

            pathCount++;
            if (collected.Count > limits.MaxImpactedNodes ||
                pathCount > limits.MaxCausalPaths)
            {
                return LimitOrGraphFailure(
                    "Migration reverse closure exceeded its explicit node or causal-path limit.",
                    "/limits");
            }

            if (!reverse.TryGetValue(state.NodeKey, out var dependents))
            {
                continue;
            }

            foreach (var edge in dependents)
            {
                var dependentKey = ExactKey(edge.Source);
                if (!state.Visited.Contains(dependentKey))
                {
                    queue.Enqueue((
                        dependentKey,
                        state.Root,
                        state.EdgeIds.Add(edge.Id),
                        state.Visited.Add(dependentKey)));
                }
            }
        }

        var immutable = collected.ToDictionary(
            static pair => pair.Key,
            static pair => pair.Value
                .OrderBy(static path => path.Key, StringComparer.Ordinal)
                .Select(static path => path.Value)
                .ToImmutableArray(),
            StringComparer.Ordinal);
        return new WorkbenchResult<Dictionary<string, ImmutableArray<MigrationCausalPath>>>(
            immutable,
            ProgramKitValidationResult.Valid);
    }

    private static WorkbenchResult<Dictionary<string, ImmutableArray<MigrationCausalPath>>>
        LimitOrGraphFailure(
            string message,
            string path) =>
        new(
            default,
            ProgramKitValidationResult.From(
            [
                WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.MigrationClosureLimitExceeded,
                    message,
                    path),
            ]));

    private static ProgramKitValidationResult ValidateClosureInputs(
        MigrationAssessmentRequest request,
        IEnumerable<string> reachedKeys,
        Dictionary<string, VersionRevisionNode> nodes,
        Dictionary<string, VersionSelection> selections)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        var reachedIdentities = reachedKeys
            .Select(key => nodes[key].Revision.Identity.Value)
            .ToHashSet(StringComparer.Ordinal);
        var decisionIdentities = new HashSet<string>(StringComparer.Ordinal);
        foreach (var identity in reachedIdentities.Order(StringComparer.Ordinal))
        {
            if (!selections.ContainsKey(identity))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidMigrationRequest,
                    "Every reached identity requires an exact observed-to-target selection.",
                    "/versionSelection/selections"));
            }
        }

        foreach (var decision in request.Decisions)
        {
            if (decision is null ||
                !reachedIdentities.Contains(decision.Identity.Value) ||
                !decisionIdentities.Add(decision.Identity.Value))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidMigrationRequest,
                    "Decisions must contain exactly one entry for each reached identity and no others.",
                    "/decisions"));
                continue;
            }

            ValidateCompatibility(decision, diagnostics);
        }

        if (!decisionIdentities.SetEquals(reachedIdentities))
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidMigrationRequest,
                "Every reached identity requires exactly one complete terminal decision.",
                "/decisions"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateCompatibility(
        MigrationBoundaryDecision decision,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var expected = Enum.GetValues<CompatibilityDimension>();
        if (decision.CompatibilityClaims.IsDefault ||
            decision.CompatibilityClaims.Length != expected.Length)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidMigrationRequest,
                "Every compatibility dimension must be classified exactly once.",
                "/decisions/compatibilityClaims"));
            return;
        }

        var dimensions = new HashSet<CompatibilityDimension>();
        foreach (var claim in decision.CompatibilityClaims)
        {
            if (claim is null ||
                !Enum.IsDefined(claim.Dimension) ||
                !Enum.IsDefined(claim.Classification) ||
                claim.Classification == CompatibilityClassification.Unknown ||
                !dimensions.Add(claim.Dimension) ||
                (claim.Classification == CompatibilityClassification.ConditionallyCompatible &&
                 claim.Conditions.IsDefaultOrEmpty))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidMigrationRequest,
                    "Compatibility must be defined, complete, unique, and cannot remain unknown.",
                    "/decisions/compatibilityClaims"));
            }
        }
    }

    private static MigrationImpact CreateImpact(
        VersionRevisionNode node,
        Dictionary<string, VersionSelection> selections,
        Dictionary<string, MigrationBoundaryDecision> decisions,
        ImmutableArray<MigrationCausalPath> paths)
    {
        var selection = selections[node.Revision.Identity.Value];
        var decision = decisions[node.Revision.Identity.Value];
        return new MigrationImpact(
            node.Revision,
            selection.Target,
            selection.OwnerId,
            decision.Disposition,
            decision.RequiredActions,
            decision.RequiredEvidence,
            paths,
            decision.Rationale);
    }

    private static ImmutableArray<MigrationWave> CreateWaves(
        VersionMapDocument map,
        HashSet<string> reached,
        Dictionary<string, VersionSelection> selections)
    {
        var adjacency = reached.ToDictionary(
            static key => key,
            static _ => new HashSet<string>(StringComparer.Ordinal),
            StringComparer.Ordinal);
        var reverse = reached.ToDictionary(
            static key => key,
            static _ => new HashSet<string>(StringComparer.Ordinal),
            StringComparer.Ordinal);
        foreach (var edge in map.Edges)
        {
            var source = ExactKey(edge.Source);
            var target = ExactKey(edge.Resolution);
            if (reached.Contains(source) && reached.Contains(target))
            {
                adjacency[source].Add(target);
                reverse[target].Add(source);
            }
        }

        var order = new List<string>();
        var visited = new HashSet<string>(StringComparer.Ordinal);
        foreach (var node in reached.Order(StringComparer.Ordinal))
        {
            DepthFirst(node, adjacency, visited, order);
        }

        visited.Clear();
        var cohorts = new List<ImmutableArray<string>>();
        for (var index = order.Count - 1; index >= 0; index--)
        {
            var members = ImmutableArray.CreateBuilder<string>();
            Collect(order[index], reverse, visited, members);
            if (members.Count > 0)
            {
                cohorts.Add(members.Order(StringComparer.Ordinal).ToImmutableArray());
            }
        }

        var cohortByNode = new Dictionary<string, int>(StringComparer.Ordinal);
        for (var index = 0; index < cohorts.Count; index++)
        {
            foreach (var member in cohorts[index])
            {
                cohortByNode.Add(member, index);
            }
        }

        var successors = Enumerable.Range(0, cohorts.Count)
            .ToDictionary(
                static index => index,
                static _ => new HashSet<int>());
        var indegree = new int[cohorts.Count];
        foreach (var edge in map.Edges)
        {
            var source = ExactKey(edge.Source);
            var target = ExactKey(edge.Resolution);
            if (!reached.Contains(source) || !reached.Contains(target))
            {
                continue;
            }

            var sourceCohort = cohortByNode[source];
            var targetCohort = cohortByNode[target];
            if (sourceCohort != targetCohort &&
                successors[targetCohort].Add(sourceCohort))
            {
                indegree[sourceCohort]++;
            }
        }

        var remaining = new HashSet<int>(Enumerable.Range(0, cohorts.Count));
        var waves = ImmutableArray.CreateBuilder<MigrationWave>();
        while (remaining.Count > 0)
        {
            var available = remaining
                .Where(index => indegree[index] == 0)
                .OrderBy(index => cohorts[index][0], StringComparer.Ordinal)
                .ToImmutableArray();
            var waveCohorts = available
                .Select(index => CreateCohort(cohorts[index], selections))
                .ToImmutableArray();
            waves.Add(new MigrationWave(waves.Count, waveCohorts));
            foreach (var completed in available)
            {
                remaining.Remove(completed);
                foreach (var successor in successors[completed])
                {
                    indegree[successor]--;
                }
            }
        }

        return waves.ToImmutable();
    }

    private static MigrationCohort CreateCohort(
        ImmutableArray<string> memberKeys,
        Dictionary<string, VersionSelection> selections)
    {
        var members = memberKeys
            .Select(key => selections[IdentityFromKey(key)].Target)
            .OrderBy(ExactKey, StringComparer.Ordinal)
            .ToImmutableArray();
        var source = string.Join("|", members.Select(ExactKey));
        var digest = SHA256.HashData(Encoding.UTF8.GetBytes(source));
        var token = Convert.ToHexString(digest.AsSpan(0, 12)).ToLowerInvariant();
        return new MigrationCohort(
            new ProgramKitIdentifier(string.Concat("pkid:cohort:program-kit:", token)),
            members);
    }

    private static void DepthFirst(
        string node,
        Dictionary<string, HashSet<string>> adjacency,
        HashSet<string> visited,
        List<string> order)
    {
        if (!visited.Add(node))
        {
            return;
        }

        foreach (var target in adjacency[node].Order(StringComparer.Ordinal))
        {
            DepthFirst(target, adjacency, visited, order);
        }

        order.Add(node);
    }

    private static void Collect(
        string node,
        Dictionary<string, HashSet<string>> reverse,
        HashSet<string> visited,
        ImmutableArray<string>.Builder members)
    {
        if (!visited.Add(node))
        {
            return;
        }

        members.Add(node);
        foreach (var source in reverse[node].Order(StringComparer.Ordinal))
        {
            Collect(source, reverse, visited, members);
        }
    }

    private static string PathKey(MigrationCausalPath path) =>
        string.Concat(
            ExactKey(path.ChangedRoot),
            "|",
            string.Join(">", path.EdgeIds.Select(static id => id.Value)));

    private static string IdentityFromKey(string exactKey) =>
        exactKey[..exactKey.IndexOf('@', StringComparison.Ordinal)];

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "@",
            reference.Digest.Value);
}
