using System.Collections.Immutable;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

/// <summary>Supplies one converter factory with an exact target-family allow-list.</summary>
public sealed class JsonConverterFactoryContribution : JsonSerializationContribution
{
    /// <summary>Initializes one exact converter-factory contribution.</summary>
    public JsonConverterFactoryContribution(
        JsonSerializationContributionDescriptor descriptor,
        JsonConverterFactory factory,
        params Type[] targetTypeFamilies)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        ArgumentNullException.ThrowIfNull(factory);
        ArgumentNullException.ThrowIfNull(targetTypeFamilies);
        if (descriptor.Kind != JsonSerializationContributionKind.ConverterFactory ||
            targetTypeFamilies.Length == 0)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A converter factory must declare kind ConverterFactory and at least one exact target family.",
                "/descriptor");
        }

        RuntimeTargetTypes =
            JsonContributionTargetContract.ValidateRuntimeTargets(
                targetTypeFamilies,
                allowOpenGenericDefinitions: true,
                "/descriptor/targetTypeFamilies");
        JsonContributionTargetContract.EnsureDescriptorMatchesRuntimeTargets(
            descriptor,
            RuntimeTargetTypes,
            allowOpenGenericDefinitions: true);
        JsonContributionTargetContract.EnsureFactoryAcceptsClosedClaims(
            descriptor,
            factory,
            RuntimeTargetTypes);
        Descriptor = descriptor;
        Converter = factory;
    }

    /// <inheritdoc />
    public override JsonSerializationContributionDescriptor Descriptor { get; }

    /// <inheritdoc />
    public override JsonConverter Converter { get; }

    /// <inheritdoc />
    public override IJsonTypeInfoResolver? TypeInfoResolver => null;

    /// <inheritdoc />
    public override ImmutableArray<Type> RuntimeTargetTypes { get; }
}
