using Orbyss.ProgramKit.DotNet.Configuration;
using System.Globalization;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Health;
using Orbyss.ProgramKit.DotNet.Operations;
using Orbyss.ProgramKit.DotNet.Packages;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Operations.Contracts.Validation;

namespace Orbyss.ProgramKit.DotNet.Validation;

/// <summary>Default deterministic validator for exact shell composition intent.</summary>
public sealed class DotNetShellValidator : IDotNetShellValidator
{
    private readonly IProgramKitSemanticValidator<ArtifactReference> referenceValidator;
    private readonly IProgramKitSemanticValidator<OperationContractDescriptor>
        operationValidator;

    /// <summary>Initializes the validator with exact-reference behavior.</summary>
    public DotNetShellValidator(
        IProgramKitSemanticValidator<ArtifactReference> referenceValidator,
        IProgramKitSemanticValidator<OperationContractDescriptor> operationValidator)
    {
        this.referenceValidator = referenceValidator ??
            throw new ArgumentNullException(nameof(referenceValidator));
        this.operationValidator = operationValidator ??
            throw new ArgumentNullException(nameof(operationValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(DotNetShellDocument value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "A shell document is required.", string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (!string.Equals(value.Schema, "pkid:schema:program-kit:dotnet-shell@3.0.0", StringComparison.Ordinal))
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "The exact DotNet shell schema is required.", "/$schema");
        }

        if (value.Version.Value != "3.0.0")
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "The shell document version must be 3.0.0.", "/version");
        }

        ValidateReference(value.InputVersionMapRevision, "/inputVersionMapRevision", diagnostics);
        ValidateReference(value.InputVersionSelectionRevision, "/inputVersionSelectionRevision", diagnostics);
        ValidateComposition(value.Composition, diagnostics);
        ValidateFeatures(value.Features, value.Composition, diagnostics);
        ValidateHosts(value.Hosts, value.Features, value.Composition, diagnostics);
        ValidateSerialization(value.JsonSerialization, diagnostics);
        ValidateCompatibility(value.Compatibility, "/compatibility", diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private void ValidateReference(
        ArtifactReference? reference,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (reference is null)
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "An exact artifact reference is required.", path);
            return;
        }

