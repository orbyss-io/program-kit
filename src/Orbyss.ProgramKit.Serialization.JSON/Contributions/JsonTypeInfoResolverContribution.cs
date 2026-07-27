using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

/// <summary>Supplies one source-generated metadata context.</summary>
public sealed class JsonTypeInfoResolverContribution : JsonSerializationContribution
{
    /// <summary>Initializes one exact source-generated metadata contribution.</summary>
    public JsonTypeInfoResolverContribution(
        JsonSerializationContributionDescriptor descriptor,
        JsonSerializerContext context)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        ArgumentNullException.ThrowIfNull(context);
        if (descriptor.Kind != JsonSerializationContributionKind.TypeInfoResolver)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A metadata contribution must declare kind TypeInfoResolver.",
                "/descriptor/kind");
        }

        RuntimeTargetTypes =
            JsonContributionTargetContract.GetSourceGeneratedContextTargets(context);
        JsonContributionTargetContract.EnsureDescriptorMatchesRuntimeTargets(
            descriptor,
            RuntimeTargetTypes,
            allowOpenGenericDefinitions: false);
        Descriptor = descriptor;
        TypeInfoResolver = context;
    }

    /// <inheritdoc />
    public override JsonSerializationContributionDescriptor Descriptor { get; }

    /// <inheritdoc />
    public override JsonConverter? Converter => null;

    /// <inheritdoc />
    public override JsonSerializerContext TypeInfoResolver { get; }

    /// <inheritdoc />
    public override ImmutableArray<Type> RuntimeTargetTypes { get; }
}
