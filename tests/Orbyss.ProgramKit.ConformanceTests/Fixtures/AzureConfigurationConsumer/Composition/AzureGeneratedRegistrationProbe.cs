using Azure.Core;
using Azure.Extensions.AspNetCore.Configuration.Secrets;

namespace Orbyss.ProgramKit.AzureConfigurationConsumerFixture.Composition;

/// <summary>Isolated compilation of the exact APIs emitted by the adapter.</summary>
public static class AzureGeneratedRegistrationProbe
{
    /// <summary>Compiles the Key Vault registration emitted by Program Kit.</summary>
    public static void AddKeyVault(
        WebApplicationBuilder builder,
        TokenCredential credential)
    {
        AzureKeyVaultConfigurationExtensions.AddAzureKeyVault(
            builder.Configuration,
            new Uri("https://fixture.vault.azure.net/"),
            credential,
            new AzureKeyVaultConfigurationOptions
            {
                Manager = new ActiveSecretManager(),
                ReloadInterval = TimeSpan.FromMinutes(5),
            });
    }
}
