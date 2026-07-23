using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.TestSupport;

internal static class JsonContributionTestFactory
{
    internal static JsonTypeInfoResolverContribution CreateResolverContribution(
        string name,
        string digestMarker,
        Type? targetType = null,
        ImmutableArray<ProgramKitIdentifier> before = default,
        ImmutableArray<ProgramKitIdentifier> after = default)
    {
        targetType ??= typeof(ProbeModel);
        JsonSerializerContext context = targetType == typeof(ProbeModel)
            ? ProbeJsonTestContext.Default
            : targetType == typeof(FactoryModel)
                ? FactoryJsonTestContext.Default
                : throw new ArgumentOutOfRangeException(
                    nameof(targetType),
                    targetType,
                    "No test source-generation context owns this target.");
        return new JsonTypeInfoResolverContribution(
            CreateDescriptor(
                name,
                digestMarker,
                JsonSerializationContributionKind.TypeInfoResolver,
                JsonTargetTypeClaim.For(targetType),
                before,
                after),
            context);
    }

    internal static JsonSerializationContributionDescriptor CreateDescriptor(
        string name,
        string digestMarker,
        JsonSerializationContributionKind kind,
        string target,
        ImmutableArray<ProgramKitIdentifier> before = default,
        ImmutableArray<ProgramKitIdentifier> after = default,
        JsonSerializationProfileRef? applicableProfile = null) =>
        new(
            new JsonSerializationContributionRef(
                new ProgramKitIdentifier(
                    string.Concat(
                        "pkid:json-contribution:tests:",
                        name)),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    string.Concat(
                        "sha256:",
                        digestMarker.PadLeft(64, '0')))),
            new ProgramKitIdentifier(
                "pkid:package:tests:serialization-fixtures"),
            (applicableProfile ??
                ProgramKitJsonProfiles.JsonContracts.Reference).Identity,
            new SemanticVersionRange("[1.0.0]"),
            kind,
            [target],
            before.IsDefault ? [] : before,
            after.IsDefault ? [] : after);
}
