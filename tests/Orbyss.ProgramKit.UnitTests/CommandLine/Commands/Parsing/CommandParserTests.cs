using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Commands.Parsing;

[TestClass]
public sealed class CommandParserTests
{
    [TestMethod]
    public void ParsesExactNestedCommandAndLongOptions()
    {
        CommandParser sut = new(CommandDescriptorCatalog.All);

        var result = sut.Parse(
        [
            "dotnet",
            "generate-host",
            "worker",
            "--shell=shell.json",
            "--host",
            "pkid:host:test:worker",
            "--artifact-manifest",
            "inputs.json",
            "--output",
            "generated",
        ]);

        Assert.AreEqual("dotnet.generate-host", result.Descriptor.Key);
        Assert.AreEqual("worker", result.Arguments[0]);
        Assert.AreEqual("shell.json", result.RequiredOption("shell"));
        Assert.AreEqual("pkid:host:test:worker", result.RequiredOption("host"));
    }

    [TestMethod]
    public void RejectsDuplicateOptionBeforeExecution()
    {
        CommandParser sut = new(CommandDescriptorCatalog.All);

        var exception = Assert.ThrowsExactly<CommandInvocationException>(
            () => sut.Parse(
            [
                "digest",
                "artifact.json",
                "--diagnostics",
                "text",
                "--diagnostics",
                "json",
            ]));

        Assert.AreEqual("/options/diagnostics", exception.Path);
    }

    [TestMethod]
    public void RejectsAmbiguousValidateInputShape()
    {
        CommandParser sut = new(CommandDescriptorCatalog.All);

        Assert.ThrowsExactly<CommandInvocationException>(
            () => sut.Parse(
            [
                "validate",
                "artifact.json",
                "--manifest",
                "manifest.json",
            ]));
    }

    [TestMethod]
    public void ParsesExplicitLocalPackageAndPublishCommands()
    {
        CommandParser sut = new(CommandDescriptorCatalog.All);

        var packages = sut.Parse(
        [
            "packages",
            "prepare-local",
            "--workspace-manifest",
            "workspace-packages.json",
            "--output",
            "packages",
        ]);
        var publish = sut.Parse(
        [
            "dotnet",
            "publish-local",
            "--shell",
            "shell.json",
            "--host",
            "pkid:host:tests:api",
            "--artifact-manifest",
            "artifacts.json",
            "--package-manifest",
            "packages/local-package-root-manifest.json",
            "--output",
            "published",
        ]);

        Assert.AreEqual("packages.prepare-local", packages.Descriptor.Key);
        Assert.AreEqual(
            "workspace-packages.json",
            packages.RequiredOption("workspace-manifest"));
        Assert.AreEqual("dotnet.publish-local", publish.Descriptor.Key);
        Assert.AreEqual(
            "pkid:host:tests:api",
            publish.RequiredOption("host"));
    }

    [TestMethod]
    public void ParsesExplicitPinnedForeignClientCommand()
    {
        CommandParser sut = new(CommandDescriptorCatalog.All);

        var result = sut.Parse(
        [
            "dotnet",
            "generate-client",
            "--openapi",
            "foreign.openapi.json",
            "--tool-manifest",
            ".config/dotnet-tools.json",
            "--tool-package",
            "microsoft.openapi.kiota.1.34.1.nupkg",
            "--namespace-name",
            "Example.ForeignApi",
            "--class-name",
            "ForeignApiClient",
            "--output",
            "generated-client",
        ]);

        Assert.AreEqual("dotnet.generate-client", result.Descriptor.Key);
        Assert.AreEqual(
            "foreign.openapi.json",
            result.RequiredOption("openapi"));
        Assert.AreEqual(
            "microsoft.openapi.kiota.1.34.1.nupkg",
            result.RequiredOption("tool-package"));
    }

    [TestMethod]
    public void ParsesExplicitCapabilityCommands()
    {
        CommandParser sut = new(CommandDescriptorCatalog.All);

        var catalog = sut.Parse(
        [
            "capabilities",
            "render-catalog",
            ".agent-capabilities/capabilities/INDEX.md",
            "--output",
            ".agent-capabilities/capabilities/README.md",
        ]);
        var bundle = sut.Parse(
        [
            "capabilities",
            "verify-bundle",
            "Orbyss.ProgramKit.CapabilityBundle.0.1.0-alpha.1.nupkg",
        ]);
        var initialize = sut.Parse(
        [
            "capabilities",
            "initialize",
            "--provider",
            "codex",
            "--workspace-root",
            "C:/work",
            "--program-kit-root",
            "C:/work/tools/program-kit",
        ]);
        var initializeClaude = sut.Parse(
        [
            "capabilities",
            "initialize",
            "--provider",
            "claude",
            "--workspace-root",
            "C:/work",
            "--program-kit-root",
            "C:/work/tools/program-kit",
        ]);

        Assert.AreEqual(
            "capabilities.render-catalog",
            catalog.Descriptor.Key);
        Assert.AreEqual(
            ".agent-capabilities/capabilities/INDEX.md",
            catalog.Arguments[0]);
        Assert.AreEqual(
            "capabilities.verify-bundle",
            bundle.Descriptor.Key);
        Assert.AreEqual(
            "capabilities.initialize",
            initialize.Descriptor.Key);
        Assert.AreEqual(
            "capabilities.initialize",
            initializeClaude.Descriptor.Key);
        Assert.AreEqual(
            "claude",
            initializeClaude.RequiredOption("provider"));
    }
}
