using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Metadata;

namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

internal static class JsonContributionTargetContract
{
    internal static Type? GetTypedConverterTarget(JsonConverter converter)
    {
        ArgumentNullException.ThrowIfNull(converter);
        for (var type = converter.GetType();
             type is not null;
             type = type.BaseType)
        {
            if (type.IsGenericType &&
                type.GetGenericTypeDefinition() == typeof(JsonConverter<>))
            {
                return type.GetGenericArguments()[0];
            }
        }

        return null;
    }

    internal static ImmutableArray<Type> GetSourceGeneratedContextTargets(
        JsonSerializerContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        var targets = context
            .GetType()
            .GetCustomAttributesData()
            .Where(static attribute =>
                attribute.AttributeType == typeof(JsonSerializableAttribute))
            .Select(static attribute =>
                attribute.ConstructorArguments.Count == 1 &&
                attribute.ConstructorArguments[0].Value is Type target
                    ? target
                    : throw ProgramKitJsonException.Create(
                        ProgramKitJsonDiagnosticIds.InvalidContribution,
                        "A JsonSerializable declaration did not expose one exact target type.",
                        "/descriptor/targetTypeFamilies"))
            .ToArray();
        if (targets.Length == 0)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A source-generated JSON context must declare at least one JsonSerializable target.",
                "/descriptor/targetTypeFamilies");
        }

        return ValidateRuntimeTargets(
            targets,
            allowOpenGenericDefinitions: false,
            "/descriptor/targetTypeFamilies");
    }

    internal static ImmutableArray<Type> ValidateRuntimeTargets(
        IEnumerable<Type> runtimeTargets,
        bool allowOpenGenericDefinitions,
        string path)
    {
        ArgumentNullException.ThrowIfNull(runtimeTargets);
        var targets = runtimeTargets.ToArray();
        if (targets.Length == 0)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "At least one runtime JSON target type is required.",
                path);
        }

        var seen = new HashSet<Type>();
        foreach (var target in targets)
        {
            if (target is null ||
                target == typeof(void) ||
                target.IsByRef ||
                target.IsPointer ||
                target.IsGenericParameter ||
                target.ContainsGenericParameters &&
                !(allowOpenGenericDefinitions && target.IsGenericTypeDefinition) ||
                !seen.Add(target))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.InvalidContribution,
                    "Runtime JSON targets must be unique exact closed types or explicitly allowed open generic definitions.",
                    path);
            }
        }

        return [.. targets];
    }

    internal static void EnsureDescriptorMatchesRuntimeTargets(
        JsonSerializationContributionDescriptor descriptor,
        ImmutableArray<Type> runtimeTargets,
        bool allowOpenGenericDefinitions)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        var validated = ValidateRuntimeTargets(
            runtimeTargets,
            allowOpenGenericDefinitions,
            "/descriptor/targetTypeFamilies");
        var identities = validated
            .Select(JsonTargetTypeIdentity.For)
            .ToImmutableArray();
        if (descriptor.TargetTypeFamilies.IsDefault ||
            !descriptor.TargetTypeFamilies.SequenceEqual(
                identities,
                StringComparer.Ordinal))
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "Declared target identities must exactly match the contribution's ordered runtime type claims.",
                "/descriptor/targetTypeFamilies");
        }
    }

    internal static void EnsureFactoryAcceptsClosedClaims(
        JsonSerializationContributionDescriptor descriptor,
        JsonConverterFactory factory,
        ImmutableArray<Type> runtimeTargets)
    {
        foreach (var target in runtimeTargets.Where(static type =>
                     !type.IsGenericTypeDefinition))
        {
            EnsureConverterAcceptsTarget(
                descriptor.Reference.Identity.Value,
                factory,
                target,
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "/descriptor/targetTypeFamilies");
        }
    }

    internal static void EnsureConverterAcceptsTarget(
        string ownerIdentity,
        JsonConverter converter,
        Type target,
        string diagnosticId,
        string path)
    {
        if (!DoesConverterAcceptTarget(
                ownerIdentity,
                converter,
                target,
                diagnosticId,
                path))
        {
            throw ProgramKitJsonException.Create(
                diagnosticId,
                $"JSON converter '{ownerIdentity}' does not accept declared target '{target.FullName}'.",
                path);
        }
    }

    internal static bool DoesConverterAcceptTarget(
        string ownerIdentity,
        JsonConverter converter,
        Type target,
        string diagnosticId,
        string path)
    {
        try
        {
            return converter.CanConvert(target);
        }
        catch (Exception exception) when (JsonExceptionBoundary.IsNonFatal(exception))
        {
            throw new ProgramKitJsonException(
                new ProgramKitDiagnostic(
                    diagnosticId,
                    ProgramKitDiagnosticSeverity.Error,
                    $"JSON converter '{ownerIdentity}' failed while validating target '{target.FullName}'.",
                    path),
                exception);
        }
    }

    internal static bool FactoryProvidesRuntimeTarget(
        string ownerIdentity,
        JsonConverterFactory factory,
        ImmutableArray<Type> claims,
        Type runtimeType,
        IDictionary<Type, bool> frozenAcceptance,
        string diagnosticId,
        string path)
    {
        if (!MatchesRuntimeTarget(runtimeType, claims))
        {
            return false;
        }

        if (frozenAcceptance.TryGetValue(runtimeType, out var accepted))
        {
            return accepted;
        }

        accepted = DoesConverterAcceptTarget(
            ownerIdentity,
            factory,
            runtimeType,
            diagnosticId,
            path);
        frozenAcceptance.Add(runtimeType, accepted);
        return accepted;
    }

    internal static bool MatchesRuntimeTarget(
        Type runtimeType,
        ImmutableArray<Type> claims) =>
        claims.Any(claim =>
            claim == runtimeType ||
            claim.IsGenericTypeDefinition &&
            runtimeType.IsConstructedGenericType &&
            runtimeType.GetGenericTypeDefinition() == claim);

    internal static bool ClaimsOverlap(
        ImmutableArray<Type> left,
        ImmutableArray<Type> right) =>
        left.Any(leftType => right.Any(rightType =>
            leftType == rightType ||
            leftType.IsGenericTypeDefinition &&
            rightType.IsConstructedGenericType &&
            rightType.GetGenericTypeDefinition() == leftType ||
            rightType.IsGenericTypeDefinition &&
            leftType.IsConstructedGenericType &&
            leftType.GetGenericTypeDefinition() == rightType));
}
