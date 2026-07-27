using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Metadata;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Binds one profile-owned converter to exact runtime target claims.</summary>
public sealed class JsonProfileOwnedConverter
{
    /// <summary>Initializes one exact profile-owned converter registration.</summary>
    public JsonProfileOwnedConverter(
        JsonConverter converter,
        params Type[] runtimeTargetTypes)
    {
        ArgumentNullException.ThrowIfNull(converter);
        ArgumentNullException.ThrowIfNull(runtimeTargetTypes);
        if (converter is JsonConverterFactory factory)
        {
            RuntimeTargetTypes = JsonContributionTargetContract.ValidateRuntimeTargets(
                runtimeTargetTypes,
                allowOpenGenericDefinitions: true,
                "/profileOwnedMechanics/converters/targetTypeFamilies");
            foreach (var target in RuntimeTargetTypes.Where(static target =>
                         !target.IsGenericTypeDefinition))
            {
                JsonContributionTargetContract.EnsureConverterAcceptsTarget(
                    "profile-owned",
                    factory,
                    target,
                    ProgramKitJsonDiagnosticIds.InvalidProfile,
                    "/profileOwnedMechanics/converters/targetTypeFamilies");
            }
        }
        else
        {
            var inferredTarget =
                JsonContributionTargetContract.GetTypedConverterTarget(converter)
                ?? throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.InvalidProfile,
                    "A profile-owned converter must derive from JsonConverter<T> or JsonConverterFactory.",
                    "/profileOwnedMechanics/converters");
            var suppliedTargets = runtimeTargetTypes.Length == 0
                ? [inferredTarget]
                : runtimeTargetTypes;
            RuntimeTargetTypes = JsonContributionTargetContract.ValidateRuntimeTargets(
                suppliedTargets,
                allowOpenGenericDefinitions: false,
                "/profileOwnedMechanics/converters/targetTypeFamilies");
            if (RuntimeTargetTypes.Length != 1 ||
                RuntimeTargetTypes[0] != inferredTarget)
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.InvalidProfile,
                    $"A typed profile-owned converter must claim only '{JsonTargetTypeIdentity.For(inferredTarget)}'.",
                    "/profileOwnedMechanics/converters/targetTypeFamilies");
            }

            JsonContributionTargetContract.EnsureConverterAcceptsTarget(
                "profile-owned",
                converter,
                inferredTarget,
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "/profileOwnedMechanics/converters/targetTypeFamilies");
        }

        Converter = converter;
        TargetTypeIdentities = RuntimeTargetTypes
            .Select(JsonTargetTypeIdentity.For)
            .ToImmutableArray();
    }

    /// <summary>Gets the owned converter or factory.</summary>
    public JsonConverter Converter { get; }

    /// <summary>Gets exact runtime target claims.</summary>
    public ImmutableArray<Type> RuntimeTargetTypes { get; }

    /// <summary>Gets stable ordered target identities.</summary>
    public ImmutableArray<string> TargetTypeIdentities { get; }
}
