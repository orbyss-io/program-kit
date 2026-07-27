using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Generation.Aspire;
using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation.Aspire;

[TestClass]
public sealed class AspireAppHostGeneratorTests
{
    [TestMethod]
    public void SameCompositionProducesIdenticalBytesAndTreeDigest()
    {
        AspireAppHostGenerator generator = new();
        var definition = Definition();

        var first = generator.Generate(definition);
        var second = generator.Generate(definition);

        Assert.AreEqual(first.OutputTreeSha256, second.OutputTreeSha256);
        Assert.AreSequenceEqual(
            first.Outputs.Select(static output => output.RelativePath).ToArray(),
            second.Outputs.Select(static output => output.RelativePath).ToArray());
        for (var index = 0; index < first.Outputs.Length; index++)
        {
            Assert.AreSequenceEqual(
                first.Outputs[index].Content.ToArray(),
                second.Outputs[index].Content.ToArray());
        }
    }

    [TestMethod]
    public void ChangedEndpointChangesModelAndOutputDigest()
    {
        AspireAppHostGenerator generator = new();
        var definition = Definition();
        var changed = definition with
        {
            Endpoints =
            [
                definition.Endpoints[0] with { TargetPort = 8081 },
                definition.Endpoints[1],
            ],
        };

        var first = generator.Generate(definition);
        var second = generator.Generate(changed);

        Assert.AreNotEqual(first.OutputTreeSha256, second.OutputTreeSha256);
        Assert.AreNotEqual(Text(first, "apphost.model.json"), Text(second, "apphost.model.json"));
    }

    [TestMethod]
    public void SecretReferenceIsHashedAndNeverRendered()
    {
        AspireAppHostGenerator generator = new();
        var result = generator.Generate(Definition());
        var allText = string.Join(
            Environment.NewLine,
            result.Outputs.Select(output => Encoding.UTF8.GetString(output.Content.Span)));

        Assert.DoesNotContain("pkid:secret-reference:fixture:database-password", allText);
        Assert.Contains("\"referenceSha256\": \"sha256:", allText);
        Assert.Contains("secret: true", Text(result, "Program.cs"));
        Assert.DoesNotContain("password-value", allText);
    }

    [TestMethod]
    public void UnknownIntegrationFailsWithStableDiagnostic()
    {
        var definition = Definition() with
        {
            Integrations =
            [
                new AspireIntegrationSelection(
                    new ProgramKitIdentifier("pkid:integration:program-kit:unknown"),
                    new SemanticVersion("1.0.0")),
            ],
        };

        AspireAppHostGenerator generator = new();
        var exception = Assert.ThrowsExactly<DotNetKitException>(
            () => generator.Generate(definition));

        Assert.AreEqual(DotNetDiagnosticIds.AspireIntegrationMismatch, exception.DiagnosticId);
    }

    [TestMethod]
    public void MissingReferenceAndCycleFailWithStableRelationshipDiagnostic()
    {
        var definition = Definition();
        var missing = definition with
        {
            References = [new AspireResourceReference("api", "missing", "tcp")],
        };
        var cyclic = definition with
        {
            References =
            [
                new AspireResourceReference("api", "database", "tcp"),
                new AspireResourceReference("database", "api", "http"),
            ],
        };

        AspireAppHostGenerator generator = new();
        var missingException = Assert.ThrowsExactly<DotNetKitException>(
            () => generator.Generate(missing));
        var cycleException = Assert.ThrowsExactly<DotNetKitException>(
            () => generator.Generate(cyclic));

        Assert.AreEqual(DotNetDiagnosticIds.InvalidAspireRelationship, missingException.DiagnosticId);
        Assert.AreEqual(DotNetDiagnosticIds.InvalidAspireRelationship, cycleException.DiagnosticId);
    }

