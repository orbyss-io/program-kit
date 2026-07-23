namespace Orbyss.ProgramKit.UnitTests.Architecture.Targeting;

[TestClass]
public sealed class DotNetTargetProfileTests
{
    [TestMethod]
    public void CanonicalProfileBindsTheEntireApprovedDotNetSelection()
    {
        var profile = DotNetTargetProfile.ProgramKitDotNet10;
        DefaultArtifactEnvelopeValidator envelopeValidator = new();
        DotNetTargetProfileValidator sut = new(envelopeValidator);

        var result = sut.Validate(profile);

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
        DefaultArtifactEnvelopeValidator envelopeValidator = new();
        DotNetTargetProfileValidator sut = new(envelopeValidator);

        foreach (var profile in invalidProfiles)
        {
            Assert.IsFalse(sut.Validate(profile).IsValid);
        }
    }
}
