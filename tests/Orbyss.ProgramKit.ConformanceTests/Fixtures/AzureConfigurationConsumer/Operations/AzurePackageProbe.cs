namespace Orbyss.ProgramKit.AzureConfigurationConsumerFixture.Operations;

/// <summary>Forces the exact reviewed Azure package API surface into isolated compilation.</summary>
public static class AzurePackageProbe
{
    /// <summary>Returns the selected public provider and credential abstraction types.</summary>
    public static Type[] Types() =>
    [
        typeof(Azure.Core.TokenCredential),
        typeof(Azure.Extensions.AspNetCore.Configuration.Secrets.AzureKeyVaultConfigurationOptions),
    ];
}
