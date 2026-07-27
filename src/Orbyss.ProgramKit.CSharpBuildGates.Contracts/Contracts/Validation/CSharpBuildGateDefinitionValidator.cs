using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;

/// <summary>
/// Pure deterministic validation for definition 1.0.0. The validator performs
/// no file, environment, package, assembly, or registration discovery.
/// </summary>
public sealed class CSharpBuildGateDefinitionValidator :
    IProgramKitSemanticValidator<CSharpBuildGateDefinitionDocument>
{
    private static readonly SemanticVersion ContractVersion = new("1.0.0");

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        CSharpBuildGateDefinitionDocument value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg001,
                "$",
                "A C# build-gate definition is required.");
            return ProgramKitValidationResult.From(diagnostics);
        }

        diagnostics.Require(
            value.Version == ContractVersion,
            CSharpBuildGateDiagnosticIds.Pkcg001,
            "$.version",
            "C# build-gate definition version must be 1.0.0.");
        diagnostics.Require(
            !string.IsNullOrWhiteSpace(value.OwnerId.Value) &&
            !string.IsNullOrWhiteSpace(value.ConsumerPolicyId.Value) &&
            value.Disposition is not null &&
            value.CompatibilityPolicy is not null,
            CSharpBuildGateDiagnosticIds.Pkcg001,
            "$",
            "Owner, policy, disposition, and compatibility references are required.");

        ValidateOwnersAndComponents(value, diagnostics);
        ValidateRules(value, diagnostics);
        ValidateProfiles(value, diagnostics);
        ValidateActivation(value, diagnostics);
        ValidateExceptions(value, diagnostics);
        ValidateSuppressions(value, diagnostics);
        ValidateAssurance(value, diagnostics);
        return diagnostics.Count == 0
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateOwnersAndComponents(
        CSharpBuildGateDefinitionDocument value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        CSharpBuildGateValidation.ValidateStableUnique(
            value.SemanticOwners,
            static owner => owner.Identity.Value,
            "$.semanticOwners",
            diagnostics);
        CSharpBuildGateValidation.ValidateStableUnique(
            value.AnalyzerComponents,
            static component => component.Identity.Value,
            "$.analyzerComponents",
            diagnostics);
        if (value.SemanticOwners.IsDefaultOrEmpty ||
            value.AnalyzerComponents.IsDefaultOrEmpty)
        {
            return;
        }

        var owners = value.SemanticOwners.ToDictionary(
            static owner => owner.Identity,
            static owner => owner);
        foreach (var owner in value.SemanticOwners)
        {
            var expectedPrefix = owner.Kind switch
            {
                CSharpAnalyzerComponentKind.CompilerBaseline => "CS",
                CSharpAnalyzerComponentKind.ProgramKitPublicContract => "PKCC",
                CSharpAnalyzerComponentKind.ConsumerOwned => null,
                _ => string.Empty,
            };
            if (expectedPrefix is not null)
            {
                diagnostics.Require(
                    string.Equals(
                        owner.DiagnosticPrefix,
                        expectedPrefix,
                        StringComparison.Ordinal),
                    CSharpBuildGateDiagnosticIds.Pkcg003,
                    "$.semanticOwners",
                    "The semantic owner's diagnostic prefix does not match its finite ownership kind.");
            }
            else
            {
                diagnostics.Require(
                    owner.Identity == value.OwnerId &&
                    IsConsumerPrefix(owner.DiagnosticPrefix),
                    CSharpBuildGateDiagnosticIds.Pkcg003,
                    "$.semanticOwners",
                    "Consumer-owned semantics must remain with the gate owner and use a non-Program-Kit prefix.");
            }
        }

        foreach (var component in value.AnalyzerComponents)
        {
            diagnostics.Require(
                owners.TryGetValue(component.SemanticOwnerId, out var owner) &&
                owner.Kind == component.Kind,
                CSharpBuildGateDiagnosticIds.Pkcg003,
                "$.analyzerComponents",
                "Every analyzer component must bind a semantic owner of the same finite kind.");
            CSharpBuildGateValidation.ValidateStableUnique(
                component.RuleIds,
                static rule => rule.Value,
                "$.analyzerComponents[].ruleIds",
                diagnostics,
                requireOne:
                    component.Kind != CSharpAnalyzerComponentKind.CompilerBaseline);
            CSharpBuildGateValidation.ValidateStableUnique(
                component.ReceiptGeneratorRevisions,
                static receipt => string.Concat(
                    receipt.Identity.Value,
                    "@",
                    receipt.Version.Value,
                    "#",
                    receipt.Digest.Value),
                "$.analyzerComponents[].receiptGeneratorRevisions",
                diagnostics);
            ValidateArtifact(component, diagnostics);
        }
    }

    private static void ValidateArtifact(
        CSharpAnalyzerComponent component,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var artifact = component.Artifact;
        if (artifact is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg005,
                "$.analyzerComponents[].artifact",
                "An exact analyzer artifact selection is required.");
            return;
        }

        diagnostics.Require(
            !artifact.HasRuntimeAssets &&
            !artifact.HasBuildTransitiveAssets,
            CSharpBuildGateDiagnosticIds.Pkcg005,
            "$.analyzerComponents[].artifact",
            "Analyzer selections cannot contain runtime or buildTransitive assets.");
        switch (artifact.Kind)
        {
            case CSharpAnalyzerArtifactKind.LocalNonPackableProject:
                diagnostics.Require(
                    CSharpBuildGateValidation.IsExactRepositoryPath(
                        artifact.RepositoryRelativeProjectPath) &&
                    artifact.Package is null &&
                    !artifact.IsPackable,
                    CSharpBuildGateDiagnosticIds.Pkcg005,
                    "$.analyzerComponents[].artifact",
                    "A local analyzer requires one exact non-packable project path and no package.");
                break;
            case CSharpAnalyzerArtifactKind.AnalyzerPackage:
                diagnostics.Require(
                    artifact.RepositoryRelativeProjectPath is null &&
                    artifact.Package is not null &&
                    artifact.IsPackable,
                    CSharpBuildGateDiagnosticIds.Pkcg005,
                    "$.analyzerComponents[].artifact",
                    "A packaged analyzer requires one exact package and no local project path.");
                break;
            default:
                diagnostics.Error(
                    CSharpBuildGateDiagnosticIds.Pkcg005,
                    "$.analyzerComponents[].artifact.kind",
                    "Analyzer artifact kind must be defined.");
                break;
        }

        diagnostics.Require(
            !string.IsNullOrWhiteSpace(artifact.AssemblyFileName) &&
            Path.GetFileName(artifact.AssemblyFileName) ==
                artifact.AssemblyFileName &&
            artifact.AssemblyFileName.EndsWith(
                ".dll",
                StringComparison.OrdinalIgnoreCase),
            CSharpBuildGateDiagnosticIds.Pkcg005,
            "$.analyzerComponents[].artifact.assemblyFileName",
            "Analyzer assembly file name must be one exact DLL file name.");
    }

    private static void ValidateRules(
        CSharpBuildGateDefinitionDocument value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.RuleCatalog is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg001,
                "$.ruleCatalog",
                "A rule catalog is required.");
            return;
        }

        var rules = value.RuleCatalog.Rules;
        var catalogDiagnostics = value.RuleCatalog.Diagnostics;
        CSharpBuildGateValidation.ValidateStableUnique(
            rules,
            static rule => rule.Identity.Value,
            "$.ruleCatalog.rules",
            diagnostics);
        CSharpBuildGateValidation.ValidateStableUnique(
            catalogDiagnostics,
            static diagnostic => diagnostic.DiagnosticId,
            "$.ruleCatalog.diagnostics",
            diagnostics);
        if (rules.IsDefaultOrEmpty || catalogDiagnostics.IsDefaultOrEmpty)
        {
            return;
        }

        var owners = value.SemanticOwners.ToDictionary(
            static owner => owner.Identity,
            static owner => owner);
        var diagnosticById = catalogDiagnostics.ToDictionary(
            static diagnostic => diagnostic.DiagnosticId,
            StringComparer.Ordinal);
        var componentRuleIds = value.AnalyzerComponents
            .SelectMany(static component => component.RuleIds.IsDefault
                ? []
                : component.RuleIds)
            .ToHashSet();
        foreach (var rule in rules)
        {
            diagnostics.Require(
                componentRuleIds.Contains(rule.Identity),
                CSharpBuildGateDiagnosticIds.Pkcg007,
                "$.ruleCatalog.rules",
                "Every rule must be selected by one exact analyzer component.");
            diagnostics.Require(
                owners.TryGetValue(rule.SemanticOwnerId, out var owner),
                CSharpBuildGateDiagnosticIds.Pkcg003,
                "$.ruleCatalog.rules",
                "Every rule must bind an exact semantic owner.");
            if (owner is not null)
            {
                var ownershipMatches =
                    rule.Kind == CSharpGateRuleKind.ProgramKitPublicContract
                        ? owner.Kind ==
                          CSharpAnalyzerComponentKind.ProgramKitPublicContract &&
                          rule.SourceContract == owner.GoverningContract &&
                          rule.DiagnosticId.StartsWith(
                              "PKCC",
                              StringComparison.Ordinal)
                        : owner.Kind ==
                          CSharpAnalyzerComponentKind.ConsumerOwned &&
                          owner.Identity == value.OwnerId &&
                          IsConsumerDiagnostic(rule.DiagnosticId);
                diagnostics.Require(
                    ownershipMatches,
                    CSharpBuildGateDiagnosticIds.Pkcg003,
                    "$.ruleCatalog.rules",
                    "Rule kind, source contract, semantic owner, and diagnostic namespace must agree exactly.");
            }

            diagnostics.Require(
                !rule.DiagnosticId.StartsWith("PKCS", StringComparison.Ordinal) &&
                !rule.DiagnosticId.StartsWith("PKCG", StringComparison.Ordinal),
                CSharpBuildGateDiagnosticIds.Pkcg004,
                "$.ruleCatalog.rules[].diagnosticId",
                "PKCS is private and PKCG is reserved for mechanics; neither may identify a consumer-source policy rule.");
            diagnostics.Require(
                diagnosticById.TryGetValue(
                    rule.DiagnosticId,
                    out var diagnosticDefinition) &&
                diagnosticDefinition.RuleId == rule.Identity &&
                diagnosticDefinition.RuleRevision == rule.Revision &&
                diagnosticDefinition.SemanticOwnerId == rule.SemanticOwnerId &&
                diagnosticDefinition.DefaultSeverity == rule.DefaultSeverity,
                CSharpBuildGateDiagnosticIds.Pkcg007,
                "$.ruleCatalog",
                "Every rule and diagnostic definition must form one exact meaning-preserving pair.");
            diagnostics.Require(
                rule.FocusedBudgetMilliseconds > 0 &&
                rule.FullBudgetMilliseconds >= rule.FocusedBudgetMilliseconds &&
                !string.IsNullOrWhiteSpace(rule.CompilationObservableClaim) &&
                !string.IsNullOrWhiteSpace(rule.LocationContract) &&
                !string.IsNullOrWhiteSpace(rule.MessageContract),
                CSharpBuildGateDiagnosticIds.Pkcg013,
                "$.ruleCatalog.rules",
                "Rules require an observable claim, deterministic location/message contracts, and positive ordered budgets.");
        }
    }

    private static void ValidateProfiles(
        CSharpBuildGateDefinitionDocument value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Profiles is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg001,
                "$.profiles",
                "A finite profile catalog is required.");
            return;
        }

        CSharpBuildGateValidation.ValidateStableUnique(
            value.Profiles.Projects,
            static profile => profile.Identity.Value,
            "$.profiles.projects",
            diagnostics);
        CSharpBuildGateValidation.ValidateStableUnique(
            value.Profiles.Inputs,
            static profile => profile.Identity.Value,
            "$.profiles.inputs",
            diagnostics);
        CSharpBuildGateValidation.ValidateStableUnique(
            value.Profiles.GeneratedSources,
            static profile => profile.Identity.Value,
            "$.profiles.generatedSources",
            diagnostics,
            requireOne: false);

        foreach (var project in value.Profiles.Projects)
        {
            diagnostics.Require(
                CSharpBuildGateValidation.IsExactRepositoryPath(
                    project.RepositoryRelativeProjectPath),
                CSharpBuildGateDiagnosticIds.Pkcg006,
                "$.profiles.projects[].repositoryRelativeProjectPath",
                "Project paths must be exact finite repository-relative paths.");
            CSharpBuildGateValidation.ValidateStableUnique(
                project.TargetFrameworks,
                static framework => framework,
                "$.profiles.projects[].targetFrameworks",
                diagnostics);
        }

        var physicalPaths = new HashSet<string>(StringComparer.Ordinal);
        foreach (var input in value.Profiles.Inputs)
        {
            ValidateInventory(
                input.Inventory,
                "$.profiles.inputs[].inventory",
                diagnostics);
            if (input.Kind == CSharpGateInputKind.PhysicalSource)
            {
                physicalPaths.UnionWith(
                    input.Inventory.Select(static item =>
                        item.RepositoryRelativePath));
            }
        }

        foreach (var generated in value.Profiles.GeneratedSources)
        {
            diagnostics.Require(
                generated.OwnerId == value.OwnerId &&
                !string.IsNullOrWhiteSpace(generated.OwnershipMarker),
                CSharpBuildGateDiagnosticIds.Pkcg003,
                "$.profiles.generatedSources",
                "Consumer-generated source must bind the consumer owner and an exact ownership marker.");
            CSharpBuildGateValidation.ValidateStableUnique(
                generated.LogicalHintPaths,
                static path => path,
                "$.profiles.generatedSources[].logicalHintPaths",
                diagnostics);
            ValidateInventory(
                generated.Inventory,
                "$.profiles.generatedSources[].inventory",
                diagnostics);
            diagnostics.Require(
                !generated.Inventory.Any(item =>
                    physicalPaths.Contains(item.RepositoryRelativePath)),
                CSharpBuildGateDiagnosticIds.Pkcg006,
                "$.profiles.generatedSources[].inventory",
                "Physical source cannot escape analysis by being relabeled as generated.");
        }
    }

    private static void ValidateInventory(
        ImmutableArray<CSharpGateContentItem> inventory,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        CSharpBuildGateValidation.ValidateStableUnique(
            inventory,
            static item => item.RepositoryRelativePath,
            path,
            diagnostics);
        if (!inventory.IsDefault)
        {
            diagnostics.Require(
                inventory.All(static item =>
                    CSharpBuildGateValidation.IsExactRepositoryPath(
                        item.RepositoryRelativePath)),
                CSharpBuildGateDiagnosticIds.Pkcg006,
                path,
                "Inventories accept exact repository-relative paths only; globs and traversal are forbidden.");
        }
    }

    private static void ValidateActivation(
        CSharpBuildGateDefinitionDocument value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.ActivationMatrix is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg008,
                "$.activationMatrix",
                "A finite activation matrix is required.");
            return;
        }

        CSharpBuildGateValidation.ValidateStableUnique(
            value.ActivationMatrix.Activations,
            ActivationKey,
            "$.activationMatrix.activations",
            diagnostics);
        var projects = value.Profiles.Projects
            .Select(static profile => profile.Identity)
            .ToHashSet();
        var sources = value.Profiles.Inputs
            .Select(static profile => profile.Identity)
            .Concat(value.Profiles.GeneratedSources.Select(
                static profile => profile.Identity))
            .ToHashSet();
        var components = value.AnalyzerComponents
            .Select(static component => component.Identity)
            .ToHashSet();
        var activatedComponents = new HashSet<ProgramKitIdentifier>();
        foreach (var activation in value.ActivationMatrix.Activations)
        {
            diagnostics.Require(
                projects.Contains(activation.ProjectProfileId) &&
                sources.Contains(activation.SourceProfileId),
                CSharpBuildGateDiagnosticIds.Pkcg008,
                "$.activationMatrix.activations",
                "Activation cells must bind exact declared project and source profiles.");
            CSharpBuildGateValidation.ValidateStableUnique(
                activation.AnalyzerComponentIds,
                static identity => identity.Value,
                "$.activationMatrix.activations[].analyzerComponentIds",
                diagnostics);
            diagnostics.Require(
                activation.AnalyzerComponentIds.All(components.Contains),
                CSharpBuildGateDiagnosticIds.Pkcg008,
                "$.activationMatrix.activations[].analyzerComponentIds",
                "Activation cells may select only exact declared analyzer components.");
            activatedComponents.UnionWith(activation.AnalyzerComponentIds);
        }

        diagnostics.Require(
            components.SetEquals(activatedComponents),
            CSharpBuildGateDiagnosticIds.Pkcg008,
            "$.activationMatrix",
            "Every selected analyzer component must participate in at least one exact activation cell.");
    }

    private static void ValidateExceptions(
        CSharpBuildGateDefinitionDocument value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        CSharpBuildGateValidation.ValidateStableUnique(
            value.TemporaryExceptions,
            static exception => exception.Identity.Value,
            "$.temporaryExceptions",
            diagnostics,
            requireOne: false);
        if (value.TemporaryExceptions.IsDefault)
        {
            return;
        }

        var rules = value.RuleCatalog.Rules
            .Select(static rule => rule.Identity)
            .ToHashSet();
        foreach (var exception in value.TemporaryExceptions)
        {
            var matchingComponentIds = value.AnalyzerComponents
                .Where(component => component.RuleIds.Contains(exception.RuleId))
                .Select(static component => component.Identity)
                .ToHashSet();
            var exactActivationExists = value.ActivationMatrix.Activations.Any(
                activation =>
                    activation.ProjectProfileId == exception.ProjectProfileId &&
                    activation.SourceProfileId == exception.SourceProfileId &&
                    activation.Command == exception.Command &&
                    activation.Boundary == exception.Boundary &&
                    activation.VerificationProfile ==
                        exception.VerificationProfile &&
                    activation.AnalyzerComponentIds.Any(
                        matchingComponentIds.Contains));
            diagnostics.Require(
                rules.Contains(exception.RuleId) &&
                exactActivationExists,
                CSharpBuildGateDiagnosticIds.Pkcg009,
                "$.temporaryExceptions",
                "A temporary exception must match one exact selected rule and activation scope.");
            diagnostics.Require(
                exception.ConsumerOwnerId == value.OwnerId &&
                exception.HumanAuthority is not null &&
                !string.IsNullOrWhiteSpace(exception.Rationale) &&
                !string.IsNullOrWhiteSpace(exception.ResidualRisk) &&
                !exception.CompensatingVerification.IsDefaultOrEmpty &&
                !exception.EvidenceRequirements.IsDefaultOrEmpty,
                CSharpBuildGateDiagnosticIds.Pkcg009,
                "$.temporaryExceptions",
                "Temporary exceptions require consumer ownership, human authority, risk, compensation, and evidence.");
            diagnostics.Require(
                exception.ExpiresAt is not null ||
                !string.IsNullOrWhiteSpace(exception.RemovalTrigger),
                CSharpBuildGateDiagnosticIds.Pkcg009,
                "$.temporaryExceptions",
                "Temporary exceptions require an expiry or deterministic removal trigger.");
            diagnostics.Require(
                exception.ExpiresAt is null ||
                exception.ExpiresAt > exception.ActivatedAt,
                CSharpBuildGateDiagnosticIds.Pkcg009,
                "$.temporaryExceptions.expiresAt",
                "Temporary exception expiry must be after activation.");
            diagnostics.Require(
                exception.MaximumUses is null || exception.MaximumUses > 0,
                CSharpBuildGateDiagnosticIds.Pkcg009,
                "$.temporaryExceptions.maximumUses",
                "Occurrence-bounded exceptions require a positive maximum use count.");
            diagnostics.Require(
                exception.ConditionKind ==
                    CSharpGateTemporaryExceptionConditionKind
                        .GateEstablishmentBoundary ||
                !exception.ConditionParameters.IsDefaultOrEmpty,
                CSharpBuildGateDiagnosticIds.Pkcg009,
                "$.temporaryExceptions.conditionParameters",
                "All non-boundary temporary conditions require exact digest-bound parameters.");
            CSharpBuildGateValidation.ValidateStableUnique(
                exception.ConditionParameters,
                static parameter => parameter.Name,
                "$.temporaryExceptions.conditionParameters",
                diagnostics,
                requireOne:
                    exception.ConditionKind !=
                    CSharpGateTemporaryExceptionConditionKind
                        .GateEstablishmentBoundary);
        }
    }

    private static void ValidateSuppressions(
        CSharpBuildGateDefinitionDocument value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.SuppressionLedger is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg010,
                "$.suppressionLedger",
                "A suppression ledger is required, even when it is explicitly empty.");
            return;
        }

        CSharpBuildGateValidation.ValidateStableUnique(
            value.SuppressionLedger.Entries,
            static entry => entry.Identity.Value,
            "$.suppressionLedger.entries",
            diagnostics,
            requireOne: false);
        if (value.SuppressionLedger.Entries.IsDefault)
        {
            return;
        }

        var rules = value.RuleCatalog.Rules.ToDictionary(
            static rule => rule.Identity,
            static rule => rule);
        var diagnosticsById = value.RuleCatalog.Diagnostics.ToDictionary(
            static diagnostic => diagnostic.DiagnosticId,
            StringComparer.Ordinal);
        var physicalSources = value.Profiles.Inputs
            .Where(static profile =>
                profile.Kind == CSharpGateInputKind.PhysicalSource)
            .SelectMany(static profile => profile.Inventory)
            .ToDictionary(
                static item => item.RepositoryRelativePath,
                static item => item.Digest,
                StringComparer.Ordinal);
        foreach (var entry in value.SuppressionLedger.Entries)
        {
            var known = rules.TryGetValue(entry.RuleId, out var rule) &&
                diagnosticsById.TryGetValue(
                    entry.DiagnosticId,
                    out var diagnostic) &&
                diagnostic.SemanticOwnerId ==
                    entry.DiagnosticSemanticOwnerId &&
                rule.Revision == entry.RuleRevision &&
                rule.SuppressionDisposition ==
                    CSharpGateSuppressionDisposition.SourceLocalLedger;
            diagnostics.Require(
                known,
                CSharpBuildGateDiagnosticIds.Pkcg010,
                "$.suppressionLedger.entries",
                "Suppression entries must bind an exact known suppressible diagnostic, owner, rule, and revision.");
            diagnostics.Require(
                physicalSources.TryGetValue(
                    entry.RepositoryRelativeSourcePath,
                    out var sourceDigest) &&
                sourceDigest == entry.SourceDigest,
                CSharpBuildGateDiagnosticIds.Pkcg010,
                "$.suppressionLedger.entries.repositoryRelativeSourcePath",
                "Suppressions are source-local and must bind an exact physical-source digest.");
            diagnostics.Require(
                entry.ExpiresAt is null || entry.ExpiresAt > entry.ApprovedAt,
                CSharpBuildGateDiagnosticIds.Pkcg010,
                "$.suppressionLedger.entries.expiresAt",
                "Suppression expiry must follow approval.");
            diagnostics.Require(
                !string.IsNullOrWhiteSpace(entry.Target) &&
                !string.IsNullOrWhiteSpace(entry.Rationale) &&
                !string.IsNullOrWhiteSpace(
                    entry.MigrationOrSupersessionCondition),
                CSharpBuildGateDiagnosticIds.Pkcg010,
                "$.suppressionLedger.entries",
                "Suppressions require an exact target, rationale, and migration or supersession condition.");
        }
    }

    private static void ValidateAssurance(
        CSharpBuildGateDefinitionDocument value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Assurance is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg013,
                "$.assurance",
                "Compatibility, migration, threat, fixture, and performance assurance is required.");
            return;
        }

        CSharpBuildGateValidation.ValidateStableUnique(
            value.Assurance.Migrations,
            static migration => string.Concat(
                migration.Source.Identity.Value,
                "@",
                migration.Source.Version.Value),
            "$.assurance.migrations",
            diagnostics,
            requireOne: false);
        CSharpBuildGateValidation.ValidateStableUnique(
            value.Assurance.Threats,
            static threat => threat.Identity.Value,
            "$.assurance.threats",
            diagnostics);
        CSharpBuildGateValidation.ValidateStableUnique(
            value.Assurance.Fixtures,
            static fixture => fixture.Identity.Value,
            "$.assurance.fixtures",
            diagnostics);
        diagnostics.Require(
            value.Assurance.Migrations.All(static migration =>
                migration.Source != migration.Target &&
                migration.RejectsLoss &&
                migration.IsDeterministic &&
                migration.IsIdempotent),
            CSharpBuildGateDiagnosticIds.Pkcg013,
            "$.assurance.migrations",
            "Gate migrations must be explicit, loss-rejecting, deterministic, and idempotent.");
        diagnostics.Require(
            value.Assurance.Performance is not null &&
            value.Assurance.Performance.FocusedMilliseconds > 0 &&
            value.Assurance.Performance.FullClosureMilliseconds >=
                value.Assurance.Performance.FocusedMilliseconds &&
            value.Assurance.Performance.MaximumAllocatedMegabytes > 0,
            CSharpBuildGateDiagnosticIds.Pkcg013,
            "$.assurance.performance",
            "Performance assurance requires positive ordered time and allocation budgets.");
    }

    private static string ActivationKey(CSharpGateActivation activation) =>
        string.Join(
            "|",
            activation.ProjectProfileId.Value,
            activation.SourceProfileId.Value,
            activation.Command,
            activation.Boundary,
            activation.VerificationProfile,
            string.Join(
                ",",
                activation.AnalyzerComponentIds.Select(
                    static identity => identity.Value)));

    private static bool IsConsumerPrefix(string value) =>
        !string.IsNullOrWhiteSpace(value) &&
        value.All(static character =>
            character is >= 'A' and <= 'Z' ||
            character is >= '0' and <= '9') &&
        !value.StartsWith("PK", StringComparison.Ordinal) &&
        !string.Equals(value, "CS", StringComparison.Ordinal);

    private static bool IsConsumerDiagnostic(string value) =>
        !string.IsNullOrWhiteSpace(value) &&
        !value.StartsWith("PKCS", StringComparison.Ordinal) &&
        !value.StartsWith("PKCC", StringComparison.Ordinal) &&
        !value.StartsWith("PKCG", StringComparison.Ordinal) &&
        !value.StartsWith("CS", StringComparison.Ordinal) &&
        value.All(static character =>
            character is >= 'A' and <= 'Z' ||
            character is >= '0' and <= '9');
}
