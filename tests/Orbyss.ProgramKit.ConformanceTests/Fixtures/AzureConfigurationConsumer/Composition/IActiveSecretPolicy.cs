using Azure.Security.KeyVault.Secrets;

namespace Orbyss.ProgramKit.AzureConfigurationConsumerFixture.Composition;

/// <summary>Behavior contract implemented by the generated active-secret manager.</summary>
public interface IActiveSecretPolicy
{
    /// <summary>Maps one loaded secret to its configuration key.</summary>
    string GetKey(KeyVaultSecret secret);

    /// <summary>Maps loaded secrets to configuration data.</summary>
    Dictionary<string, string?> GetData(IEnumerable<KeyVaultSecret> secrets);

    /// <summary>Returns whether one Key Vault secret may enter configuration.</summary>
    bool Load(SecretProperties secret);
}
