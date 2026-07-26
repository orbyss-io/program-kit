using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.DotNet.Configuration.Azure;

/// <summary>Azure Key Vault provider-specific reload and value rules.</summary>
public sealed record DotNetAzureKeyVaultConfiguration(
    [property: JsonPropertyName("reloadIntervalSeconds")] int? ReloadIntervalSeconds,
    [property: JsonPropertyName("valueRotationReaction")] SecretConsumerReaction ValueRotationReaction,
    [property: JsonPropertyName("excludeExpiredOrNotYetValidSecrets")] bool ExcludeExpiredOrNotYetValidSecrets);
