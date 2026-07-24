using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization.Converters;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Default registration for the fixed local operations JSON profile.</summary>
public sealed class LocalOperationsJsonProfileRegistration :
    ILocalOperationsJsonProfileRegistration
{
    /// <inheritdoc />
    public void Register(IProgramKitJsonBuilder builder)
    {
        ArgumentNullException.ThrowIfNull(builder);
        builder.AddOwnedProfile(
            CommandLineJsonProfiles.LocalOperations,
            new JsonProfileOwnedMechanics(
                CommandLineJsonProfiles.LocalOperations.Reference,
                new ProgramKitIdentifier(
                    "pkid:package:program-kit:command-line"),
                LocalOperationsJsonContext.Default,
                new JsonProfileOwnedConverter(
                    new CommandArtifactReferenceJsonConverter()),
                new JsonProfileOwnedConverter(
                    new CommandArtifactIntegrityJsonConverter()),
                new JsonProfileOwnedConverter(
                    new CommandKebabCaseEnumJsonConverter<
                        CompatibilityDimension>()),
                new JsonProfileOwnedConverter(
                    new CommandKebabCaseEnumJsonConverter<
                        DependencyExposure>()),
                new JsonProfileOwnedConverter(
                    new CommandKebabCaseEnumJsonConverter<
                        VersionBoundaryKind>()),
                new JsonProfileOwnedConverter(
                    new CommandKebabCaseEnumJsonConverter<
                        VersionDependencyKind>())));
    }
}
