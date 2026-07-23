using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Pure semantic validation for an architecture-design document. The validator
/// reads no workspace, package graph, clock, environment, or generated output.
/// </summary>
public sealed class ArchitectureDesignValidator :
    IProgramKitSemanticValidator<ArchitectureDesignDocument>
{
    private readonly IArtifactDecisionValidator artifactDecisionValidator;

    /// <summary>Initializes the validator with artifact-decision validation behavior.</summary>
    public ArchitectureDesignValidator(
        IArtifactDecisionValidator artifactDecisionValidator)
    {
        this.artifactDecisionValidator = artifactDecisionValidator ??
            throw new ArgumentNullException(nameof(artifactDecisionValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArchitectureDesignDocument value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc600, "/", "An architecture design document is required.");
            return diagnostics.ToResult();
        }

        diagnostics.Required(value.Title, "/title", "Architecture title");
        diagnostics.Required(value.Intent, "/intent", "Architecture intent");
        RequireStatements(value.Scope, "/scope", "scope statement", diagnostics, requireOne: true);
        RequireStatements(value.NonGoals, "/nonGoals", "non-goal", diagnostics, requireOne: true);
        RequireStatements(value.Assumptions, "/assumptions", "assumption", diagnostics, requireOne: false);

        var declaredIds = CollectAndValidateDefinitionIdentities(value, diagnostics);
        var domainIds = ArchitectureValidation.OrEmpty(value.Domains)
            .Select(static domain => domain.Identity.Value)
            .Where(static identity => !string.IsNullOrWhiteSpace(identity))
            .ToHashSet(StringComparer.Ordinal);
        var contractIds = ArchitectureValidation.OrEmpty(value.Contracts)
            .Select(static contract => contract.Identity.Value)
            .Where(static identity => !string.IsNullOrWhiteSpace(identity))
            .ToHashSet(StringComparer.Ordinal);
        var componentById = ArchitectureValidation.OrEmpty(value.Components)
            .Where(static component => !string.IsNullOrWhiteSpace(component.Identity.Value))
            .GroupBy(static component => component.Identity.Value, StringComparer.Ordinal)
            .ToDictionary(static group => group.Key, static group => group.First(), StringComparer.Ordinal);
        var projectIds = ArchitectureValidation.OrEmpty(value.Projects)
            .Select(static project => project.Identity.Value)
            .Where(static identity => !string.IsNullOrWhiteSpace(identity))
            .ToHashSet(StringComparer.Ordinal);
        var packageIds = ArchitectureValidation.OrEmpty(value.Packages)
            .Select(static package => package.Identity.Value)
            .Where(static identity => !string.IsNullOrWhiteSpace(identity))
            .ToHashSet(StringComparer.Ordinal);

        ValidateOpenDecisions(value.UnresolvedDecisions, declaredIds, diagnostics);
        ValidateAuthorities(value.SourceTruthAuthorities, declaredIds, diagnostics);
        ValidateDomains(value.Domains, diagnostics);
        ValidateContracts(value.Contracts, domainIds, diagnostics);
        ValidateSemanticModels(value.SemanticModels, domainIds, contractIds, diagnostics);
        ValidateOperations(value.Operations, domainIds, diagnostics);
        ValidateComponents(value.Components, contractIds, diagnostics);
        ValidateProjects(value.Projects, componentById, projectIds, packageIds, diagnostics);
        ValidatePackages(value.Packages, projectIds, packageIds, contractIds, diagnostics);
        ValidateReferenceRules(value.ReferenceRules, diagnostics);
        ValidateExtensions(value.Extensions, componentById, diagnostics);
        ValidateConfiguration(value.Configuration, diagnostics);
        ValidateFeatureActivations(
            value.FeatureActivations,
            value.Configuration,
            componentById,
            diagnostics);
        ValidateArtifactDecisions(value.ArtifactDecisions, diagnostics);
        ValidateRepresentationRelationships(value, diagnostics);
        ValidateBoundaries(value.Boundaries, diagnostics);
        ValidateScenarios(value.Scenarios, diagnostics);
        ValidateStatusClaims(value.StatusClaims, declaredIds, diagnostics);

        return diagnostics.ToResult();
    }

    private static HashSet<string> CollectAndValidateDefinitionIdentities(
        ArchitectureDesignDocument design,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var declared = new HashSet<string>(StringComparer.Ordinal);

        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.UnresolvedDecisions),
            static item => item.Identity,
            "/unresolvedDecisions",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.SourceTruthAuthorities),
            static item => item.Identity,
            "/sourceTruthAuthorities",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Domains),
            static item => item.Identity,
            "/domains",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Contracts),
            static item => item.Identity,
            "/contracts",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.SemanticModels),
            static item => item.Identity,
            "/semanticModels",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Operations),
            static item => item.Identity,
            "/operations",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Components),
            static item => item.Identity,
            "/components",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Projects),
            static item => item.Identity,
            "/projects",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Packages),
            static item => item.Identity,
            "/packages",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.ReferenceRules),
            static item => item.Identity,
            "/referenceRules",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Extensions),
            static item => item.Identity,
            "/extensions",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Configuration),
            static item => item.Identity,
            "/configuration",
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.FeatureActivations),
            static item => item.Identity,
            "/featureActivations",
            declared,
            diagnostics);
        AddArtifactDecisions(
            ArchitectureValidation.OrEmpty(design.ArtifactDecisions),
            declared,
            diagnostics);
        AddDefinitions(
            ArchitectureValidation.OrEmpty(design.Scenarios),
            static item => item.Identity,
            "/scenarios",
            declared,
            diagnostics);

        return declared;
    }

    private static void AddArtifactDecisions(
        ImmutableArray<ArtifactDecision> values,
        HashSet<string> declared,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var decisions = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var identity = values[index].Identity;
            var path = $"/artifactDecisions/{index}/identity";
            diagnostics.Identifier(identity, path);
            if (string.IsNullOrWhiteSpace(identity.Value))
            {
                continue;
            }

            if (!decisions.Add(identity.Value))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc601,
                    path,
                    $"Artifact identity '{identity.Value}' has more than one artifact decision.");
            }

            // An ArtifactDecision is governance for the artifact whose identity
            // it carries, not a second semantic definition of that artifact.
            // It may therefore share an identity with the governed contract,
            // project, package, or other design definition.
            declared.Add(identity.Value);
        }
    }

    private static void AddDefinitions<T>(
        ImmutableArray<T> values,
        Func<T, ProgramKitIdentifier> identity,
        string path,
        HashSet<string> declared,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        for (var index = 0; index < values.Length; index++)
        {
            var id = identity(values[index]);
            diagnostics.Identifier(id, $"{path}/{index}/identity");
            if (!string.IsNullOrWhiteSpace(id.Value) && !declared.Add(id.Value))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc601,
                    $"{path}/{index}/identity",
                    $"Semantic identity '{id.Value}' is defined more than once in the design.");
            }
        }
    }

    private static void ValidateOpenDecisions(
        ImmutableArray<UnresolvedDecision> values,
        HashSet<string> declaredIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var decisions = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < decisions.Length; index++)
        {
            var decision = decisions[index];
            var path = $"/unresolvedDecisions/{index}";
            diagnostics.Identifier(decision.OwnerId, $"{path}/ownerId");
            diagnostics.Required(decision.Question, $"{path}/question", "Unresolved question");
            diagnostics.Required(
                decision.DecisionNeededBy,
                $"{path}/decisionNeededBy",
                "Decision-needed-by boundary");
            diagnostics.Required(
                decision.BlockingEffect,
                $"{path}/blockingEffect",
                "Unresolved-decision blocking effect");
            if (decision.OwnerId == decision.Identity)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc602,
                    $"{path}/ownerId",
                    "An unresolved decision cannot own itself.");
            }

            _ = declaredIds;
        }
    }

    private static void ValidateAuthorities(
        ImmutableArray<SourceTruthAuthority> values,
        HashSet<string> declaredIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var authorities = ArchitectureValidation.OrEmpty(values);
        if (authorities.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc603,
                "/sourceTruthAuthorities",
                "At least one source-truth authority is required.");
        }

        for (var index = 0; index < authorities.Length; index++)
        {
            var authority = authorities[index];
            var path = $"/sourceTruthAuthorities/{index}";
            diagnostics.Identifier(authority.OwnerId, $"{path}/ownerId");
            diagnostics.Reference(authority.Source, $"{path}/source");
            diagnostics.Required(authority.SourcePath, $"{path}/sourcePath", "Source path");
            diagnostics.Required(authority.Governs, $"{path}/governs", "Source authority scope");
            _ = declaredIds;
        }
    }

    private static void ValidateDomains(
        ImmutableArray<DomainDefinition> values,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var domains = ArchitectureValidation.OrEmpty(values);
        if (domains.Length == 0)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc604, "/domains", "At least one domain is required.");
        }

        for (var index = 0; index < domains.Length; index++)
        {
            var domain = domains[index];
            var path = $"/domains/{index}";
            if (!string.Equals(domain.Identity.Kind, "domain", StringComparison.Ordinal))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc605,
                    $"{path}/identity",
                    "A domain identity must use the 'domain' PKID kind.");
            }

            diagnostics.Required(domain.Purpose, $"{path}/purpose", "Domain purpose");
            var vocabulary = ArchitectureValidation.OrEmpty(domain.Vocabulary);
            if (vocabulary.Length == 0)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc606,
                    $"{path}/vocabulary",
                    "A domain must own at least one vocabulary term.");
            }

            var terms = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            for (var termIndex = 0; termIndex < vocabulary.Length; termIndex++)
            {
                var term = vocabulary[termIndex];
                var termPath = $"{path}/vocabulary/{termIndex}";
                diagnostics.Required(term.Term, $"{termPath}/term", "Vocabulary term");
                diagnostics.Required(term.Meaning, $"{termPath}/meaning", "Vocabulary meaning");
                if (!string.IsNullOrWhiteSpace(term.Term) && !terms.Add(term.Term))
                {
                    diagnostics.Error(
                        ArchitectureDiagnosticIds.Pkarc607,
                        $"{termPath}/term",
                        "Vocabulary terms must be unique within their owning domain.");
                }

                RequireStatements(
                    term.AcceptedAliases,
                    $"{termPath}/acceptedAliases",
                    "accepted alias",
                    diagnostics,
                    requireOne: false);
            }
        }
    }

    private static void ValidateContracts(
        ImmutableArray<ContractDefinition> values,
        HashSet<string> domainIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var contracts = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < contracts.Length; index++)
        {
            var contract = contracts[index];
            var path = $"/contracts/{index}";
            RequireLocalDomain(contract.OwnerDomainId, domainIds, $"{path}/ownerDomainId", diagnostics);
            if (!Enum.IsDefined(contract.Kind))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc637,
                    $"{path}/kind",
                    "The contract kind is unsupported.");
            }

            diagnostics.Version(contract.Version, $"{path}/version");
            diagnostics.Reference(contract.Schema, $"{path}/schema");
            diagnostics.Required(contract.Meaning, $"{path}/meaning", "Contract meaning");
            diagnostics.Required(
                contract.CompatibilityPolicy,
                $"{path}/compatibilityPolicy",
                "Contract compatibility policy");
        }
    }

    private static void ValidateSemanticModels(
        ImmutableArray<SemanticModelDefinition> values,
        HashSet<string> domainIds,
        HashSet<string> contractIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var models = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < models.Length; index++)
        {
            var model = models[index];
            var path = $"/semanticModels/{index}";
            RequireLocalDomain(model.OwnerDomainId, domainIds, $"{path}/ownerDomainId", diagnostics);
            diagnostics.Required(model.Meaning, $"{path}/meaning", "Semantic model meaning");
            diagnostics.Required(model.Invariants, $"{path}/invariants", "Semantic model invariants");
            var termContracts = ArchitectureValidation.OrEmpty(model.TermContractIds);
            for (var referenceIndex = 0; referenceIndex < termContracts.Length; referenceIndex++)
            {
                RequireLocal(
                    termContracts[referenceIndex],
                    contractIds,
                    $"{path}/termContractIds/{referenceIndex}",
                    "contract",
                    diagnostics);
            }
        }
    }

    private static void ValidateOperations(
        ImmutableArray<OperationDefinition> values,
        HashSet<string> domainIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var operations = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < operations.Length; index++)
        {
            var operation = operations[index];
            var path = $"/operations/{index}/";
            OperationDefinitionValidator.ValidateInto(operation, path, diagnostics);
            RequireLocalDomain(
                operation.OwnerDomainId,
                domainIds,
                $"/operations/{index}/ownerDomainId",
                diagnostics);
        }
    }

    private static void ValidateComponents(
        ImmutableArray<ComponentDefinition> values,
        HashSet<string> contractIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var components = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < components.Length; index++)
        {
            var component = components[index];
            var path = $"/components/{index}";
            diagnostics.Identifier(component.OwnerId, $"{path}/ownerId");
            diagnostics.Required(component.Purpose, $"{path}/purpose", "Component purpose");
            diagnostics.Required(
                component.CompatibilityBoundary,
                $"{path}/compatibilityBoundary",
                "Component compatibility boundary");

            if (!Enum.IsDefined(component.Kind))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc638,
                    $"{path}/kind",
                    "The component kind is unsupported.");
            }

            if (component.Kind is ComponentKind.DomainCore or ComponentKind.FocusedHelper &&
                component.IsActivatable)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc608,
                    $"{path}/isActivatable",
                    "Domain cores and focused helpers cannot be activatable.");
            }

            if (component.Kind == ComponentKind.Feature && !component.IsActivatable)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc609,
                    $"{path}/isActivatable",
                    "A feature must be explicitly activatable.");
            }

            ValidateContractIds(
                component.ProvidesContractIds,
                contractIds,
                $"{path}/providesContractIds",
                diagnostics);
            ValidateContractIds(
                component.ConsumesContractIds,
                contractIds,
                $"{path}/consumesContractIds",
                diagnostics);
        }
    }

    private static void ValidateProjects(
        ImmutableArray<ProjectDefinition> values,
        Dictionary<string, ComponentDefinition> componentById,
        HashSet<string> projectIds,
        HashSet<string> packageIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var projects = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < projects.Length; index++)
        {
            var project = projects[index];
            var path = $"/projects/{index}";
            diagnostics.Identifier(project.OwnerId, $"{path}/ownerId");
            ValidateRelativePath(project.ProjectPath, $"{path}/projectPath", diagnostics);

            var components = ArchitectureValidation.OrEmpty(project.ComponentIds);
            if (components.Length == 0)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc610,
                    $"{path}/componentIds",
                    "A project must implement at least one component.");
            }

            for (var componentIndex = 0; componentIndex < components.Length; componentIndex++)
            {
                RequireLocal(
                    components[componentIndex],
                    componentById.Keys,
                    $"{path}/componentIds/{componentIndex}",
                    "component",
                    diagnostics);
            }

            var references = ArchitectureValidation.OrEmpty(project.ProjectReferenceIds);
            for (var referenceIndex = 0; referenceIndex < references.Length; referenceIndex++)
            {
                RequireLocal(
                    references[referenceIndex],
                    projectIds,
                    $"{path}/projectReferenceIds/{referenceIndex}",
                    "project",
                    diagnostics);
                if (references[referenceIndex] == project.Identity)
                {
                    diagnostics.Error(
                        ArchitectureDiagnosticIds.Pkarc611,
                        $"{path}/projectReferenceIds/{referenceIndex}",
                        "A project cannot reference itself.");
                }
            }

            if (project.PackageId is not null)
            {
                RequireLocal(
                    project.PackageId.Value,
                    packageIds,
                    $"{path}/packageId",
                    "package",
                    diagnostics);
            }
        }
    }

    private static void ValidatePackages(
        ImmutableArray<PackageDefinition> values,
        HashSet<string> projectIds,
        HashSet<string> packageIds,
        HashSet<string> contractIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var packages = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < packages.Length; index++)
        {
            var package = packages[index];
            var path = $"/packages/{index}";
            diagnostics.Identifier(package.OwnerId, $"{path}/ownerId");
            diagnostics.Version(package.Version, $"{path}/version");
            diagnostics.Required(
                package.CompatibilityBoundary,
                $"{path}/compatibilityBoundary",
                "Package compatibility boundary");

            var projects = ArchitectureValidation.OrEmpty(package.ProjectIds);
            if (projects.Length == 0)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc612,
                    $"{path}/projectIds",
                    "A package must contain at least one project.");
            }

            for (var projectIndex = 0; projectIndex < projects.Length; projectIndex++)
            {
                RequireLocal(
                    projects[projectIndex],
                    projectIds,
                    $"{path}/projectIds/{projectIndex}",
                    "project",
                    diagnostics);
            }

            var dependencies = ArchitectureValidation.OrEmpty(package.PackageDependencyIds);
            for (var dependencyIndex = 0; dependencyIndex < dependencies.Length; dependencyIndex++)
            {
                RequireLocal(
                    dependencies[dependencyIndex],
                    packageIds,
                    $"{path}/packageDependencyIds/{dependencyIndex}",
                    "package",
                    diagnostics);
                if (dependencies[dependencyIndex] == package.Identity)
                {
                    diagnostics.Error(
                        ArchitectureDiagnosticIds.Pkarc613,
                        $"{path}/packageDependencyIds/{dependencyIndex}",
                        "A package cannot depend on itself.");
                }
            }

            ValidateContractIds(
                package.PublicContractIds,
                contractIds,
                $"{path}/publicContractIds",
                diagnostics);
        }
    }

    private static void ValidateReferenceRules(
        ImmutableArray<ReferenceRuleDefinition> values,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var rules = ArchitectureValidation.OrEmpty(values);
        if (rules.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc614,
                "/referenceRules",
                "Allowed and forbidden reference rules must be explicit.");
        }

        for (var index = 0; index < rules.Length; index++)
        {
            var rule = rules[index];
            var path = $"/referenceRules/{index}";
            diagnostics.Identifier(rule.OwnerId, $"{path}/ownerId");
            if (!Enum.IsDefined(rule.Disposition))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc639,
                    $"{path}/disposition",
                    "The reference-rule disposition is unsupported.");
            }

            diagnostics.Required(rule.ReferencingScope, $"{path}/referencingScope", "Referencing scope");
            diagnostics.Required(rule.ReferencedScope, $"{path}/referencedScope", "Referenced scope");
            diagnostics.Required(rule.Rationale, $"{path}/rationale", "Reference-rule rationale");
            if (rule.OwnerInput is null)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc615,
                    $"{path}/ownerInput",
                    "A reference rule must trace to its owner input.");
            }
            else
            {
                diagnostics.Reference(rule.OwnerInput.Artifact, $"{path}/ownerInput/artifact");
                diagnostics.Required(
                    rule.OwnerInput.Path,
                    $"{path}/ownerInput/path",
                    "Owner-input path");
            }
        }
    }

    private static void ValidateExtensions(
        ImmutableArray<ExtensionDefinition> values,
        Dictionary<string, ComponentDefinition> componentById,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var extensions = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < extensions.Length; index++)
        {
            var extension = extensions[index];
            var path = $"/extensions/{index}/";
            ExtensionDefinitionValidator.ValidateInto(extension, path, diagnostics);
            var provider = extension.Semantics?.ProviderSpecialization;
            if (provider is not null)
            {
                if (!componentById.TryGetValue(provider.BaseProviderId.Value, out var component))
                {
                    diagnostics.Error(
                        ArchitectureDiagnosticIds.Pkarc616,
                        $"/extensions/{index}/semantics/providerSpecialization/baseProviderId",
                        "The base provider must be a component declared by this design.");
                }
                else if (component.Kind != ComponentKind.Provider)
                {
                    diagnostics.Error(
                        ArchitectureDiagnosticIds.Pkarc617,
                        $"/extensions/{index}/semantics/providerSpecialization/baseProviderId",
                        "The base provider component must have provider kind.");
                }
            }
        }
    }

    private static void ValidateConfiguration(
        ImmutableArray<ConfigurationDefinition> values,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var configurations = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < configurations.Length; index++)
        {
            var configuration = configurations[index];
            var path = $"/configuration/{index}";
            diagnostics.Identifier(configuration.OwnerId, $"{path}/ownerId");
            diagnostics.Reference(configuration.Schema, $"{path}/schema");
            diagnostics.Required(configuration.Scope, $"{path}/scope", "Configuration scope");
            diagnostics.Required(
                configuration.SecretsPolicy,
                $"{path}/secretsPolicy",
                "Configuration secrets policy");
            diagnostics.Required(
                configuration.CompatibilityPolicy,
                $"{path}/compatibilityPolicy",
                "Configuration compatibility policy");
        }
    }

    private static void ValidateFeatureActivations(
        ImmutableArray<FeatureActivationDefinition> values,
        ImmutableArray<ConfigurationDefinition> configurations,
        Dictionary<string, ComponentDefinition> componentById,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var configurationIds = ArchitectureValidation.OrEmpty(configurations)
            .Select(static configuration => configuration.Identity.Value)
            .Where(static identity => !string.IsNullOrWhiteSpace(identity))
            .ToHashSet(StringComparer.Ordinal);
        var activations = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < activations.Length; index++)
        {
            var activation = activations[index];
            var path = $"/featureActivations/{index}";
            diagnostics.Identifier(activation.OwnerId, $"{path}/ownerId");
            diagnostics.Identifier(activation.FeatureId, $"{path}/featureId");
            if (!componentById.TryGetValue(activation.FeatureId.Value, out var feature))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc618,
                    $"{path}/featureId",
                    "Feature activation must reference a component declared by this design.");
            }
            else if (feature.Kind != ComponentKind.Feature)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc619,
                    $"{path}/featureId",
                    "Feature activation must reference a feature component.");
            }

            if (activation.ConfigurationId is not null)
            {
                RequireLocal(
                    activation.ConfigurationId.Value,
                    configurationIds,
                    $"{path}/configurationId",
                    "configuration",
                    diagnostics);
            }

            diagnostics.Required(
                activation.SelectionSemantics,
                $"{path}/selectionSemantics",
                "Activation selection semantics");
            diagnostics.Required(
                activation.FailureSemantics,
                $"{path}/failureSemantics",
                "Activation failure semantics");
        }
    }

    private void ValidateArtifactDecisions(
        ImmutableArray<ArtifactDecision> values,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var decisions = ArchitectureValidation.OrEmpty(values);
        if (decisions.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc620,
                "/artifactDecisions",
                "At least one intent-to-artifact decision is required.");
        }

        for (var index = 0; index < decisions.Length; index++)
        {
            diagnostics.Add(artifactDecisionValidator.Validate(
                decisions[index],
                $"/artifactDecisions/{index}/"));
        }
    }

    private static void ValidateRepresentationRelationships(
        ArchitectureDesignDocument design,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var decisions = ArchitectureValidation.OrEmpty(design.ArtifactDecisions)
            .Where(static decision => !string.IsNullOrWhiteSpace(decision.Identity.Value))
            .GroupBy(static decision => decision.Identity.Value, StringComparer.Ordinal)
            .ToDictionary(static group => group.Key, static group => group.First(), StringComparer.Ordinal);
        var relationships = ArchitectureValidation.OrEmpty(design.RepresentationRelationships);
        var projections = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < relationships.Length; index++)
        {
            var relationship = relationships[index];
            var path = $"/representationRelationships/{index}";
            diagnostics.Identifier(relationship.ProjectionId, $"{path}/projectionId");
            diagnostics.Identifier(relationship.CanonicalId, $"{path}/canonicalId");
            diagnostics.Required(
                relationship.ProjectionRule,
                $"{path}/projectionRule",
                "Projection rule");
            diagnostics.Required(relationship.LossPolicy, $"{path}/lossPolicy", "Projection loss policy");
            if (!projections.Add(relationship.ProjectionId.Value))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc621,
                    $"{path}/projectionId",
                    "A projection may have only one canonical relationship.");
            }

            if (!decisions.TryGetValue(relationship.ProjectionId.Value, out var projection))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc622,
                    $"{path}/projectionId",
                    "The projection must have an artifact decision.");
            }
            else if (projection.Representation?.Role != ArtifactRepresentationRole.Projection)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc623,
                    $"{path}/projectionId",
                    "The projection artifact decision must select projection role.");
            }

            if (!decisions.TryGetValue(relationship.CanonicalId.Value, out var canonical))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc624,
                    $"{path}/canonicalId",
                    "The canonical artifact must have an artifact decision.");
            }
            else if (canonical.Representation?.Role != ArtifactRepresentationRole.Canonical)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc625,
                    $"{path}/canonicalId",
                    "The canonical artifact decision must select canonical role.");
            }

            if (projection?.Representation?.CanonicalArtifactId != relationship.CanonicalId)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc626,
                    path,
                    "The relationship must match the projection's canonical-artifact answer.");
            }
        }

        foreach (var decision in decisions.Values)
        {
            if (decision.Representation?.Role == ArtifactRepresentationRole.Projection &&
                !projections.Contains(decision.Identity.Value))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc627,
                    "/representationRelationships",
                    $"Projection '{decision.Identity.Value}' requires a canonical relationship.");
            }
        }
    }

    private static void ValidateBoundaries(
        ArchitectureBoundarySet? boundaries,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (boundaries is null)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc628,
                "/boundaries",
                "Security, authority, secrets, persistence, failure, concurrency, cancellation, observability, and compatibility boundaries are required.");
            return;
        }

        ValidateBoundary(boundaries.Security, "/boundaries/security", diagnostics);
        ValidateBoundary(boundaries.Authority, "/boundaries/authority", diagnostics);
        ValidateBoundary(boundaries.Secrets, "/boundaries/secrets", diagnostics);
        ValidateBoundary(boundaries.Persistence, "/boundaries/persistence", diagnostics);
        ValidateBoundary(boundaries.Failure, "/boundaries/failure", diagnostics);
        ValidateBoundary(boundaries.Concurrency, "/boundaries/concurrency", diagnostics);
        ValidateBoundary(boundaries.Cancellation, "/boundaries/cancellation", diagnostics);
        ValidateBoundary(boundaries.Observability, "/boundaries/observability", diagnostics);
        ValidateBoundary(boundaries.Compatibility, "/boundaries/compatibility", diagnostics);
    }

    private static void ValidateBoundary(
        BoundaryDefinition? boundary,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (boundary is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc629, path, "The named architecture boundary is required.");
            return;
        }

        diagnostics.Identifier(boundary.OwnerId, $"{path}/ownerId");
        diagnostics.Required(boundary.Policy, $"{path}/policy", "Boundary policy");
        RequireStatements(
            boundary.Guarantees,
            $"{path}/guarantees",
            "boundary guarantee",
            diagnostics,
            requireOne: true);
        RequireStatements(
            boundary.Exclusions,
            $"{path}/exclusions",
            "boundary exclusion",
            diagnostics,
            requireOne: true);
    }

    private static void ValidateScenarios(
        ImmutableArray<CallerVisibleScenario> values,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var scenarios = ArchitectureValidation.OrEmpty(values);
        if (scenarios.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc630,
                "/scenarios",
                "At least one caller-visible scenario is required.");
        }

        for (var index = 0; index < scenarios.Length; index++)
        {
            var scenario = scenarios[index];
            var path = $"/scenarios/{index}";
            diagnostics.Required(scenario.Actor, $"{path}/actor", "Scenario actor");
            diagnostics.Required(scenario.Intent, $"{path}/intent", "Scenario intent");
            RequireStatements(
                scenario.Preconditions,
                $"{path}/preconditions",
                "scenario precondition",
                diagnostics,
                requireOne: false);
            RequireStatements(scenario.Steps, $"{path}/steps", "scenario step", diagnostics, requireOne: true);
            RequireStatements(
                scenario.Outcomes,
                $"{path}/outcomes",
                "scenario outcome",
                diagnostics,
                requireOne: true);
            RequireStatements(
                scenario.FailureOutcomes,
                $"{path}/failureOutcomes",
                "scenario failure outcome",
                diagnostics,
                requireOne: true);
        }
    }

    private static void ValidateStatusClaims(
        ImmutableArray<ArchitectureStatusClaim> values,
        HashSet<string> declaredIds,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var claims = ArchitectureValidation.OrEmpty(values);
        if (claims.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc631,
                "/statusClaims",
                "At least one truthful implementation-status claim is required.");
        }

        var subjects = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < claims.Length; index++)
        {
            var claim = claims[index];
            var path = $"/statusClaims/{index}";
            RequireLocal(claim.SubjectId, declaredIds, $"{path}/subjectId", "status subject", diagnostics);
            diagnostics.Required(claim.Claim, $"{path}/claim", "Status claim");
            if (!Enum.IsDefined(claim.Status))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc640,
                    $"{path}/status",
                    "The architecture status is unsupported.");
            }

            if (!subjects.Add(claim.SubjectId.Value))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc632,
                    $"{path}/subjectId",
                    "A subject may have only one implementation-status claim.");
            }

            var evidence = ArchitectureValidation.OrEmpty(claim.Evidence);
            if (claim.Status is ArtifactStatus.Implemented or ArtifactStatus.Scaffolded &&
                evidence.Length == 0)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc633,
                    $"{path}/evidence",
                    "Implemented and scaffolded claims require exact evidence.");
            }

            for (var evidenceIndex = 0; evidenceIndex < evidence.Length; evidenceIndex++)
            {
                diagnostics.Reference(evidence[evidenceIndex], $"{path}/evidence/{evidenceIndex}");
            }
        }
    }

    private static void ValidateContractIds(
        ImmutableArray<ProgramKitIdentifier> values,
        HashSet<string> contractIds,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var references = ArchitectureValidation.OrEmpty(values);
        for (var index = 0; index < references.Length; index++)
        {
            RequireLocal(references[index], contractIds, $"{path}/{index}", "contract", diagnostics);
        }
    }

    private static void RequireLocalDomain(
        ProgramKitIdentifier identity,
        HashSet<string> domainIds,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        RequireLocal(identity, domainIds, path, "domain", diagnostics);

    private static void RequireLocal(
        ProgramKitIdentifier identity,
        IEnumerable<string> declared,
        string path,
        string description,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        diagnostics.Identifier(identity, path);
        if (!declared.Contains(identity.Value, StringComparer.Ordinal))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc634,
                path,
                $"The referenced {description} '{identity.Value}' is not declared by this design.");
        }
    }

    private static void ValidateRelativePath(
        string? value,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        diagnostics.Required(value, path, "Project path");
        if (string.IsNullOrWhiteSpace(value))
        {
            return;
        }

        var startsWithDrive =
            value.Length >= 2 &&
            value[0] is (>= 'A' and <= 'Z') or (>= 'a' and <= 'z') &&
            value[1] == ':';
        if (value[0] == '/' ||
            value[0] == '\\' ||
            startsWithDrive ||
            value.Contains('\\', StringComparison.Ordinal) ||
            value.Split('/').Any(static segment => segment is "." or ".." or ""))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc635,
                path,
                "Project paths must be normalized, relative, forward-slash paths without traversal.");
        }
    }

    private static void RequireStatements(
        ImmutableArray<string> values,
        string path,
        string description,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        bool requireOne)
    {
        var statements = ArchitectureValidation.OrEmpty(values);
        if (requireOne && statements.Length == 0)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc636, path, $"At least one {description} is required.");
        }

        for (var index = 0; index < statements.Length; index++)
        {
            diagnostics.Required(statements[index], $"{path}/{index}", description);
        }
    }
}
