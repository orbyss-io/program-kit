using System.Collections.Immutable;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.DevContainers.Composition;
using Orbyss.ProgramKit.DevContainers.Contracts.Artifacts;
using Orbyss.ProgramKit.DevContainers.Contracts.Definitions;
using Orbyss.ProgramKit.DevContainers.Contracts.Lifecycle;
using Orbyss.ProgramKit.DevContainers.Contracts.Profiles;
using Orbyss.ProgramKit.DevContainers.Contracts.Schemas;
using Orbyss.ProgramKit.DevContainers.Operations.Generation;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.ConformanceTests.Schemas.DevContainers;

[TestClass]
public sealed class DevContainerGenerationConformanceTests
{
    /// <summary>Gets the active test context and cancellation token.</summary>
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public void ImageDockerfileAndComposeOutputsValidateAgainstExactOfficialBaseSchema()
    {
        var generator = DevContainerComposition.CreateGenerator();
        var dockerfile = Opaque(
            ".devcontainer/Dockerfile",
            "FROM example.invalid/base@sha256:" + new string('c', 64) + "\n");
        DevContainerProfile[] profiles =
        [
            new DevContainerImageProfile(string.Concat(
                "mcr.microsoft.com/devcontainers/dotnet@sha256:",
                new string('a', 64))),
            new DevContainerDockerfileProfile(dockerfile, ".."),
            new DevContainerComposeProfile(
                "workspace",
                "/workspaces/example",
                null,
                dockerfile,
                ".."),
        ];
        DevContainerSchemaModule schemas = new();
        JsonSchemaWorkbenchValidator validator = new(
            new ProgramKitJsonCanonicalizer(),
            new ProgramKitSchemaModuleValidator());

        foreach (var profile in profiles)
        {
            var result = generator.Generate(
                Definition(profile),
                TestContext.CancellationToken);
            var json = result.Files.Single(
                static file =>
                    file.RelativePath == ".devcontainer/devcontainer.json");
            var validation = validator.Validate(
                json.Content.AsMemory(),
                schemas,
                DevContainerSchemaModule.BaseSchemaReference,
                JsonSerializationLimits.Default);

            Assert.IsTrue(
                validation.IsValid,
                string.Join(
                    Environment.NewLine,
                    validation.Diagnostics.Select(static item => item.ToString())));
        }
    }

    [TestMethod]
    public void VendoredSchemaAndSelectionEvidenceBindExactUpstreamGitBytes()
    {
        DevContainerSchemaModule schemas = new();
        using var stream = DevContainerSchemaModule.OpenOfficialBaseSchema();
        var schemaBytes = ReadAll(stream);
        Assert.AreEqual(
            "a0883c0405ff433db188849d458fb20b9c0d73e0ba1a6e44c1d83f3b485408dd",
            Digest(schemaBytes));
        using var validationStream = schemas.OpenRead(
            DevContainerSchemaModule.BaseSchemaReference);
        Assert.AreEqual(
            "ad4a53e96281b53a5b4332ebdd8d4cb06d93da152a8c2889f98690874c60716e",
            Digest(ReadAll(validationStream)));

        var assembly = typeof(DevContainerSchemaModule).Assembly;
        var evidenceName = assembly.GetManifestResourceNames().Single(
            static name => name.EndsWith(
                "dev-container-spec-selection-1.0.0.json",
                StringComparison.Ordinal));
        using var evidenceStream = assembly.GetManifestResourceStream(evidenceName);
        Assert.IsNotNull(evidenceStream);
        var evidence = Encoding.UTF8.GetString(ReadAll(evidenceStream));
        Assert.Contains(
            "c95ffeed1d059abfe9ffbe79762dc2fa4e7c2421",
            evidence);
        Assert.Contains(
            "a0883c0405ff433db188849d458fb20b9c0d73e0ba1a6e44c1d83f3b485408dd",
            evidence);
        Assert.Contains("general-purpose Compose semantics", evidence);
    }

    [TestMethod]
    public void ProductPackageHasNoContainerExecutionOrWorkbenchDependency()
    {
        var references = typeof(DevContainerGenerator)
            .Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name)
            .Where(static name => name is not null)
            .ToArray();

        Assert.DoesNotContain("Orbyss.ProgramKit.Workbench", references);
        Assert.DoesNotContain("Docker.DotNet", references);
        Assert.DoesNotContain("Testcontainers", references);
        Assert.DoesNotContain("CliWrap", references);
    }

    private static DevContainerDefinition Definition(DevContainerProfile profile)
    {
        var script = Opaque(
            ".devcontainer/scripts/setup.sh",
            "#!/bin/sh\nset -eu\ndotnet --info\n");
        return new DevContainerDefinition(
            new ProgramKitIdentifier("pkid:dev-container:fixture:conformance"),
            new SemanticVersion("1.0.0"),
            "Conformance development container",
            profile,
            [],
            [],
            [],
            "vscode",
            "vscode",
            [
                new DevContainerLifecycleCommand(
                    DevContainerLifecycleStage.PostCreate,
                    null,
                    ["/bin/sh", ".devcontainer/scripts/setup.sh"]),
            ],
            [script]);
    }

    private static DevContainerOpaqueArtifact Opaque(string path, string content)
    {
        var bytes = Encoding.UTF8.GetBytes(content);
        return new DevContainerOpaqueArtifact(
            path,
            ImmutableArray.Create(bytes),
            new Sha256Digest(string.Concat("sha256:", Digest(bytes))),
            true);
    }

    private static byte[] ReadAll(Stream stream)
    {
        using MemoryStream memory = new();
        stream.CopyTo(memory);
        return memory.ToArray();
    }

    private static string Digest(ReadOnlySpan<byte> bytes) =>
        Convert.ToHexStringLower(SHA256.HashData(bytes));
}
