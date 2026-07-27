using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.DotNet.Configuration.Azure;

/// <summary>
/// One exact source-to-Azure-adapter binding. Endpoints and classified
/// references are intent; credential or secret material is never accepted.
/// </summary>
public sealed record DotNetAzureConfigurationBinding(
    [property: JsonPropertyName("sourceIdentity")] ProgramKitIdentifier SourceIdentity,
    [property: JsonPropertyName("providerKind")] DotNetAzureConfigurationProviderKind ProviderKind,
    [property: JsonPropertyName("endpoint")] Uri Endpoint,
    [property: JsonPropertyName("credentialResolution")] SecretResolutionContract CredentialResolution,
    [property: JsonPropertyName("credentialResolutionTimeoutSeconds")] int CredentialResolutionTimeoutSeconds,
    [property: JsonPropertyName("keyVault")] DotNetAzureKeyVaultConfiguration? KeyVault,
    [property: JsonPropertyName("redactOperationalMetadata")] bool RedactOperationalMetadata);
