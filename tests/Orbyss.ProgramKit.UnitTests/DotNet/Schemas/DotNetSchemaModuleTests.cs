using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.DotNet.Schemas;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Schemas;

[TestClass]
public sealed class DotNetSchemaModuleTests
{
    [TestMethod]
    public void ModuleRegistersOwnedAndOperationDependencySchemas()
    {
        DotNetSchemaModule module = new(new OperationsSchemaModule());
        ProgramKitSchemaModuleValidator validator = new();

        var validation = validator.Validate(module);

        Assert.IsTrue(validation.IsValid);
        Assert.HasCount(13, module.Resources);
        foreach (var resource in module.Resources)
        {
            using var stream = module.OpenRead(resource.SchemaReference);
            var actual = string.Concat(
                "sha256:",
                Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant());
            Assert.AreEqual(resource.SchemaReference.Digest.Value, actual);
        }
    }

    [TestMethod]
    public void TypedBootstrapDocumentsConformToTheirExactSchemas()
    {
        var shell = DotNetTestContractFactory.Shell();
        IDotNetShellValidator shellValidator =
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator());
        DotNetShellLockBuilder lockBuilder = new(shellValidator);
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "reviewed",
            '7');
        var lockDocument = lockBuilder.Build(shell, shellRevision);
        var inputManifest = new DotNetArtifactInputManifest(
            "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            [
                new DotNetArtifactInputEntry(
                    shell.InputVersionMapRevision,
                    "versions/map.json"),
                new DotNetArtifactInputEntry(
                    shell.InputVersionSelectionRevision,
                    "versions/selection.json"),
            ],
            []);
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder builder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(builder);
        ProgramKitJsonCanonicalizer canonicalizer = new();
        ProgramKitJsonSerializer serializer = new(
            builder.Freeze(),
            canonicalizer);
        var profile = DotNetJsonProfiles.ShellBootstrap;
        var documents = new[]
        {
            (
                Name: "dotnet-artifact-input-manifest",
                Content: serializer.Write(
                    inputManifest,
                    profile.Reference,
                    profile.MaximumLimits).ToArray()),
            (
                Name: "dotnet-shell",
                Content: serializer.Write(
                    shell,
                    profile.Reference,
                    profile.MaximumLimits).ToArray()),
            (
                Name: "dotnet-shell-lock",
                Content: serializer.Write(
                    lockDocument,
                    profile.Reference,
                    profile.MaximumLimits).ToArray()),
            (
                Name: "open-console",
                Content: serializer.Write(
                    DotNetTestContractFactory.ConsoleDocument(shell),
                    profile.Reference,
                    profile.MaximumLimits).ToArray()),
            (
                Name: "open-worker",
                Content: serializer.Write(
                    DotNetTestContractFactory.WorkerDocument(shell),
                    profile.Reference,
                    profile.MaximumLimits).ToArray()),
        };
        DotNetSchemaModule module = new(new OperationsSchemaModule());
        JsonSchemaWorkbenchValidator validator = new(
            canonicalizer,
            new ProgramKitSchemaModuleValidator());

        foreach (var document in documents)
        {
            var schema = module.Resources.Single(resource =>
                resource.SchemaReference.Identity.Name == document.Name &&
                (document.Name != "dotnet-shell" ||
                 resource.SchemaReference.Version.Value == "2.0.0"));

            var result = validator.Validate(
                document.Content,
                module,
                schema.SchemaReference,
                profile.MaximumLimits);

            Assert.IsTrue(
                result.IsValid,
                string.Join(
                    Environment.NewLine,
                    result.Diagnostics.Select(static diagnostic =>
                        string.Concat(
                            diagnostic.Id,
                            " ",
                            diagnostic.Path,
                            " ",
                            diagnostic.Message))));
        }
    }
}
