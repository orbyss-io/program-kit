using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.DotNet.Schemas;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.OpenConsole.Contracts.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Schemas;

[TestClass]
public sealed class DotNetSchemaModuleTests
{
    [TestMethod]
    public void ModuleRegistersOwnedAndOperationDependencySchemas()
    {
        DotNetSchemaModule module = new(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        ProgramKitSchemaModuleValidator validator = new();

        var validation = validator.Validate(module);

        Assert.IsTrue(validation.IsValid);
        Assert.HasCount(38, module.Resources);
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
                new OperationContractDescriptorValidator(),
                new TransportFailureProfileValidator(),
                new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
                DotNetTestContractFactory.ProviderCatalog());
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
        var consoleDocument = DotNetTestContractFactory.ConsoleDocument(shell);
        var consoleDocumentBytes = serializer.Write(
            consoleDocument,
            profile.Reference,
            profile.MaximumLimits);
        var consoleDocumentRevision = new ArtifactReference(
            DotNetTestContractFactory.Id("document", "console"),
            consoleDocument.DocumentVersion,
            Digest(consoleDocumentBytes.ToArray()));
        var consoleHost = shell.Hosts.Single(static host =>
            host.Kind == Orbyss.ProgramKit.DotNet.Shells.DotNetHostKind.Console);
        var dispatchLock = new DotNetConsoleCommandDispatchLockDocument(
            "pkid:schema:program-kit:dotnet-console-command-dispatch-lock@1.0.0",
            new SemanticVersion("1.0.0"),
            consoleDocument.HostRevision,
            shellRevision,
            consoleDocumentRevision,
            consoleHost.GeneratorProfileRevision,
            DotNetTestContractFactory.Ref(
                "contract",
                "console-command-dispatcher",
                'e'));
        var dispatchLockBytes = serializer.Write(
            dispatchLock,
            profile.Reference,
            profile.MaximumLimits);
        var dispatchEvidence = new DotNetConsoleCommandDispatchEvidenceDocument(
            "pkid:schema:program-kit:dotnet-console-command-dispatch-evidence@1.0.0",
            new SemanticVersion("1.0.0"),
            new ArtifactReference(
                DotNetTestContractFactory.Id("lock", "console-dispatch"),
                new SemanticVersion("1.0.0"),
                Digest(dispatchLockBytes.ToArray())),
            "ProgramKitGenerated/Commands/IProgramKitConsoleCommandDispatcher.cs",
            "ConfigureProgramKitConsoleServices",
            true,
            true,
            [
                "parse",
                "compose",
                "resolve-single-dispatcher",
                "start-host",
                "dispatch-once",
                "stop-host-finally",
                "return-dispatcher-integer-unchanged",
            ],
            "ProgramKitGenerated/Commands/GeneratedConsoleParser.cs",
            DotNetTestContractFactory.Digest('c'),
            "ProgramKitGenerated/Commands/GeneratedConsoleParseResult.cs",
            DotNetTestContractFactory.Digest('d'),
            "return-dispatcher-integer-unchanged");
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
                Name: "dotnet-configuration-provider-catalog",
                Content: serializer.Write(
                    new DotNetConfigurationProviderCatalogDocument(
                        "pkid:schema:program-kit:dotnet-configuration-provider-catalog@1.0.0",
                        new ProgramKitIdentifier(
                            "pkid:catalog:program-kit:dotnet-configuration-providers"),
                        new SemanticVersion("1.0.0"),
                        DotNetTestContractFactory.ProviderCatalog().Providers),
                    profile.Reference,
                    profile.MaximumLimits).ToArray()),
            (
                Name: "open-console",
                Content: consoleDocumentBytes.ToArray()),
            (
                Name: "dotnet-console-command-dispatch-lock",
                Content: dispatchLockBytes.ToArray()),
            (
                Name: "dotnet-console-command-dispatch-evidence",
                Content: serializer.Write(
                    dispatchEvidence,
                    profile.Reference,
                    profile.MaximumLimits).ToArray()),
            (
                Name: "open-worker",
                Content: serializer.Write(
                    DotNetTestContractFactory.WorkerDocument(shell),
                    profile.Reference,
                    profile.MaximumLimits).ToArray()),
        };
        DotNetSchemaModule module = new(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        OpenConsoleSchemaModule openConsoleModule = new();
        JsonSchemaWorkbenchValidator validator = new(
            canonicalizer,
            new ProgramKitSchemaModuleValidator());

        foreach (var document in documents)
        {
            IProgramKitSchemaModule selectedModule =
                document.Name == "open-console"
                    ? openConsoleModule
                    : module;
            var schema = selectedModule.Resources.Single(resource =>
                resource.SchemaReference.Identity.Name == document.Name &&
                (document.Name != "dotnet-shell" ||
                 resource.SchemaReference.Version.Value == "11.0.0") &&
                (document.Name != "dotnet-configuration-provider-catalog" ||
                 resource.SchemaReference.Version.Value == "1.0.0"));

            var result = validator.Validate(
                document.Content,
                selectedModule,
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

    private static Sha256Digest Digest(ReadOnlySpan<byte> content) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(content))));
}
