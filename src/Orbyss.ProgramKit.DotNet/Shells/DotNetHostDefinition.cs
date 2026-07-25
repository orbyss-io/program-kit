using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Health;
using Orbyss.ProgramKit.DotNet.Observability;
using Orbyss.ProgramKit.DotNet.Operations;
using Orbyss.ProgramKit.DotNet.Packages;
using Orbyss.ProgramKit.DotNet.Operations.TransportFailures;

namespace Orbyss.ProgramKit.DotNet.Shells;

/// <summary>Complete reviewed generation intent for one exact host.</summary>
public sealed record DotNetHostDefinition(
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("kind")] DotNetHostKind Kind,
    [property: JsonPropertyName("dotNetTargetProfileRevision")] ArtifactReference DotNetTargetProfileRevision,
    [property: JsonPropertyName("generatorProfileRevision")] ArtifactReference GeneratorProfileRevision,
    [property: JsonPropertyName("shellIdentities")] ImmutableArray<ProgramKitIdentifier> ShellIdentities,
    [property: JsonPropertyName("featureActivationIdentities")] ImmutableArray<ProgramKitIdentifier> FeatureActivationIdentities,
    [property: JsonPropertyName("hostPackages")] ImmutableArray<DotNetPackageReference> HostPackages,
    [property: JsonPropertyName("operationBindings")] ImmutableArray<DotNetOperationBinding> OperationBindings,
    [property: JsonPropertyName("configurationSources")] ImmutableArray<DotNetConfigurationSource> ConfigurationSources,
    [property: JsonPropertyName("configurationBindings")] ImmutableArray<DotNetConfigurationBinding> ConfigurationBindings,
    [property: JsonPropertyName("taskRuntimeRequirements")] ImmutableArray<DotNetTaskRuntimeRequirement> TaskRuntimeRequirements,
    [property: JsonPropertyName("health")] DotNetHealthConfiguration? Health,
    [property: JsonPropertyName("compatibility")] ArtifactCompatibility Compatibility,
    [property: JsonPropertyName("telemetry")] DotNetTelemetryConfiguration? Telemetry = null,
    [property: JsonPropertyName("transportFailures")] DotNetTransportFailureConfiguration? TransportFailures = null);
