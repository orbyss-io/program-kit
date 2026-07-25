using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Targeting;
using Orbyss.ProgramKit.DotNet.Validation;

namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>Default deterministic host-lock builder.</summary>
public sealed class DotNetShellLockBuilder : IDotNetShellLockBuilder
{
    private readonly IDotNetShellValidator shellValidator;

    /// <summary>Initializes the builder with shell validation behavior.</summary>
    public DotNetShellLockBuilder(IDotNetShellValidator shellValidator)
    {
        this.shellValidator = shellValidator ??
            throw new ArgumentNullException(nameof(shellValidator));
    }

    /// <inheritdoc />
    public DotNetShellLockDocument Build(
        DotNetShellDocument shell,
        ArtifactReference shellRevision)
    {
        ArgumentNullException.ThrowIfNull(shell);
        ArgumentNullException.ThrowIfNull(shellRevision);
        var validation = shellValidator.Validate(shell);
        if (!validation.IsValid)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidShell,
                "A host lock cannot be built from an invalid shell.",
                string.Empty);
        }

        var hosts = shell.Hosts
            .OrderBy(static host => host.Identity.Value, StringComparer.Ordinal)
            .Select(host => BuildHost(shell, host))
            .ToImmutableArray();
        return new DotNetShellLockDocument(
            "pkid:schema:program-kit:dotnet-shell-lock@1.0.0",
            new SemanticVersion("1.0.0"),
            shellRevision,
            shell.InputVersionMapRevision,
            shell.InputVersionSelectionRevision,
            hosts);
    }

    private static DotNetHostLock BuildHost(
        DotNetShellDocument shell,
        DotNetHostDefinition host)
    {
        var selectedActivations = host.FeatureActivationIdentities.ToHashSet();
        var packages = host.HostPackages
            .Concat(
                host.ConfigurationSources
                    .Select(static source => source.Package))
            .Concat(host.Telemetry?.Packages ?? [])
            .Concat(
                shell.Features
                    .Where(feature => selectedActivations.Contains(feature.ActivationIdentity))
                    .Select(static feature => feature.Package))
            .DistinctBy(
                static package => package.PackageId,
                StringComparer.Ordinal)
            .OrderBy(static package => package.PackageId, StringComparer.Ordinal)
            .Select(static package => new DotNetPackageLock(
                package.PackageId,
                package.Version,
                package.Sha256))
            .ToImmutableArray();
        var packageDigest = HashPackages(packages);
        var contracts = host.OperationBindings
            .SelectMany(static operation =>
                operation.GetInputSchemaRevisions()
                    .AddRange(operation.GetResultSchemaRevisions())
                    .AddRange(operation.GetDiagnosticSchemaRevisions())
                    .AddRange(operation.GetRelatedOperationRevisions())
                    .Add(operation.OperationContract.OperationRevision))
            .Concat(
                host.ConfigurationSources.SelectMany(static source =>
                    source.Reload.RefreshRevision is null
                        ? [source.ProviderRevision]
                        : new[]
                        {
                            source.ProviderRevision,
                            source.Reload.RefreshRevision,
                        }))
            .Concat(
                host.ConfigurationBindings.Select(static binding =>
                    binding.Definition.SchemaRevision))
            .Concat(
                host.TaskRuntimeRequirements.SelectMany(static requirement =>
                    requirement.ScheduleProviderRevisions.Add(requirement.RuntimeRevision)))
            .Concat(host.Telemetry is null
                ? []
                :
                [
                    host.Telemetry.ProfileRevision,
                    host.Telemetry.SpecificationRevision,
                    host.Telemetry.SemanticConventionRevision,
                ])
            .DistinctBy(static reference => string.Concat(reference.Identity.Value, "@", reference.Version.Value, "#", reference.Digest.Value))
            .OrderBy(static reference => reference.Identity.Value, StringComparer.Ordinal)
            .ThenBy(static reference => reference.Version.Value, StringComparer.Ordinal)
            .ToImmutableArray();
        var generators = host.OperationBindings
            .Select(static operation => operation.ProjectionRevision)
            .Append(host.GeneratorProfileRevision)
            .DistinctBy(static reference => string.Concat(reference.Identity.Value, "@", reference.Version.Value, "#", reference.Digest.Value))
            .OrderBy(static reference => reference.Identity.Value, StringComparer.Ordinal)
            .ToImmutableArray();
        var serialization = shell.JsonSerialization.Profiles
            .Select(static profile => new ArtifactReference(profile.Identity, profile.Version, profile.Digest))
            .Concat(
                shell.JsonSerialization.Contributions.Select(static contribution =>
                    new ArtifactReference(
                        contribution.Identity,
                        contribution.Version,
                        contribution.Digest)))
            .OrderBy(static reference => reference.Identity.Value, StringComparer.Ordinal)
            .ToImmutableArray();

        return new DotNetHostLock(
            host.Identity,
            host.Version,
            host.Kind,
            new DotNetTargetLock(
                host.DotNetTargetProfileRevision,
                "10.0.302",
                "net10.0",
                "14.0",
                "disable",
                false),
            shell.Composition.AbiVersion,
            host.FeatureActivationIdentities.OrderBy(static item => item.Value, StringComparer.Ordinal).ToImmutableArray(),
            contracts,
            contracts.Where(static reference => reference.Identity.Kind == "schema").ToImmutableArray(),
            generators,
            serialization,
            shell.InputVersionMapRevision,
            shell.InputVersionSelectionRevision,
            packages,
            packageDigest);
    }

    private static Sha256Digest HashPackages(ImmutableArray<DotNetPackageLock> packages)
    {
        var text = string.Join(
            "\n",
            packages.Select(static package =>
                string.Concat(
                    package.PackageId,
                    "@",
                    package.Version.Value,
                    "#",
                    package.PackageDigest.Value)));
        var digest = Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(text)));
        return new Sha256Digest(string.Concat("sha256:", digest));
    }
}
