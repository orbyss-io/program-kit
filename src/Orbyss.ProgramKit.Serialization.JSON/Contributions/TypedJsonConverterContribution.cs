using System.Collections.Immutable;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Metadata;

namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

/// <summary>Supplies one stable typed converter contribution.</summary>
public sealed class TypedJsonConverterContribution<T> : JsonSerializationContribution
{
    /// <summary>Initializes one exact typed converter contribution.</summary>
    public TypedJsonConverterContribution(
        JsonSerializationContributionDescriptor descriptor,
        JsonConverter<T> converter)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        ArgumentNullException.ThrowIfNull(converter);
        if (descriptor.Kind != JsonSerializationContributionKind.TypedConverter)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A typed converter contribution must declare kind TypedConverter.",
                "/descriptor/kind");
        }

        var target = JsonTargetTypeIdentity.For<T>();
        if (descriptor.TargetTypeFamilies.Length != 1 ||
            !string.Equals(descriptor.TargetTypeFamilies[0], target, StringComparison.Ordinal))
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                $"A typed converter must claim only its exact target '{target}'.",
                "/descriptor/targetTypeFamilies");
        }

        RuntimeTargetTypes = [typeof(T)];
        JsonContributionTargetContract.EnsureDescriptorMatchesRuntimeTargets(
            descriptor,
            RuntimeTargetTypes,
            allowOpenGenericDefinitions: false);
        JsonContributionTargetContract.EnsureConverterAcceptsTarget(
            descriptor.Reference.Identity.Value,
            converter,
            typeof(T),
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            "/descriptor/targetTypeFamilies");
        Descriptor = descriptor;
        Converter = converter;
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
