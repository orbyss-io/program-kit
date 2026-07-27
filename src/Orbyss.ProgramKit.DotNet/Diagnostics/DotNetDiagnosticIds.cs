namespace Orbyss.ProgramKit.DotNet.Diagnostics;

/// <summary>Stable diagnostics emitted by the .NET Program Kit.</summary>
public static class DotNetDiagnosticIds
{
    /// <summary>The shell document is structurally or semantically invalid.</summary>
    public const string InvalidShell = "PKNET001";

    /// <summary>An exact artifact input is missing, stale, or unsafe.</summary>
    public const string InvalidArtifactInput = "PKNET002";

    /// <summary>A requested host is absent, ambiguous, or kind-incompatible.</summary>
    public const string InvalidHostSelection = "PKNET003";

    /// <summary>A generated host lock is incomplete or inconsistent.</summary>
    public const string InvalidHostLock = "PKNET004";

    /// <summary>Health exposure is unsafe or internally inconsistent.</summary>
    public const string InvalidHealthConfiguration = "PKNET005";

    /// <summary>An integrator document descriptor is inconsistent.</summary>
    public const string InvalidIntegratorDocument = "PKNET006";

    /// <summary>Generation could not produce the declared deterministic output.</summary>
    public const string GenerationFailed = "PKNET007";

    /// <summary>An exact configuration provider or generator is not registered.</summary>
    public const string UnknownConfigurationProvider = "PKNET008";

    /// <summary>A provider cannot satisfy the selected reload declaration.</summary>
    public const string UnsupportedProviderReload = "PKNET009";

    /// <summary>A provider package does not match the exact catalog closure.</summary>
    public const string ConfigurationProviderPackageMismatch = "PKNET010";

    /// <summary>Configuration provider selections duplicate or conflict.</summary>
    public const string ConfigurationProviderConflict = "PKNET011";

    /// <summary>Telemetry composition is unsafe, ambiguous, or unsupported.</summary>
    public const string InvalidTelemetryConfiguration = "PKNET012";

    /// <summary>A telemetry package does not match the exact reviewed selection.</summary>
    public const string TelemetryPackageMismatch = "PKNET013";

    /// <summary>Telemetry would duplicate framework instrumentation.</summary>
    public const string DuplicateTelemetryInstrumentation = "PKNET014";

    /// <summary>Telemetry could disclose sensitive or unbounded data.</summary>
    public const string UnsafeTelemetryData = "PKNET015";

    /// <summary>ASP.NET Core transport-failure composition is invalid.</summary>
    public const string InvalidTransportFailureConfiguration = "PKNET016";

    /// <summary>An exception mapping is ambiguous, inferred, or unsafe.</summary>
    public const string InvalidExceptionFailureMapping = "PKNET017";

    /// <summary>Transport failure detail could expose runtime material.</summary>
    public const string UnsafeTransportFailureDisclosure = "PKNET018";

    /// <summary>OpenAPI failure responses do not match runtime declarations.</summary>
    public const string TransportFailureOpenApiMismatch = "PKNET019";

    /// <summary>OIDC, OAuth, or host authorization composition is invalid.</summary>
    public const string InvalidSecurityConfiguration = "PKNET020";

    /// <summary>A security package does not match the exact reviewed selection.</summary>
    public const string SecurityPackageMismatch = "PKNET021";

    /// <summary>Runtime authorization and OpenAPI security declarations disagree.</summary>
    public const string SecurityOpenApiMismatch = "PKNET022";

    /// <summary>Security material would be persisted or disclosed unsafely.</summary>
    public const string UnsafeSecurityMaterial = "PKNET023";

    /// <summary>Azure configuration adapter composition is invalid or incomplete.</summary>
    public const string InvalidAzureConfiguration = "PKNET024";

    /// <summary>Azure credential, locator, or Key Vault reference handling is unsafe.</summary>
    public const string UnsafeAzureConfigurationMaterial = "PKNET025";

    /// <summary>Aspire application-composition input is invalid or incomplete.</summary>
    public const string InvalidAspireComposition = "PKNET026";

    /// <summary>An Aspire integration is absent, duplicated, or not exactly registered.</summary>
    public const string AspireIntegrationMismatch = "PKNET027";

    /// <summary>An Aspire resource relationship is missing, conflicting, or cyclic.</summary>
    public const string InvalidAspireRelationship = "PKNET028";

    /// <summary>An Aspire projection could disclose secret or classified locator material.</summary>
    public const string UnsafeAspireSecretMaterial = "PKNET029";

    /// <summary>Aspire output could not be produced deterministically.</summary>
    public const string AspireGenerationFailed = "PKNET030";

    /// <summary>The optional FastEndpoints projection selection is invalid.</summary>
    public const string InvalidFastEndpointsConfiguration = "PKNET031";

    /// <summary>The exact FastEndpoints adapter package selection is inconsistent.</summary>
    public const string FastEndpointsPackageMismatch = "PKNET032";

    /// <summary>FastEndpoints output differs from the canonical API projection.</summary>
    public const string FastEndpointsProjectionMismatch = "PKNET033";

    /// <summary>The optional Keycloak local-test fixture input is invalid.</summary>
    public const string InvalidKeycloakLocalFixture = "PKNET034";

    /// <summary>Keycloak fixture secret material is missing, unsafe, or disclosed.</summary>
    public const string UnsafeKeycloakFixtureMaterial = "PKNET035";

    /// <summary>The exact Keycloak image or Aspire integration selection differs.</summary>
    public const string KeycloakFixtureSelectionMismatch = "PKNET036";

    /// <summary>A requested protocol behavior is not in the reviewed provider subset.</summary>
    public const string UnsupportedKeycloakFixtureProfile = "PKNET037";

    /// <summary>The exact Open Console document revision is missing, stale, or mismatched.</summary>
    public const string InvalidOpenConsoleDocumentRevision = "PKNET038";
}
