using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.DotNet.Composition.Converters;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Configuration.Azure;
using Orbyss.ProgramKit.DotNet.Health;
using Orbyss.ProgramKit.DotNet.Observability;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Operations.TransportFailures;
using Orbyss.ProgramKit.DotNet.Operations.Security;
using Orbyss.ProgramKit.Operations.Contracts;
using Orbyss.ProgramKit.Operations.Contracts.Transport;
using Orbyss.ProgramKit.SecretResolution.Contracts;
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
            new JsonProfileOwnedConverter(
                new SecretLifecycleDateTimeOffsetJsonConverter()),
            CreateEnumConverter<CompatibilityDimension>(),
            CreateEnumConverter<CompatibilityClassification>(),
            CreateEnumConverter<DotNetHostKind>(),
            CreateEnumConverter<DotNetHealthDocumentationDisposition>(),
            CreateEnumConverter<DotNetHealthExposure>(),
            CreateEnumConverter<DotNetHealthEndpointKind>(),
            CreateEnumConverter<DotNetConfigurationProviderKind>(),
            CreateEnumConverter<DotNetConfigurationReloadCapability>(),
            CreateEnumConverter<DotNetConfigurationReloadMechanism>(),
            CreateEnumConverter<DotNetConfigurationStartupDisposition>(),
            CreateEnumConverter<DotNetConfigurationSecretClassification>(),
            CreateEnumConverter<DotNetConfigurationFailureDisposition>(),
            CreateEnumConverter<DotNetConfigurationOwnerKind>(),
            CreateEnumConverter<DotNetConfigurationValueKind>(),
            CreateEnumConverter<DotNetConfigurationValueClassification>(),
            CreateEnumConverter<DotNetOptionsConsumption>(),
            CreateEnumConverter<DotNetServiceLifetime>(),
            CreateEnumConverter<DotNetConfigurationChangeReaction>(),
            CreateEnumConverter<DotNetAzureConfigurationProviderKind>(),
            CreateEnumConverter<DotNetLogLevel>(),
            CreateEnumConverter<DotNetActivityKind>(),
            CreateEnumConverter<DotNetMetricInstrumentKind>(),
            CreateEnumConverter<DotNetTelemetryInstrumentationKind>(),
            CreateEnumConverter<DotNetTelemetrySamplerKind>(),
            CreateEnumConverter<DotNetOtlpProtocol>(),
            CreateEnumConverter<DotNetTelemetryFailureDisposition>(),
            CreateEnumConverter<DotNetHandledExceptionDiagnostics>(),
            CreateEnumConverter<DotNetResponseStartedDisposition>(),
            CreateEnumConverter<DotNetClientDisconnectDisposition>(),
            CreateEnumConverter<TransportFailureDisclosure>(),
            CreateEnumConverter<DotNetTransportClaimMapping>(),
            CreateEnumConverter<DotNetOidcPushedAuthorizationBehavior>(),
            CreateEnumConverter<DotNetOidcClientAuthenticationMethod>(),
            CreateEnumConverter<DotNetCookieSameSite>(),
            CreateEnumConverter<DotNetJwtAccessTokenProfile>(),
            CreateEnumConverter<DotNetPolicyRegistrationOwnership>(),
            CreateEnumConverter<DotNetOperationSecurityDisposition>(),
            CreateEnumConverter<DotNetPublicBrowserTargetKind>(),
            CreateEnumConverter<DotNetPublicBrowserTokenStorage>(),
            CreateEnumConverter<DotNetPublicBrowserRefreshDisposition>(),
            CreateEnumConverter<DotNetBrowserEngine>(),
            CreateEnumConverter<DotNetOAuthClientAuthenticationMethod>(),
            CreateEnumConverter<DotNetOAuthTokenType>(),
            CreateEnumConverter<DotNetOAuthExchangeMode>(),
            CreateEnumConverter<OpenApiSecuritySchemeKind>(),
            CreateEnumConverter<ConsoleOptionKind>(),
            CreateEnumConverter<OperationResultDisposition>(),
            CreateEnumConverter<OperationExpectedRevisionPolicy>(),
            CreateEnumConverter<OperationIdempotencyPolicy>(),
            CreateEnumConverter<OperationCancellationPolicy>(),
            CreateEnumConverter<OperationProgressPolicy>(),
            CreateEnumConverter<SecretReferenceClassification>(),
            CreateEnumConverter<SecretResultKind>(),
            CreateEnumConverter<SecretResultLifetime>(),
            CreateEnumConverter<SecretRotationCapability>(),
            CreateEnumConverter<SecretConsumptionShape>(),
            CreateEnumConverter<SecretConsumerReaction>(),
            CreateEnumConverter<SecretResolutionStatus>(),
            CreateEnumConverter<SecretChangeKind>(),
            CreateEnumConverter<SecretReactionStatus>());
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
