using Azure.Extensions.AspNetCore.Configuration.Secrets;
using Azure.Security.KeyVault.Secrets;

namespace Orbyss.ProgramKit.AzureConfigurationConsumerFixture.Composition;

/// <summary>Excludes disabled, expired, and not-yet-valid Key Vault secrets.</summary>
public sealed class ActiveSecretManager :
    KeyVaultSecretManager,
    IActiveSecretPolicy
{
    /// <inheritdoc />
    public override bool Load(SecretProperties secret)
    {
        var now = DateTimeOffset.UtcNow;
        return secret.Enabled is not false &&
               (secret.NotBefore is null ||
                secret.NotBefore <= now) &&
               (secret.ExpiresOn is null ||
                secret.ExpiresOn > now);
    }
}
