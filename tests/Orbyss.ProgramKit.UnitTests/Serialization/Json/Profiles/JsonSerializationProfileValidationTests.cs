using Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Profiles;

[TestClass]
public sealed class JsonSerializationProfileValidationTests
{
    [TestMethod]
    [DataRow(false, true)]
    [DataRow(true, false)]
    public void RegistryRejectsDescriptorRuntimeRuleDrift(
        bool caseSensitiveReads,
        bool writeNullProperties)
    {
        var invalid = ProgramKitJsonProfiles.JsonContracts with
        {
            Reference = new JsonSerializationProfileRef(
                new ProgramKitIdentifier(
                    "pkid:profile:tests:invalid-rules"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")),
            Rules = ProgramKitJsonProfiles.JsonContracts.Rules with
            {
                CaseSensitiveReads = caseSensitiveReads,
                WriteNullProperties = writeNullProperties,
            },
        };
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddProfile(invalid);

        var exception =
            Assert.ThrowsExactly<ProgramKitJsonException>(
                builder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidProfile,
            exception.Diagnostic.Id);
    }

    [TestMethod]
    public void RegistryMapsMalformedProfileMembersToStableDiagnostics()
    {
        var invalid = ProgramKitJsonProfiles.JsonContracts with
        {
            Reference = new JsonSerializationProfileRef(
                new ProgramKitIdentifier(
                    "pkid:profile:tests:malformed"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")),
            CanonicalizationProfile = null!,
        };
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddProfile(invalid);

        var exception =
            Assert.ThrowsExactly<ProgramKitJsonException>(
                builder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidProfile,
            exception.Diagnostic.Id);
    }

    [TestMethod]
    public void RegistryMapsDefaultPrimitiveMembersToStableDiagnostics()
    {
        var invalidProfile = ProgramKitJsonProfiles.JsonContracts with
        {
            Reference =
                new JsonSerializationProfileRef(default, default, default),
        };
        var invalidProfileBuilder =
            ProgramKitJsonTestComposition.CreateBuilder();
        invalidProfileBuilder.AddProfile(invalidProfile);

        var profileException =
            Assert.ThrowsExactly<ProgramKitJsonException>(
                invalidProfileBuilder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidProfile,
            profileException.Diagnostic.Id);

        var validContribution =
            new TypedJsonConverterContribution<ProbeId>(
                JsonContributionTestFactory.CreateDescriptor(
                    "default-selection-profile",
                    "4",
                    JsonSerializationContributionKind.TypedConverter,
                    JsonTargetTypeClaim.For<ProbeId>()),
                new ProbeIdConverter());
        var invalidSelectionBuilder =
            ProgramKitJsonTestComposition.CreateBuilder();
        invalidSelectionBuilder.AddJsonSerializationContribution(
            new JsonSerializationProfileRef(default, default, default),
            validContribution);

        var selectionException =
            Assert.ThrowsExactly<ProgramKitJsonException>(
                invalidSelectionBuilder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidProfile,
            selectionException.Diagnostic.Id);

        var validDescriptor =
            JsonContributionTestFactory.CreateDescriptor(
                "default-descriptor",
                "5",
                JsonSerializationContributionKind.TypedConverter,
                JsonTargetTypeClaim.For<ProbeId>());
        var invalidDescriptors = new[]
        {
            validDescriptor with
            {
                Reference =
                    new JsonSerializationContributionRef(
                        default,
                        default,
                        default),
            },
            validDescriptor with
            {
                OwningPackage = default,
            },
            validDescriptor with
            {
                ApplicableProfileId = default,
            },
            validDescriptor with
            {
                ApplicableProfileRange = default,
            },
        };
        foreach (var descriptor in invalidDescriptors)
        {
            var contribution =
                new TypedJsonConverterContribution<ProbeId>(
                    descriptor,
                    new ProbeIdConverter());
            var builder = ProgramKitJsonTestComposition.CreateBuilder();
            builder.AddJsonSerializationContribution(
                ProgramKitJsonProfiles.JsonContracts.Reference,
                contribution);

            var exception =
                Assert.ThrowsExactly<ProgramKitJsonException>(
                    builder.Freeze);

            Assert.AreEqual(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                exception.Diagnostic.Id);
        }
    }
}