    [TestMethod]
    public void ConflictingEndpointFailsWithStableRelationshipDiagnostic()
    {
        var definition = Definition();
        var conflicting = definition with
        {
            Endpoints =
            [
                definition.Endpoints[0],
                definition.Endpoints[0] with { TargetPort = 8081 },
                definition.Endpoints[1],
            ],
        };

        AspireAppHostGenerator generator = new();
        var exception = Assert.ThrowsExactly<DotNetKitException>(
            () => generator.Generate(conflicting));

        Assert.AreEqual(DotNetDiagnosticIds.InvalidAspireRelationship, exception.DiagnosticId);
    }

    [TestMethod]
    public void ContainerImageMustBeDigestPinned()
    {
        var definition = Definition();
        var invalid = definition with
        {
            Resources =
            [
                definition.Resources[0],
                definition.Resources[1] with { ContainerImage = "postgres:18" },
                definition.Resources[2],
            ],
        };

        AspireAppHostGenerator generator = new();
        var exception = Assert.ThrowsExactly<DotNetKitException>(
            () => generator.Generate(invalid));

        Assert.AreEqual(DotNetDiagnosticIds.InvalidAspireComposition, exception.DiagnosticId);
    }

    internal static AspireAppHostDefinition Definition() =>
        new(
            new ProgramKitIdentifier("pkid:apphost:fixture:local-composition"),
            new SemanticVersion("1.0.0"),
            [
                new AspireIntegrationSelection(
                    AspireIntegrationCatalog.AppHost.Identity,
                    AspireIntegrationCatalog.AppHost.Version),
            ],
            [
                new AspireParameterDefinition(
                    "database-password",
                    "Parameters:database-password",
                    SecretReference()),
                new AspireParameterDefinition(
                    "log-level",
                    "Parameters:log-level",
                    null),
            ],
            [
                new AspireResourceDefinition(
                    "api",
                    AspireResourceKind.Project,
                    "../Fixture.Api/Fixture.Api.csproj",
                    "FixtureApi",
                    null,
                    null,
                    [],
                    null),
                new AspireResourceDefinition(
                    "database",
                    AspireResourceKind.Container,
                    null,
                    null,
                    null,
                    null,
                    ["-c", "max_connections=100"],
                    string.Concat(
                        "postgres@sha256:",
                        new string('a', 64))),
                new AspireResourceDefinition(
                    "migration",
                    AspireResourceKind.Executable,
                    null,
                    null,
                    "../tools/migrate",
                    "../tools",
                    ["--apply"],
                    null),
            ],
            [
                new AspireEndpointDefinition(
                    "api",
                    "http",
                    "http",
                    8080,
                    null,
                    true,
                    true),
                new AspireEndpointDefinition(
                    "database",
                    "tcp",
                    "tcp",
                    5432,
                    null,
                    false,
                    true),
            ],
            [
                new AspireEnvironmentBinding("api", "LOG_LEVEL", "log-level"),
                new AspireEnvironmentBinding(
                    "database",
                    "POSTGRES_PASSWORD",
                    "database-password"),
            ],
            [new AspireResourceReference("api", "database", "tcp")],
            [new AspireWaitDependency("migration", "database")],
            [new AspireVolumeDefinition("database", "database-data", "/var/lib/postgresql/data", false)]);

    private static SecretReferenceDescriptor SecretReference()
    {
        var resolver = Reference("pkid:capability:fixture:secret-resolver");
        return new SecretReferenceDescriptor(
            new ProgramKitIdentifier("pkid:secret-reference:fixture:database-password"),
            SecretReferenceClassification.RestrictedMetadata,
            SecretResultKind.ConfigurationText,
            resolver,
            Reference("pkid:locator:fixture:database-password"),
            SecretReferenceClassification.SensitiveMetadata);
    }

    private static ArtifactReference Reference(string identity) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                string.Concat("sha256:", new string('b', 64))));

    private static string Text(AspireAppHostGenerationResult result, string path) =>
        Encoding.UTF8.GetString(
            result.Outputs.Single(output => output.RelativePath == path).Content.Span);
}
