using System.Security.Cryptography;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;

namespace Orbyss.ProgramKit.UnitTests.SecretResolution.Contracts;

[TestClass]
public sealed class SecretResolutionSchemaModuleTests
{
    [TestMethod]
    public void RegisteredSchemaDigestsBindExactEmbeddedBytes()
    {
        SecretResolutionSchemaModule module = new();

        Assert.HasCount(3, module.Resources);
        foreach (var resource in module.Resources)
        {
            using var stream = module.OpenRead(resource.SchemaReference);
            var digest = string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(stream)));

            Assert.AreEqual(resource.SchemaReference.Digest.Value, digest);
            Assert.AreEqual(ArtifactStatus.Implemented, resource.Status);
        }
    }

    [TestMethod]
    public void SchemaModelPropertyNamesDoNotDrift()
    {
        SecretResolutionSchemaModule module = new();
        var contractSchema = module.Resources.Single(static resource =>
            resource.SchemaReference.Identity.Value ==
            "pkid:schema:program-kit:secret-resolution-contract");
        using var stream = module.OpenRead(contractSchema.SchemaReference);
        using var reader = new StreamReader(stream);
        var schema = reader.ReadToEnd();

        foreach (var property in typeof(
                     Orbyss.ProgramKit.SecretResolution.Contracts.SecretResolutionContract)
                 .GetProperties())
        {
            var jsonName = property.GetCustomAttributes(
                    typeof(JsonPropertyNameAttribute),
                    inherit: false)
                .Cast<JsonPropertyNameAttribute>()
                .Single()
                .Name;
            Assert.Contains(string.Concat("\"", jsonName, "\""), schema);
        }
    }
}
