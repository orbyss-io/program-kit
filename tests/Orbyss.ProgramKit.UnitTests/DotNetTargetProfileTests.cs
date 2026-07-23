using Orbyss.ProgramKit.Architecture;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class DotNetTargetProfileTests
{
    [TestMethod]
    public void CanonicalProfileBindsTheEntireApprovedDotNetSelection()
    {
        var profile = DotNetTargetProfile.ProgramKitDotNet10;
        var result = new DotNetTargetProfileValidator().Validate(profile);

        Assert.IsTrue(result.IsValid);
        Assert.AreEqual("pkid:profile:program-kit:dotnet-10", profile.Identity.Value);
        Assert.AreEqual("1.0.0", profile.Version.Value);
        Assert.AreEqual("10.0.302", profile.SdkVersion);
        Assert.AreEqual("disable", profile.RollForward);
        Assert.IsFalse(profile.AllowPrerelease);
        Assert.AreEqual("net10.0", profile.TargetFramework);
        Assert.AreEqual("14.0", profile.LanguageVersion);
    }

    [TestMethod]
    public void AnyTargetProfileDriftFailsClosed()
    {
        var canonical = DotNetTargetProfile.ProgramKitDotNet10;
        var invalidProfiles = new[]
        {
            canonical with { SdkVersion = "10.0.301" },
            canonical with { RollForward = "latestPatch" },
            canonical with { AllowPrerelease = true },
            canonical with { TargetFramework = "net8.0" },
            canonical with { TargetFramework = "net10.0;net8.0" },
            canonical with { LanguageVersion = "latest" },
        };

        foreach (var profile in invalidProfiles)
        {
            Assert.IsFalse(new DotNetTargetProfileValidator().Validate(profile).IsValid);
        }
    }
}
