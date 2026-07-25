using System.Text;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.TestSupport.SecretResolution;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Composition;

[TestClass]
public sealed class SecretResolutionJsonProfileTests
{
    [TestMethod]
    public void FixedDotNetProfileRoundTripsSecretContractWithoutReflectionFallback()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder builder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(builder);
        ProgramKitJsonCanonicalizer canonicalizer = new();
        ProgramKitJsonSerializer serializer =
            new(builder.Freeze(), canonicalizer);
        var contract = SecretResolutionTestContractFactory.Contract();

        var canonical = serializer.Write(
            contract,
            DotNetJsonProfiles.ShellBootstrap.Reference,
            DotNetJsonProfiles.ShellBootstrap.MaximumLimits);
        var roundTrip = serializer.Read<SecretResolutionContract>(
            canonical.ToArray(),
            DotNetJsonProfiles.ShellBootstrap.Reference,
            DotNetJsonProfiles.ShellBootstrap.MaximumLimits);
        var json = Encoding.UTF8.GetString(canonical.ToArray());

        Assert.AreEqual(contract.Reference.Identity, roundTrip.Reference.Identity);
        Assert.AreEqual(
            contract.Reference.ExpectedResultKind,
            roundTrip.Reference.ExpectedResultKind);
        Assert.Contains("\"expectedResultKind\":\"configuration-text\"", json);
        Assert.DoesNotContain("secretValue", json);
        Assert.DoesNotContain("JsonElement", json);
    }
}
