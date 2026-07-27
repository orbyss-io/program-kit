using Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Default manifest-driven deterministic Version Map builder.</summary>
public sealed class VersionMapBuilder : IVersionMapBuilder
{
    private readonly IProgramKitSemanticValidator<VersionedComponentManifest> manifestValidator;
    private readonly IProgramKitSemanticValidator<VersionMapDocument> mapValidator;

    /// <summary>Initializes the builder with contract-owned semantic validators.</summary>
    public VersionMapBuilder(
        IProgramKitSemanticValidator<VersionedComponentManifest> manifestValidator,
        IProgramKitSemanticValidator<VersionMapDocument> mapValidator)
    {
        this.manifestValidator = manifestValidator ??
            throw new ArgumentNullException(nameof(manifestValidator));
        this.mapValidator = mapValidator ??
            throw new ArgumentNullException(nameof(mapValidator));
    }

    /// <inheritdoc />
    public WorkbenchResult<VersionMapDocument> Build(VersionMapBuildRequest request)
    {
        ArgumentNullException.ThrowIfNull(request);
        var diagnostics = ValidateRequest(request);
        if (!diagnostics.IsValid)
        {
            return new WorkbenchResult<VersionMapDocument>(default, diagnostics);
        }

        var byIdentity = request.Manifests.ToDictionary(
            static input => input.Manifest.Identity.Value,
            StringComparer.Ordinal);
        var nodes = request.Manifests
            .OrderBy(static input => ExactKey(input.Manifest.Revision), StringComparer.Ordinal)
            .Select(static input => new VersionRevisionNode(
                input.Manifest.Revision,
                input.Manifest.Kind,
                input.Manifest.OwnerId,
                [input.ManifestReference]))
            .ToImmutableArray();
        var edges = request.Dependencies
            .OrderBy(static declaration => declaration.Id.Value, StringComparer.Ordinal)
            .Select(declaration => CreateEdge(declaration, byIdentity))
            .ToImmutableArray();
        var map = new VersionMapDocument(nodes, edges);
        var validation = mapValidator.Validate(map);
        return validation.IsValid
            ? new WorkbenchResult<VersionMapDocument>(map, validation)
            : new WorkbenchResult<VersionMapDocument>(default, validation);
    }

    private ProgramKitValidationResult ValidateRequest(VersionMapBuildRequest request)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (request.Manifests.IsDefaultOrEmpty)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidVersionMapBuild,
                "At least one selected component manifest is required.",
                "/manifests"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (request.Dependencies.IsDefault)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidVersionMapBuild,
                "The typed dependency collection must be initialized.",
                "/dependencies"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        var identities = new HashSet<string>(StringComparer.Ordinal);
        var revisions = new HashSet<string>(StringComparer.Ordinal);
        var requirementKeys = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < request.Manifests.Length; index++)
        {
            var input = request.Manifests[index];
            var path = string.Concat("/manifests/", index);
            if (input is null || input.ManifestReference is null || input.Manifest is null)
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidVersionMapBuild,
                    "Each Version Map input requires an exact reference and manifest.",
                    path));
                continue;
            }

            diagnostics.AddRange(manifestValidator.Validate(input.Manifest).Diagnostics);
            if (!identities.Add(input.Manifest.Identity.Value) ||
                !revisions.Add(ExactKey(input.Manifest.Revision)))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidVersionMapBuild,
                    "Selected manifest identities and exact revisions must be unique.",
                    string.Concat(path, "/manifest/identity")));
            }

            foreach (var claim in input.Manifest.CompatibilityClaims)
            {
                if (claim is not null &&
                    claim.Classification == CompatibilityClassification.Unknown)
                {
                    diagnostics.Add(WorkbenchDiagnostics.Error(
                        WorkbenchDiagnosticIds.InvalidVersionMapBuild,
                        "Unknown compatibility fails closed before Version Map construction.",
                        string.Concat(path, "/manifest/compatibilityClaims")));
                }
            }

            foreach (var requirement in input.Manifest.RequiredContracts)
            {
                if (requirement is not null)
                {
                    requirementKeys.Add(RequirementKey(
                        input.Manifest.Identity,
                        requirement.Identity));
                }
            }
        }

        var declaredRequirements = new HashSet<string>(StringComparer.Ordinal);
        var edgeIds = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < request.Dependencies.Length; index++)
        {
            var declaration = request.Dependencies[index];
            var path = string.Concat("/dependencies/", index);
            if (declaration is null ||
                !Enum.IsDefined(declaration.Kind) ||
                !identities.Contains(declaration.SourceIdentity.Value) ||
                !identities.Contains(declaration.TargetIdentity.Value) ||
                !edgeIds.Add(declaration.Id.Value))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidVersionMapBuild,
                    "Every dependency must use a unique edge ID, defined kind, and selected source and target.",
                    path));
                continue;
            }

            var requirementKey = RequirementKey(
                declaration.SourceIdentity,
                declaration.TargetIdentity);
            if (!requirementKeys.Contains(requirementKey) ||
                !declaredRequirements.Add(requirementKey))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidVersionMapBuild,
                    "Each typed dependency must match exactly one undeclared manifest requirement.",
                    path));
            }
        }

        if (!declaredRequirements.SetEquals(requirementKeys))
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidVersionMapBuild,
                "Every manifest requirement must receive exactly one typed dependency declaration.",
                "/dependencies"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static VersionDependencyEdge CreateEdge(
        VersionDependencyDeclaration declaration,
        Dictionary<string, VersionedManifestInput> byIdentity)
    {
        var source = byIdentity[declaration.SourceIdentity.Value].Manifest;
        var requirement = source.RequiredContracts.Single(candidate =>
            candidate.Identity == declaration.TargetIdentity);
        return new VersionDependencyEdge(
            declaration.Id,
            source.Revision,
            requirement.Identity,
            declaration.Kind,
            requirement.AcceptedRange,
            requirement.Resolution,
            requirement.Exposure,
            requirement.Dimensions,
            requirement.EvidenceReferences);
    }

    private static string RequirementKey(
        ProgramKitIdentifier source,
        ProgramKitIdentifier target) =>
        string.Concat(source.Value, "->", target.Value);

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "@",
            reference.Digest.Value);
}
