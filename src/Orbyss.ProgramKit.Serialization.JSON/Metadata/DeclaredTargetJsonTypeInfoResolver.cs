using System.Collections.Immutable;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Metadata;

internal sealed class DeclaredTargetJsonTypeInfoResolver : IJsonTypeInfoResolver
{
    private readonly JsonSerializerContext context;
    private readonly ImmutableArray<Type> runtimeTargets;
    private readonly string ownerIdentity;
    private readonly ImmutableDictionary<Type, JsonSerializerContext>
        selectedResolverByRootType;

    internal DeclaredTargetJsonTypeInfoResolver(
        JsonSerializerContext context,
        ImmutableArray<Type> runtimeTargets,
        string ownerIdentity,
        ImmutableDictionary<Type, JsonSerializerContext>
            selectedResolverByRootType)
    {
        this.context = context;
        this.runtimeTargets = runtimeTargets;
        this.ownerIdentity = ownerIdentity;
        this.selectedResolverByRootType = selectedResolverByRootType;
    }

    public JsonTypeInfo? GetTypeInfo(Type type, JsonSerializerOptions options)
    {
        if (selectedResolverByRootType.TryGetValue(
                type,
                out var selectedResolver) &&
            !ReferenceEquals(selectedResolver, context))
        {
            return null;
        }

        try
        {
            var typeInfo =
                ((IJsonTypeInfoResolver)context).GetTypeInfo(type, options);
            if (typeInfo is null &&
                JsonContributionTargetContract.MatchesRuntimeTarget(
                    type,
                    runtimeTargets))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.TypeMetadataUnavailable,
                    $"Declared source-generated metadata '{ownerIdentity}' returned no metadata for '{type.FullName}'.");
            }

            if (typeInfo is not null &&
                !ReferenceEquals(typeInfo.OriginatingResolver, context))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.TypeMetadataUnavailable,
                    $"Declared source-generated metadata '{ownerIdentity}' returned metadata not originated by its contributed context for '{type.FullName}'.",
                    "/targetTypeFamilies");
            }

            return typeInfo;
        }
        catch (ProgramKitJsonException)
        {
            throw;
        }
        catch (Exception exception) when (JsonExceptionBoundary.IsNonFatal(exception))
        {
            throw new ProgramKitJsonException(
                new ProgramKitDiagnostic(
                    ProgramKitJsonDiagnosticIds.TypeMetadataUnavailable,
                    ProgramKitDiagnosticSeverity.Error,
                    $"Declared source-generated metadata '{ownerIdentity}' failed for '{type.FullName}'.",
                    "/targetTypeFamilies"),
                exception);
        }
    }
}
