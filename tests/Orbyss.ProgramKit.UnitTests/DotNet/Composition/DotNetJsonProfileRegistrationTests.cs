using System.Text;
using System.Security.Cryptography;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Composition;

[TestClass]
public sealed class DotNetJsonProfileRegistrationTests
{
    [TestMethod]
    public void FixedProfileWritesAndReadsTypedShellWithoutReflectionFallback()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder builder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(builder);
        var registry = builder.Freeze();
        ProgramKitJsonCanonicalizer canonicalizer = new();
        ProgramKitJsonSerializer serializer = new(registry, canonicalizer);
        var shell = DotNetTestContractFactory.Shell();

        var canonical = serializer.Write(
            shell,
            DotNetJsonProfiles.ShellBootstrap.Reference,
            DotNetJsonProfiles.ShellBootstrap.MaximumLimits);
        var roundTrip = serializer.Read<DotNetShellDocument>(
            canonical.ToArray(),
            DotNetJsonProfiles.ShellBootstrap.Reference,
            DotNetJsonProfiles.ShellBootstrap.MaximumLimits);

        Assert.AreEqual(shell.Version, roundTrip.Version);
        Assert.AreEqual(shell.Composition.Provider, roundTrip.Composition.Provider);
        Assert.HasCount(3, roundTrip.Hosts);
        var json = Encoding.UTF8.GetString(canonical.ToArray());
        Assert.Contains("\"inputVersionMapRevision\"", json);
        Assert.Contains("\"operationRevision\"", json);
        Assert.DoesNotContain("\"InputVersionMapRevision\"", json);
        Assert.DoesNotContain("JsonElement", json);
    }

    [TestMethod]
    public void FixedProfileDigestBindsItsPackagedMechanicsDescriptor()
    {
        var assembly = typeof(DotNetJsonProfiles).Assembly;
        var resource = assembly.GetManifestResourceNames().Single(name =>
            name.EndsWith(
                "json-dotnet-shell-1.0.0.json",
                StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resource) ??
            throw new InvalidOperationException(
                "The shell bootstrap profile descriptor is missing.");
        var digest = string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(stream)));

        Assert.AreEqual(
            DotNetJsonProfiles.ShellBootstrap.Reference.Digest.Value,
            digest);
    }
}
