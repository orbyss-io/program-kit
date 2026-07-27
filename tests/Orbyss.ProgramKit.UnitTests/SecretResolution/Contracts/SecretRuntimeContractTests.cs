using Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

namespace Orbyss.ProgramKit.UnitTests.SecretResolution.Contracts;

[TestClass]
public sealed class SecretRuntimeContractTests
{
    [TestMethod]
    public void NativeResultCapabilitiesNeverCollapseToObjectOrString()
    {
        var runtimeTypes = new[]
        {
            typeof(IConfigurationTextSecretLease),
            typeof(IConfigurationBytesSecretLease),
            typeof(ICertificateSecretLease),
            typeof(IMountedFileSecretLease),
            typeof(ICredentialHandleSecretLease),
            typeof(IAssertionServiceSecretLease),
            typeof(IWorkloadIdentitySecretLease),
        };

        foreach (var runtimeType in runtimeTypes)
        {
            var exposedTypes = runtimeType
                .GetProperties()
                .Select(static property => property.PropertyType)
                .Concat(runtimeType.GetMethods().Select(static method =>
                    method.ReturnType))
                .ToArray();
            Assert.DoesNotContain(typeof(object), exposedTypes, runtimeType.Name);
            Assert.DoesNotContain(typeof(string), exposedTypes, runtimeType.Name);
        }
    }

    [TestMethod]
    public void MountedFileCapabilityDoesNotExposeCanonicalPath()
    {
        Assert.IsEmpty(typeof(ISecretMountedFileHandle).GetProperties());
        Assert.AreEqual(
            typeof(Stream),
            typeof(ISecretMountedFileHandle)
                .GetMethod(nameof(ISecretMountedFileHandle.OpenRead))!
                .ReturnType);
    }
}
