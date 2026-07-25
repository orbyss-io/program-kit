using Orbyss.ProgramKit.DotNet.Configuration;
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

        if (!string.Equals(value.Schema, "pkid:schema:program-kit:dotnet-shell@2.0.0", StringComparison.Ordinal))
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "The exact DotNet shell schema is required.", "/$schema");
        }

        if (value.Version.Value != "2.0.0")
        {
            AddError(diagnostics, DotNetDiagnosticIds.InvalidShell, "The shell document version must be 2.0.0.", "/version");
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
            ValidateConfiguration(host.ConfigurationBindings, diagnostics);
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
        ImmutableArray<DotNetConfigurationBinding> bindings,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        RequireInitializedUnique(
            bindings,
            static binding => binding.Section,
            "/hosts/configurationBindings",
            diagnostics);
        foreach (var binding in bindings)
        {
            if (string.IsNullOrWhiteSpace(binding.Section))
            {
                AddError(
                    diagnostics,
                    DotNetDiagnosticIds.InvalidShell,
                    "Configuration sections must be explicit.",
                    "/hosts/configurationBindings/section");
            }

            ValidateReference(
                binding.SchemaRevision,
                "/hosts/configurationBindings/schemaRevision",
                diagnostics);
        }
    }

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
