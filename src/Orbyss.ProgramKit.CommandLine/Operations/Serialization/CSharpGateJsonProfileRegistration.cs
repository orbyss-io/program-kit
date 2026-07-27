using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization.Converters;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Closed registration for C# build-gate command documents.</summary>
public sealed class CSharpGateJsonProfileRegistration :
    ICSharpGateJsonProfileRegistration
{
    /// <inheritdoc />
    public void Register(IProgramKitJsonBuilder builder)
    {
        ArgumentNullException.ThrowIfNull(builder);
        builder.AddOwnedProfile(
            CommandLineJsonProfiles.CSharpBuildGates,
            new JsonProfileOwnedMechanics(
                CommandLineJsonProfiles.CSharpBuildGates.Reference,
                new ProgramKitIdentifier(
                    "pkid:package:program-kit:command-line"),
                CSharpGateJsonContext.Default,
                Model<CSharpBuildGateDefinitionDocument>(),
                Model<ConsumerAnalyzerScaffoldRequest>(),
                Model<CSharpGateBindRequest>(),
                Model<CSharpBuildGateSelectionLockDocument>(),
                Model<CSharpGateVerificationRequest>(),
                Model<CSharpGateCompilerHarnessResult>(),
                new JsonProfileOwnedConverter(
                    new CommandArtifactReferenceJsonConverter()),
                new JsonProfileOwnedConverter(
                    new CommandArtifactIntegrityJsonConverter()),
                new JsonProfileOwnedConverter(
                    new CommandRoundTripDateTimeOffsetJsonConverter()),
                Enum<CSharpAnalyzerArtifactKind>(),
                Enum<CSharpAnalyzerComponentKind>(),
                Enum<CSharpGateCommand>(),
                Enum<CSharpGateDiagnosticSeverity>(),
                Enum<CSharpGateEvidenceLayer>(),
                Enum<CSharpGateFixtureKind>(),
                Enum<CSharpGateImplementationBoundary>(),
                Enum<CSharpGateInputKind>(),
                Enum<CSharpGateRuleKind>(),
                Enum<CSharpGateRuleLayer>(),
                Enum<CSharpGateSuppressionDisposition>(),
                Enum<CSharpGateSuppressionMechanism>(),
                Enum<CSharpGateSuppressionTargetKind>(),
                Enum<CSharpGateTemporaryExceptionConditionKind>(),
                Enum<CSharpGateVerificationProfileKind>()));
    }

    private static JsonProfileOwnedConverter Enum<TEnum>()
        where TEnum : struct, Enum =>
        new(new CommandKebabCaseEnumJsonConverter<TEnum>());

    private static JsonProfileOwnedConverter Model<TModel>() =>
        new(new CommandCSharpGateModelJsonConverter<TModel>());
}
