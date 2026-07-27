using System.Collections.Immutable;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Profiles;

[TestClass]
public sealed class JsonProfileSourceDescriptorValidatorTests
{
    [TestMethod]
    [DataRow(".")]
    [DataRow("..")]
    [DataRow("Composition/./Owned.cs")]
    [DataRow("Composition/../Owned.cs")]
    [DataRow("/Composition/Owned.cs")]
    [DataRow("C:/Composition/Owned.cs")]
    [DataRow(@"Composition\Owned.cs")]
    public void ProfileOwnedMechanicsSourceRejectsUnsafePaths(string path)
    {
        var validator = new JsonProfileSourceDescriptorValidator();
        var descriptor = ProfileSource(
            [new JsonOwnedMechanicsSource(path, Digest('b'))]);

        var result = validator.Validate(descriptor);

        Assert.IsFalse(result.IsValid);
        Assert.Contains(
            diagnostic =>
                diagnostic.Id ==
                ProgramKitJsonDiagnosticIds.InvalidProfile &&
                diagnostic.Path ==
                "/ownedMechanicsSources/0/relativePath",
            result.Diagnostics);
    }

    [TestMethod]
    public void ProfileOwnedMechanicsSourceRejectsDuplicatePaths()
    {
        var validator = new JsonProfileSourceDescriptorValidator();
        var descriptor = ProfileSource(
            [
                new JsonOwnedMechanicsSource(
                    "Composition/Owned.cs",
                    Digest('c')),
                new JsonOwnedMechanicsSource(
                    "Composition/Owned.cs",
                    Digest('d')),
            ]);

        var result = validator.Validate(descriptor);

        Assert.IsFalse(result.IsValid);
        Assert.Contains(
            diagnostic =>
                diagnostic.Id ==
                ProgramKitJsonDiagnosticIds.InvalidProfile &&
                diagnostic.Path ==
                "/ownedMechanicsSources/1/relativePath",
            result.Diagnostics);
    }

    private static JsonProfileSourceDescriptor ProfileSource(
        ImmutableArray<JsonOwnedMechanicsSource> sources) =>
        new(
            new Uri(
                "https://schemas.orbyss.example/program-kit/serialization/profile-source.schema.json"),
            new ProgramKitIdentifier(
                "pkid:profile:tests:source-validation"),
            new SemanticVersion("1.0.0"),
            JsonProfileSourceKind.Serialization,
            ProgramKitJsonProfiles.CanonicalJsonRfc8785,
            JsonProfileExtensibility.None,
            [],
            JsonSerializationLimits.Default,
            [],
            [],
            sources,
            "sha256 over canonical source bytes");

    private static Sha256Digest Digest(char marker) =>
        new(string.Concat("sha256:", new string(marker, 64)));
}
