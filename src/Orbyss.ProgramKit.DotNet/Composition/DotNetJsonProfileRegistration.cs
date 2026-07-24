using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.DotNet.Composition.Converters;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Health;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.DotNet.Composition;

/// <summary>Default registration of fixed DotNet profile-owned mechanics.</summary>
public sealed class DotNetJsonProfileRegistration : IDotNetJsonProfileRegistration
{
    /// <inheritdoc />
    public void Register(IProgramKitJsonBuilder builder)
    {
        ArgumentNullException.ThrowIfNull(builder);
        var profile = DotNetJsonProfiles.ShellBootstrap;
        var mechanics = new JsonProfileOwnedMechanics(
            profile.Reference,
            new ProgramKitIdentifier("pkid:package:program-kit:dotnet"),
            DotNetShellJsonContext.Default,
            new JsonProfileOwnedConverter(
                new ArtifactReferenceJsonConverter()),
            new JsonProfileOwnedConverter(
                new CompatibilityClaimJsonConverter()),
            new JsonProfileOwnedConverter(
                new ArtifactCompatibilityJsonConverter()),
            new JsonProfileOwnedConverter(
                new JsonSerializationProfileRefJsonConverter()),
            new JsonProfileOwnedConverter(
                new JsonSerializationContributionRefJsonConverter()),
            CreateEnumConverter<CompatibilityDimension>(),
            CreateEnumConverter<CompatibilityClassification>(),
            CreateEnumConverter<DotNetHostKind>(),
            CreateEnumConverter<DotNetHealthDocumentationDisposition>(),
            CreateEnumConverter<DotNetHealthExposure>(),
            CreateEnumConverter<DotNetHealthEndpointKind>(),
            CreateEnumConverter<ConsoleOptionKind>());
        builder.AddOwnedProfile(profile, mechanics);
    }

    private static JsonProfileOwnedConverter CreateEnumConverter<TEnum>()
        where TEnum : struct, Enum =>
        new(
            new JsonStringEnumConverter<TEnum>(
                JsonNamingPolicy.KebabCaseLower,
                allowIntegerValues: false),
            typeof(TEnum));
}