        foreach (var diagnostic in referenceValidator.Validate(reference).Diagnostics)
        {
            diagnostics.Add(diagnostic with { Path = string.Concat(path, diagnostic.Path) });
        }
    }

    private static void ValidateComposition(
        DotNetShellComposition? composition,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (composition is null ||
            !string.Equals(composition.Provider, "cshells", StringComparison.Ordinal) ||
            !string.Equals(composition.AbiVersion.Value, "0.0.28", StringComparison.Ordinal))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "The baseline requires the exact 'cshells' provider and ABI 0.0.28.",
                "/composition");
            return;
        }

        RequireInitializedUnique(
            composition.Shells,
            static item => item.Identity.Value,
            "/composition/shells",
            diagnostics);
        foreach (var shell in composition.Shells)
        {
            RequireInitializedUnique(
                shell.EnabledFeatures,
                static item => item,
                "/composition/shells/enabledFeatures",
                diagnostics);
        }
    }

    private static void ValidateFeatures(
        ImmutableArray<DotNetFeatureSelection> features,
        DotNetShellComposition? composition,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        RequireInitializedUnique(
            features,
            static item => item.ActivationIdentity.Value,
            "/features",
            diagnostics);
        var shells = composition?.Shells.IsDefault == false
            ? composition.Shells.Select(static shell => shell.Identity.Value).ToHashSet(StringComparer.Ordinal)
            : [];
        foreach (var feature in features)
        {
            if (!shells.Contains(feature.ShellIdentity.Value))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "A feature must select a declared shell.", "/features/shellIdentity");
            }

            if (string.IsNullOrWhiteSpace(feature.FeatureTypeName) ||
                !feature.FeatureTypeName.Contains('.', StringComparison.Ordinal))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "A feature requires a namespace-qualified type name.", "/features/featureTypeName");
            }

            ValidatePackage(feature.Package, "/features/package", diagnostics);
        }
    }

    private void ValidateHosts(
        ImmutableArray<DotNetHostDefinition> hosts,
        ImmutableArray<DotNetFeatureSelection> features,
        DotNetShellComposition? composition,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        RequireInitializedUnique(hosts, static item => item.Identity.Value, "/hosts", diagnostics);
        var activations = features.IsDefault
            ? []
            : features.Select(static feature => feature.ActivationIdentity.Value).ToHashSet(StringComparer.Ordinal);
        var shells = composition?.Shells.IsDefault == false
            ? composition.Shells.Select(static shell => shell.Identity.Value).ToHashSet(StringComparer.Ordinal)
            : [];
        foreach (var host in hosts)
        {
            if (!Enum.IsDefined(host.Kind))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHostSelection, "The host kind is not supported.", "/hosts/kind");
            }

            ValidateReference(
                host.DotNetTargetProfileRevision,
                "/hosts/dotNetTargetProfileRevision",
                diagnostics);
            ValidateReference(
                host.GeneratorProfileRevision,
                "/hosts/generatorProfileRevision",
                diagnostics);
            RequireInitializedUnique(
                host.ShellIdentities,
                static item => item.Value,
                "/hosts/shellIdentities",
                diagnostics);
            if (host.ShellIdentities.Any(item => !shells.Contains(item.Value)))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHostSelection, "Every host shell must be declared by the composition.", "/hosts/shellIdentities");
            }

            RequireInitializedUnique(
                host.FeatureActivationIdentities,
                static item => item.Value,
                "/hosts/featureActivationIdentities",
                diagnostics);
            if (host.FeatureActivationIdentities.Any(item => !activations.Contains(item.Value)))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHostSelection, "Every host feature activation must be declared by the shell.", "/hosts/featureActivationIdentities");
            }

            RequireInitializedUnique(host.HostPackages, DotNetContractKeys.Package, "/hosts/hostPackages", diagnostics);
            foreach (var package in host.HostPackages)
            {
                ValidatePackage(package, "/hosts/hostPackages", diagnostics);
            }

            ValidateHostPackages(host, diagnostics);
            ValidateHostPackageClosure(host, features, diagnostics);
            ValidateOperations(host.OperationBindings, diagnostics);
            ValidateConfiguration(
                host.ConfigurationSources,
                host.ConfigurationBindings,
                diagnostics);
            ValidateTaskRuntime(host.TaskRuntimeRequirements, diagnostics);
            ValidateHealth(host.Health, host.OperationBindings, diagnostics);
            ValidateCompatibility(host.Compatibility, "/hosts/compatibility", diagnostics);
        }
    }

    private static void ValidateHostPackages(
        DotNetHostDefinition host,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var packages = host.HostPackages.IsDefault
            ? new Dictionary<string, DotNetPackageReference>(StringComparer.Ordinal)
            : host.HostPackages.ToDictionary(static item => item.PackageId, StringComparer.Ordinal);
        RequirePackage(packages, "CShells", diagnostics);
        if (host.Kind == DotNetHostKind.Api)
        {
            RequirePackage(packages, "CShells.AspNetCore", diagnostics);
        }
        if (!host.ConfigurationBindings.IsDefaultOrEmpty)
        {
            RequirePackage(
                packages,
                "Microsoft.Extensions.Configuration.Binder",
                diagnostics);
            RequirePackage(
                packages,
                "Microsoft.Extensions.Options",
                diagnostics);
            RequirePackage(
                packages,
                "Microsoft.Extensions.Options.ConfigurationExtensions",
                diagnostics);
            RequirePackage(
                packages,
                "Microsoft.Extensions.Options.DataAnnotations",
                diagnostics);
        }

        foreach (var package in packages.Values.Where(static package =>
                     package.PackageId.StartsWith("CShells", StringComparison.Ordinal)))
        {
            if (!string.Equals(package.Version.Value, "0.0.28", StringComparison.Ordinal))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "Every CShells package must be pinned to 0.0.28.", "/hosts/hostPackages/version");
            }
        }
    }

    private static void ValidateHostPackageClosure(
        DotNetHostDefinition host,
        ImmutableArray<DotNetFeatureSelection> features,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var activations = host.FeatureActivationIdentities.ToHashSet();
        var packages = host.HostPackages
            .Concat(
                host.ConfigurationSources
                    .Select(static source => source.Package))
            .Concat(
                features
                    .Where(feature => activations.Contains(feature.ActivationIdentity))
                    .Select(static feature => feature.Package));
        foreach (var group in packages.GroupBy(static package => package.PackageId, StringComparer.Ordinal))
        {
            var exactSelections = group
                .Select(static package => string.Concat(
                    package.Version.Value,
                    "#",
                    package.Sha256.Value))
                .Distinct(StringComparer.Ordinal)
                .Count();
            if (exactSelections != 1)
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "A host package closure cannot select conflicting revisions of one package ID.",
                    "/hosts/hostPackages");
            }
        }
    }

    private void ValidateHealth(
        DotNetHealthConfiguration? health,
        ImmutableArray<DotNetOperationBinding> operations,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (health is null)
        {
            return;
        }

        RequireInitializedUnique(health.Listeners, static item => item.Identity.Value, "/hosts/health/listeners", diagnostics);
        RequireInitializedUnique(
            health.Endpoints,
            static item => string.Concat(item.ListenerIdentity.Value, ":", item.Path),
            "/hosts/health/endpoints",
            diagnostics);
        var listeners = health.Listeners.ToDictionary(static item => item.Identity.Value, StringComparer.Ordinal);
        foreach (var listener in health.Listeners)
        {
            var unsafeAddress = listener.Exposure != DotNetHealthExposure.Loopback ||
                                listener.Address is not ("127.0.0.1" or "::1" or "localhost");
            if (listener.Port is < 1 or > 65535)
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHealthConfiguration, "Health listener ports must be explicit values from 1 through 65535.", "/hosts/health/listeners/port");
            }

            if (unsafeAddress &&
                (listener.AuthenticationRevision is null ||
                 listener.TlsRevision is null ||
                 listener.HostFilterRevision is null))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHealthConfiguration, "Non-loopback health exposure requires authentication, TLS, and host-filter policy references.", "/hosts/health/listeners");
            }

            ValidateOptionalReference(
                listener.AuthenticationRevision,
                "/hosts/health/listeners/authenticationRevision",
                diagnostics);
            ValidateOptionalReference(
                listener.TlsRevision,
                "/hosts/health/listeners/tlsRevision",
                diagnostics);
            ValidateOptionalReference(
                listener.HostFilterRevision,
                "/hosts/health/listeners/hostFilterRevision",
                diagnostics);
        }

        var operationKeys = operations.IsDefault
            ? []
            : operations.Select(static operation => DotNetContractKeys.Exact(operation.OperationContract.OperationRevision)).ToHashSet(StringComparer.Ordinal);
        foreach (var endpoint in health.Endpoints)
        {
            ValidateReference(
                endpoint.ResponseProfileRevision,
                "/hosts/health/endpoints/responseProfileRevision",
                diagnostics);
            ValidateReference(
                endpoint.AuthorizationRevision,
                "/hosts/health/endpoints/authorizationRevision",
                diagnostics);
            if (!listeners.ContainsKey(endpoint.ListenerIdentity.Value))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHealthConfiguration, "A health endpoint must name a declared listener.", "/hosts/health/endpoints/listenerIdentity");
            }

            if (!endpoint.Path.StartsWith('/') ||
                endpoint.StatusCodes != new DotNetHealthStatusCodeMap(200, 200, 503) ||
                !string.Equals(endpoint.CachePolicy, "no-store", StringComparison.Ordinal))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHealthConfiguration, "Health endpoints require an absolute path, 200/200/503 status mapping, and no-store caching.", "/hosts/health/endpoints");
            }

            var documentation = endpoint.Documentation;
            if (documentation.Disposition == DotNetHealthDocumentationDisposition.Excluded &&
                documentation.OperationRevision is not null)
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHealthConfiguration, "Excluded health endpoints cannot carry an operation reference.", "/hosts/health/endpoints/documentation");
            }

            if (documentation.Disposition == DotNetHealthDocumentationDisposition.OwnedOperation &&
                (documentation.OperationRevision is null ||
                 !operationKeys.Contains(DotNetContractKeys.Exact(documentation.OperationRevision))))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidHealthConfiguration, "Documented health requires an exact owned host operation.", "/hosts/health/endpoints/documentation/operationRevision");
            }

            ValidateOptionalReference(
                documentation.OperationRevision,
                "/hosts/health/endpoints/documentation/operationRevision",
                diagnostics);
        }
    }

    private void ValidateSerialization(
        DotNetJsonSerializationSelection? selection,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (selection is null ||
            selection.Profiles.IsDefault ||
            selection.Contributions.IsDefault)
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "Serialization selections must be explicit initialized collections.", "/jsonSerialization");
            return;
        }

        foreach (var profile in selection.Profiles)
        {
            ValidateReference(
                new ArtifactReference(
                    profile.Identity,
                    profile.Version,
                    profile.Digest),
                "/jsonSerialization/profiles",
                diagnostics);
        }

        foreach (var contribution in selection.Contributions)
        {
            ValidateReference(
                new ArtifactReference(
                    contribution.Identity,
                    contribution.Version,
                    contribution.Digest),
                "/jsonSerialization/contributions",
                diagnostics);
        }
    }

    private void ValidateOperations(
        ImmutableArray<DotNetOperationBinding> operations,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        RequireInitializedUnique(
            operations,
            static operation =>
                DotNetContractKeys.Exact(operation.OperationContract.OperationRevision),
            "/hosts/operationBindings",
            diagnostics);
        foreach (var operation in operations)
        {
            var operationValidation =
                operationValidator.Validate(operation.OperationContract);
            diagnostics.AddRange(operationValidation.Diagnostics.Select(diagnostic =>
                diagnostic with
                {
                    Path = string.Concat(
                        "/hosts/operationBindings/operationContract",
                        diagnostic.Path.TrimStart('$')),
                }));
            ValidateReference(
                operation.ProjectionRevision,
                "/hosts/operationBindings/projectionRevision",
                diagnostics);
        }
    }

    private void ValidateConfiguration(
        ImmutableArray<DotNetConfigurationSource> sources,
        ImmutableArray<DotNetConfigurationBinding> bindings,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        RequireInitializedUnique(
            sources,
            static source => source.Identity.Value,
            "/hosts/configurationSources",
            diagnostics);
        var sourceIdentities = new HashSet<ProgramKitIdentifier>();
        if (!sources.IsDefault)
        {
            var filePaths = new HashSet<string>(StringComparer.Ordinal);
            for (var index = 0; index < sources.Length; index++)
            {
                var source = sources[index];
                sourceIdentities.Add(source.Identity);
                if (!ProgramKitIdentifier.Validate(source.Identity.Value).IsValid ||
                    !Enum.IsDefined(source.ProviderKind) ||
                    !Enum.IsDefined(source.StartupDisposition) ||
                    !Enum.IsDefined(source.SecretClassification) ||
                    !Enum.IsDefined(source.FailureDisposition) ||
                    !Enum.IsDefined(source.Reload.Capability))
                {
                    AddError(
                        diagnostics,
                        DotNetDiagnosticIds.InvalidShell,
                        "Configuration source identities and closed declarations must be valid.",
                        "/hosts/configurationSources");
                }

                if (source.Order != index)
                {
                    AddError(
                        diagnostics,
                        DotNetDiagnosticIds.InvalidShell,
                        "Configuration sources must be physically ordered with contiguous zero-based order values.",
                        "/hosts/configurationSources/order");
                }

                ValidateConfigurationSource(source, diagnostics);
                if (source.Path is not null &&
                    !filePaths.Add(source.Path))
                {
                    AddError(
                        diagnostics,
                        DotNetDiagnosticIds.InvalidShell,
                        "Configuration provider paths must be unique.",
                        "/hosts/configurationSources/path");
                }
                if (source.Path is not null &&
                    IsReservedConfigurationOutputPath(source.Path))
                {
                    AddError(
                        diagnostics,
                        DotNetDiagnosticIds.InvalidShell,
                        "Configuration provider paths cannot collide with generated configuration mechanics or ownership artifacts.",
                        "/hosts/configurationSources/path");
                }
            }
        }

        RequireInitializedUnique(
            bindings,
            static binding => string.Concat(
                binding.Definition.Identity.Value,
                "@",
                binding.Definition.Version.Value,
                "#",
                binding.OptionsName),
            "/hosts/configurationBindings",
            diagnostics);
        ValidateConfigurationDefinitionClaims(bindings, diagnostics);
        foreach (var binding in bindings)
        {
            ValidateConfigurationDefinition(binding.Definition, diagnostics);
            if (!Enum.IsDefined(binding.Consumption) ||
                !Enum.IsDefined(binding.ConsumerLifetime) ||
                !Enum.IsDefined(binding.ChangeReaction) ||
                (!string.IsNullOrEmpty(binding.OptionsName) &&
                 string.IsNullOrWhiteSpace(binding.OptionsName)))
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Options consumption, lifetime, reaction, and optional name must be valid.",
                    "/hosts/configurationBindings");
            }

            RequireInitializedUnique(
                binding.SourceIdentities,
                static identity => identity.Value,
                "/hosts/configurationBindings/sourceIdentities",
                diagnostics);
            if (binding.SourceIdentities.IsDefaultOrEmpty)
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Every Options binding requires at least one explicit source.",
                    "/hosts/configurationBindings/sourceIdentities");
            }
            if (binding.SourceIdentities.Any(identity => !sourceIdentities.Contains(identity)))
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Every Options binding source must identify a declared source.",
                    "/hosts/configurationBindings/sourceIdentities");
            }
            var selectedSources = sources.IsDefault
                ? []
                : sources
                    .Where(source =>
                        binding.SourceIdentities.Contains(source.Identity))
                    .ToArray();
            if (binding.Definition.Properties.Any(static property =>
                    property.Classification ==
                    DotNetConfigurationValueClassification.Sensitive) &&
                !selectedSources.Any(static source =>
                    source.SecretClassification ==
                    DotNetConfigurationSecretClassification.ProviderOwned))
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Sensitive values require an explicitly provider-owned secret source.",
                    "/hosts/configurationBindings/sourceIdentities");
            }

            if (binding.Definition.Properties.Any(static property =>
                    property.Classification ==
                    DotNetConfigurationValueClassification.SecretReference) &&
                !selectedSources.Any(static source =>
                    source.SecretClassification is
                        DotNetConfigurationSecretClassification.ReferencesOnly or
                        DotNetConfigurationSecretClassification.ProviderOwned))
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Secret-reference values require a reference-capable source.",
                    "/hosts/configurationBindings/sourceIdentities");
            }

            if ((binding.SecurityCritical ||
                 binding.Definition.Properties.Any(static property => property.Required)) &&
                !binding.ValidateOnStart)
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Required and security-critical Options must validate on startup.",
                    "/hosts/configurationBindings/validateOnStart");
            }

            if (binding.Consumption == DotNetOptionsConsumption.Snapshot &&
                binding.ConsumerLifetime == DotNetServiceLifetime.Singleton)
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "IOptionsSnapshot cannot be consumed by a singleton.",
                    "/hosts/configurationBindings/consumerLifetime");
            }

            if (binding.Consumption == DotNetOptionsConsumption.Monitor)
            {
                var monitoredSources = selectedSources;
                if (monitoredSources.Length == 0 ||
                    monitoredSources.Any(static source =>
                        !source.Reload.Enabled ||
                        source.Reload.Capability == DotNetConfigurationReloadCapability.None))
                {
                    AddError(
                        diagnostics,
                        DotNetDiagnosticIds.InvalidShell,
                        "IOptionsMonitor requires every selected source to expose an enabled change token or explicit refresh.",
                        "/hosts/configurationBindings/consumption");
                }

                if (binding.RestartRequired)
                {
                    AddError(
                        diagnostics,
                        DotNetDiagnosticIds.InvalidShell,
                        "Live Options monitoring cannot be combined with restart-required topology.",
                        "/hosts/configurationBindings/restartRequired");
                }
            }
            else if (binding.ChangeReaction != DotNetConfigurationChangeReaction.None)
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Configuration change reactions require monitored Options.",
                    "/hosts/configurationBindings/changeReaction");
            }
        }
    }

    private static void ValidateConfigurationDefinitionClaims(
        ImmutableArray<DotNetConfigurationBinding> bindings,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (bindings.IsDefaultOrEmpty)
        {
            return;
        }

        var definitionGroups = bindings
            .Select(static binding => binding.Definition)
            .GroupBy(
                static definition => string.Concat(
                    definition.Identity.Value,
                    "@",
                    definition.Version.Value),
                StringComparer.Ordinal)
            .ToArray();
        foreach (var group in definitionGroups)
        {
            var first = group.First();
            if (group.Skip(1).Any(definition =>
                    !ConfigurationDefinitionsMatch(first, definition)))
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "One configuration definition revision cannot carry conflicting owner-authored content.",
                    "/hosts/configurationBindings/definition");
            }
        }

        var definitions = definitionGroups
            .Select(static group => group.First())
            .ToArray();
        if (definitions
                .Select(static definition => string.Concat(
                    definition.Namespace,
                    ".",
                    definition.TypeName))
                .Distinct(StringComparer.Ordinal)
                .Count() != definitions.Length)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Distinct configuration definition revisions cannot generate the same C# type.",
                "/hosts/configurationBindings/definition/typeName");
        }

        if (definitions
                .Select(static definition => definition.Section)
                .Distinct(StringComparer.Ordinal)
                .Count() != definitions.Length)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Distinct configuration definition revisions cannot own the same generated section.",
                "/hosts/configurationBindings/definition/section");
        }
    }

    private static bool ConfigurationDefinitionsMatch(
        DotNetConfigurationDefinition left,
        DotNetConfigurationDefinition right) =>
        left.Identity == right.Identity &&
        left.Version == right.Version &&
        left.OwnerIdentity == right.OwnerIdentity &&
        left.OwnerKind == right.OwnerKind &&
        string.Equals(left.Namespace, right.Namespace, StringComparison.Ordinal) &&
        string.Equals(left.TypeName, right.TypeName, StringComparison.Ordinal) &&
        string.Equals(left.Section, right.Section, StringComparison.Ordinal) &&
        left.SchemaRevision == right.SchemaRevision &&
        ((left.Properties.IsDefault && right.Properties.IsDefault) ||
         (!left.Properties.IsDefault &&
          !right.Properties.IsDefault &&
          left.Properties.SequenceEqual(right.Properties))) &&
        CompatibilityMatches(left.Compatibility, right.Compatibility);

    private static bool CompatibilityMatches(
        ArtifactCompatibility left,
        ArtifactCompatibility right) =>
        left.Policy == right.Policy &&
        left.ReaderRange == right.ReaderRange &&
        left.WriterRange == right.WriterRange &&
        ((left.MigrationReferences.IsDefault &&
          right.MigrationReferences.IsDefault) ||
         (!left.MigrationReferences.IsDefault &&
          !right.MigrationReferences.IsDefault &&
          left.MigrationReferences.SequenceEqual(right.MigrationReferences))) &&
        ((left.Dimensions.IsDefault && right.Dimensions.IsDefault) ||
         (!left.Dimensions.IsDefault &&
          !right.Dimensions.IsDefault &&
          left.Dimensions.Length == right.Dimensions.Length &&
          left.Dimensions.Zip(right.Dimensions).All(static pair =>
              pair.First.Dimension == pair.Second.Dimension &&
              pair.First.Classification == pair.Second.Classification &&
              ((pair.First.Conditions.IsDefault &&
                pair.Second.Conditions.IsDefault) ||
               (!pair.First.Conditions.IsDefault &&
                !pair.Second.Conditions.IsDefault &&
                pair.First.Conditions.SequenceEqual(
                    pair.Second.Conditions,
                    StringComparer.Ordinal))))));

    private static bool IsReservedConfigurationOutputPath(string path) =>
        path.StartsWith(
            "ProgramKitGenerated/Configuration/",
            StringComparison.Ordinal) ||
        path.StartsWith(
            "configuration/generated/",
            StringComparison.Ordinal) ||
        path.StartsWith(
            "configuration/examples/",
            StringComparison.Ordinal) ||
        path.StartsWith(
            "configuration/developer/",
            StringComparison.Ordinal) ||
        path is
            "configuration/environment-map.json" or
            "configuration/key-per-file-map.json" or
            "configuration/provider-bindings.json" or
            "configuration/validation-report.json" or
            "configuration/provenance.json" or
            "configuration/ownership.json";

    private void ValidateConfigurationSource(
        DotNetConfigurationSource source,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        ValidateReference(
            source.ProviderRevision,
            "/hosts/configurationSources/providerRevision",
            diagnostics);
        ValidatePackage(
            source.Package,
            "/hosts/configurationSources/package",
            diagnostics);
        var expectedPackageId = source.ProviderKind switch
        {
            DotNetConfigurationProviderKind.JsonFile =>
                "Microsoft.Extensions.Configuration.Json",
            DotNetConfigurationProviderKind.EnvironmentVariables =>
                "Microsoft.Extensions.Configuration.EnvironmentVariables",
            DotNetConfigurationProviderKind.CommandLine =>
                "Microsoft.Extensions.Configuration.CommandLine",
            DotNetConfigurationProviderKind.KeyPerFile =>
                "Microsoft.Extensions.Configuration.KeyPerFile",
            _ => string.Empty,
        };
        if (source.Package is null ||
            !string.Equals(
                source.Package.PackageId,
                expectedPackageId,
                StringComparison.Ordinal) ||
            !string.Equals(
                source.Package.Version.Value,
                "10.0.10",
                StringComparison.Ordinal))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "The built-in configuration provider requires its exact pinned Microsoft.Extensions package.",
                "/hosts/configurationSources/package");
        }

        var pathRequired =
            source.ProviderKind is DotNetConfigurationProviderKind.JsonFile or
                DotNetConfigurationProviderKind.KeyPerFile;
        if (pathRequired == string.IsNullOrWhiteSpace(source.Path))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Only file-backed providers require an explicit path.",
                "/hosts/configurationSources/path");
        }
        else if (source.Path is not null &&
                 (System.IO.Path.IsPathRooted(source.Path) ||
                  source.Path.Replace('\\', '/')
                      .Split('/')
                      .Any(static segment => segment is "." or "..")))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Configuration provider paths must be normalized relative paths below the explicit output root.",
                "/hosts/configurationSources/path");
        }

        if (source.ProviderKind != DotNetConfigurationProviderKind.EnvironmentVariables &&
            source.Prefix is not null)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Only the environment-variable provider accepts a prefix.",
                "/hosts/configurationSources/prefix");
        }

        if (source.Optional !=
            (source.StartupDisposition == DotNetConfigurationStartupDisposition.Optional))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Provider optionality and startup disposition must agree.",
                "/hosts/configurationSources/startupDisposition");
        }

        if (source.FailureDisposition == DotNetConfigurationFailureDisposition.ContinueWithoutSource &&
            !source.Optional)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "A required source cannot continue after provider failure.",
                "/hosts/configurationSources/failureDisposition");
        }

        if (!source.Reload.Enabled &&
            source.Reload.Capability != DotNetConfigurationReloadCapability.None)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "A disabled reload declaration cannot claim a reload capability.",
                "/hosts/configurationSources/reload");
        }

        if (source.Reload.Enabled &&
            source.Reload.Capability == DotNetConfigurationReloadCapability.None)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Enabled reload requires a change token or explicit refresh.",
                "/hosts/configurationSources/reload");
        }

        if (source.ProviderKind != DotNetConfigurationProviderKind.JsonFile &&
            source.Reload.Capability == DotNetConfigurationReloadCapability.ChangeToken)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "The W020 built-in provider profile supports change-token reload only for JSON files.",
                "/hosts/configurationSources/reload/capability");
        }

        if (source.Reload.Capability == DotNetConfigurationReloadCapability.ExplicitRefresh)
        {
            ValidateReference(
                source.Reload.RefreshRevision,
                "/hosts/configurationSources/reload/refreshRevision",
                diagnostics);
            if (source.Reload.PollIntervalSeconds is <= 0)
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Explicit refresh requires a positive polling interval.",
                    "/hosts/configurationSources/reload/pollIntervalSeconds");
            }
        }
        else if (source.Reload.RefreshRevision is not null ||
                 source.Reload.PollIntervalSeconds is not null)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Refresh revision and polling are valid only for explicit refresh.",
                "/hosts/configurationSources/reload");
        }
    }

    private void ValidateConfigurationDefinition(
        DotNetConfigurationDefinition definition,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (definition is null)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "A typed configuration definition is required.",
                "/hosts/configurationBindings/definition");
            return;
        }

        if (!ProgramKitIdentifier.Validate(definition.Identity.Value).IsValid ||
            !SemanticVersion.Validate(definition.Version.Value).IsValid ||
            !ProgramKitIdentifier.Validate(definition.OwnerIdentity.Value).IsValid ||
            !IsNamespace(definition.Namespace) ||
            !IsIdentifier(definition.TypeName) ||
            string.IsNullOrWhiteSpace(definition.Section))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Configuration identity, owner, version, namespace, type, and section must be explicit and valid.",
                "/hosts/configurationBindings/definition");
        }
        else if (!Enum.IsDefined(definition.OwnerKind))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "The configuration definition owner kind is unsupported.",
                "/hosts/configurationBindings/definition/ownerKind");
        }

        ValidateReference(
            definition.SchemaRevision,
            "/hosts/configurationBindings/definition/schemaRevision",
            diagnostics);
        ValidateCompatibility(
            definition.Compatibility,
            "/hosts/configurationBindings/definition/compatibility",
            diagnostics);
        RequireInitializedUnique(
            definition.Properties,
            static property => property.PropertyName,
            "/hosts/configurationBindings/definition/properties",
            diagnostics);
        if (!definition.Properties.IsDefault &&
            definition.Properties.Select(static property => property.Key)
                .Distinct(StringComparer.Ordinal).Count() != definition.Properties.Length)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Configuration property keys must be unique.",
                "/hosts/configurationBindings/definition/properties/key");
        }

        foreach (var property in definition.Properties)
        {
            ValidateConfigurationProperty(property, diagnostics);
        }
    }

    private static void ValidateConfigurationProperty(
        DotNetConfigurationProperty property,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!IsIdentifier(property.PropertyName) ||
            string.IsNullOrWhiteSpace(property.Key) ||
            property.Key.Contains(':', StringComparison.Ordinal) ||
            !Enum.IsDefined(property.ValueKind) ||
            !Enum.IsDefined(property.Classification))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Configuration properties require a C# identifier and one section-relative key.",
                "/hosts/configurationBindings/definition/properties");
        }

        if (property.Classification != DotNetConfigurationValueClassification.Public &&
            (property.DefaultValue is not null || property.ExampleValue is not null))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Sensitive values and secret references cannot have generated defaults or examples.",
                "/hosts/configurationBindings/definition/properties/classification");
        }

        var validation = property.Validation;
        if ((property.DefaultValue is not null &&
             !IsScalarValue(property.ValueKind, property.DefaultValue)) ||
            (property.ExampleValue is not null &&
             !IsScalarValue(property.ValueKind, property.ExampleValue)))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Configuration defaults and examples must parse exactly as the declared scalar kind.",
                "/hosts/configurationBindings/definition/properties");
        }

        if (validation.MinimumLength is < 0 ||
            validation.MaximumLength is < 0 ||
            validation.MinimumLength > validation.MaximumLength)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "String length validation bounds are invalid.",
                "/hosts/configurationBindings/definition/properties/validation");
        }

        if (property.ValueKind != DotNetConfigurationValueKind.Text &&
            (validation.MinimumLength is not null ||
             validation.MaximumLength is not null ||
             validation.RegularExpression is not null))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Length and regular-expression rules apply only to string values.",
                "/hosts/configurationBindings/definition/properties/validation");
        }

        if (property.ValueKind is not (
                DotNetConfigurationValueKind.WholeNumber32 or
                DotNetConfigurationValueKind.WholeNumber64 or
                DotNetConfigurationValueKind.DecimalNumber or
                DotNetConfigurationValueKind.FloatingPoint) &&
            (validation.MinimumValue is not null ||
             validation.MaximumValue is not null))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Numeric bounds apply only to numeric values.",
                "/hosts/configurationBindings/definition/properties/validation");
        }

        if ((validation.MinimumValue is null) !=
            (validation.MaximumValue is null))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Numeric validation requires both minimum and maximum bounds.",
                "/hosts/configurationBindings/definition/properties/validation");
        }
        else if (validation.MinimumValue is not null &&
                 !AreNumericBoundsValid(
                     property.ValueKind,
                     validation.MinimumValue,
                     validation.MaximumValue!))
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Numeric validation bounds must be invariant numbers in ascending order.",
                "/hosts/configurationBindings/definition/properties/validation");
        }

        if (validation.RegularExpression is not null)
        {
            try
            {
                _ = new Regex(
                    validation.RegularExpression,
                    RegexOptions.CultureInvariant,
                    TimeSpan.FromSeconds(1));
            }
            catch (ArgumentException)
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "The configuration regular expression is invalid.",
                    "/hosts/configurationBindings/definition/properties/validation/regularExpression");
            }
        }
    }

    private static bool IsScalarValue(
        DotNetConfigurationValueKind kind,
        string value) =>
        kind switch
        {
            DotNetConfigurationValueKind.Text => true,
            DotNetConfigurationValueKind.Boolean =>
                bool.TryParse(value, out _),
            DotNetConfigurationValueKind.WholeNumber32 =>
                IsJsonNumber(value) &&
                int.TryParse(
                    value,
                    NumberStyles.AllowLeadingSign,
                    CultureInfo.InvariantCulture,
                    out _),
            DotNetConfigurationValueKind.WholeNumber64 =>
                IsJsonNumber(value) &&
                long.TryParse(
                    value,
                    NumberStyles.AllowLeadingSign,
                    CultureInfo.InvariantCulture,
                    out _),
            DotNetConfigurationValueKind.DecimalNumber =>
                IsJsonNumber(value) &&
                decimal.TryParse(
                    value,
                    NumberStyles.Float,
                    CultureInfo.InvariantCulture,
                    out _),
            DotNetConfigurationValueKind.FloatingPoint =>
                IsJsonNumber(value) &&
                double.TryParse(
                    value,
                    NumberStyles.Float,
                    CultureInfo.InvariantCulture,
                    out var parsed) &&
                double.IsFinite(parsed),
            DotNetConfigurationValueKind.AbsoluteUri =>
                Uri.TryCreate(value, UriKind.Absolute, out _),
            DotNetConfigurationValueKind.Duration =>
                TimeSpan.TryParse(
                    value,
                    CultureInfo.InvariantCulture,
                    out _),
            _ => false,
        };

    private static bool AreNumericBoundsValid(
        DotNetConfigurationValueKind kind,
        string minimum,
        string maximum)
    {
        if (!IsJsonNumber(minimum) || !IsJsonNumber(maximum))
        {
            return false;
        }

        return kind switch
        {
            DotNetConfigurationValueKind.WholeNumber32 =>
                int.TryParse(
                    minimum,
                    NumberStyles.AllowLeadingSign,
                    CultureInfo.InvariantCulture,
                    out var minimumInt32) &&
                int.TryParse(
                    maximum,
                    NumberStyles.AllowLeadingSign,
                    CultureInfo.InvariantCulture,
                    out var maximumInt32) &&
                minimumInt32 <= maximumInt32,
            DotNetConfigurationValueKind.WholeNumber64 =>
                long.TryParse(
                    minimum,
                    NumberStyles.AllowLeadingSign,
                    CultureInfo.InvariantCulture,
                    out var minimumInt64) &&
                long.TryParse(
                    maximum,
                    NumberStyles.AllowLeadingSign,
                    CultureInfo.InvariantCulture,
                    out var maximumInt64) &&
                minimumInt64 <= maximumInt64,
            DotNetConfigurationValueKind.DecimalNumber =>
                decimal.TryParse(
                    minimum,
                    NumberStyles.Float,
                    CultureInfo.InvariantCulture,
                    out var minimumDecimal) &&
                decimal.TryParse(
                    maximum,
                    NumberStyles.Float,
                    CultureInfo.InvariantCulture,
                    out var maximumDecimal) &&
                minimumDecimal <= maximumDecimal,
            DotNetConfigurationValueKind.FloatingPoint =>
                double.TryParse(
                    minimum,
                    NumberStyles.Float,
                    CultureInfo.InvariantCulture,
                    out var minimumDouble) &&
                double.IsFinite(minimumDouble) &&
                double.TryParse(
                    maximum,
                    NumberStyles.Float,
                    CultureInfo.InvariantCulture,
                    out var maximumDouble) &&
                double.IsFinite(maximumDouble) &&
                minimumDouble <= maximumDouble,
            _ => false,
        };
    }

    private static bool IsJsonNumber(string value) =>
        Regex.IsMatch(
            value,
            "^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$",
            RegexOptions.CultureInvariant,
            TimeSpan.FromSeconds(1));

    private static bool IsNamespace(string value) =>
        !string.IsNullOrWhiteSpace(value) &&
        value.Split('.').All(IsIdentifier);

    private static bool IsIdentifier(string value) =>
        !string.IsNullOrWhiteSpace(value) &&
        (char.IsLetter(value[0]) || value[0] == '_') &&
        value.Skip(1).All(static character =>
            char.IsLetterOrDigit(character) || character == '_');

    private void ValidateTaskRuntime(
        ImmutableArray<DotNetTaskRuntimeRequirement> requirements,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        RequireInitializedUnique(
            requirements,
            static requirement =>
                DotNetContractKeys.Exact(requirement.RuntimeRevision),
            "/hosts/taskRuntimeRequirements",
            diagnostics);
        foreach (var requirement in requirements)
        {
            ValidateReference(
                requirement.RuntimeRevision,
                "/hosts/taskRuntimeRequirements/runtimeRevision",
                diagnostics);
            ValidateReferenceSet(
                requirement.ScheduleProviderRevisions,
                "/hosts/taskRuntimeRequirements/scheduleProviderRevisions",
                diagnostics);
        }
    }

    private void ValidateCompatibility(
        ArtifactCompatibility? compatibility,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (compatibility is null ||
            !ProgramKitIdentifier.Validate(compatibility.Policy.Value).IsValid ||
            compatibility.Dimensions.IsDefault ||
            compatibility.MigrationReferences.IsDefault ||
            !SemanticVersionRange.Validate(compatibility.ReaderRange.Value).IsValid ||
            !SemanticVersionRange.Validate(compatibility.WriterRange.Value).IsValid)
        {
            AddError(
                diagnostics,
                DotNetDiagnosticIds.InvalidShell,
                "Compatibility policy, dimensions, ranges, and migrations must be explicit.",
                path);
            return;
        }

        RequireInitializedUnique(
            compatibility.Dimensions,
            static claim => claim.Dimension.ToString(),
            string.Concat(path, "/dimensions"),
            diagnostics);
        foreach (var claim in compatibility.Dimensions)
        {
            if (!Enum.IsDefined(claim.Dimension) ||
                !Enum.IsDefined(claim.Classification) ||
                claim.Conditions.IsDefault)
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Compatibility claims require defined dimensions, classifications, and initialized conditions.",
                    string.Concat(path, "/dimensions"));
            }
        }

        ValidateReferenceSet(
            compatibility.MigrationReferences,
            string.Concat(path, "/migrationReferences"),
            diagnostics);
    }

    private void ValidateReferenceSet(
        ImmutableArray<ArtifactReference> references,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        RequireInitializedUnique(
            references,
            DotNetContractKeys.Exact,
            path,
            diagnostics);
        foreach (var reference in references)
        {
            ValidateReference(reference, path, diagnostics);
        }
    }

    private void ValidateOptionalReference(
        ArtifactReference? reference,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (reference is not null)
        {
            ValidateReference(reference, path, diagnostics);
        }
    }

    private static void ValidatePackage(
        DotNetPackageReference package,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (package is null ||
            string.IsNullOrWhiteSpace(package.PackageId) ||
            !SemanticVersion.Validate(package.Version.Value).IsValid ||
            !Sha256Digest.Validate(package.Sha256.Value).IsValid)
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "An exact package ID, version, and SHA-256 are required.", path);
        }
    }

    private static void RequirePackage(
        Dictionary<string, DotNetPackageReference> packages,
        string packageId,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!packages.ContainsKey(packageId))
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, string.Concat("The host requires package '", packageId, "'."), "/hosts/hostPackages");
        }
    }

    private static void RequireInitializedUnique<T>(
        ImmutableArray<T> values,
        Func<T, string> key,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "The collection must be initialized.", path);
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var value in values)
        {
            if (value is null || !seen.Add(key(value)))
            {
                AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "The collection must contain unique non-null entries.", path);
            }
        }
    }

    private static void AddError(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string id,
        string message,
        string path) =>
        diagnostics.Add(new ProgramKitDiagnostic(id, ProgramKitDiagnosticSeverity.Error, message, path));
}
