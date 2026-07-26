using Azure.Security.KeyVault.Secrets;
using Orbyss.ProgramKit.AzureConfigurationConsumerFixture.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Configuration;

[TestClass]
public sealed class AzureKeyVaultPolicyTests
{
    [TestMethod]
    public void ActiveSecretPolicyExcludesDisabledExpiredAndPrematureSecrets()
    {
        var now = DateTimeOffset.UtcNow;
        ActiveSecretManager manager = new();

        Assert.IsTrue(manager.Load(new SecretProperties("current")
        {
            Enabled = true,
            NotBefore = now.AddMinutes(-5),
            ExpiresOn = now.AddMinutes(5),
        }));
        Assert.IsFalse(manager.Load(new SecretProperties("disabled")
        {
            Enabled = false,
        }));
        Assert.IsFalse(manager.Load(new SecretProperties("expired")
        {
            ExpiresOn = now.AddMinutes(-5),
        }));
        Assert.IsFalse(manager.Load(new SecretProperties("premature")
        {
            NotBefore = now.AddMinutes(5),
        }));
    }
}
