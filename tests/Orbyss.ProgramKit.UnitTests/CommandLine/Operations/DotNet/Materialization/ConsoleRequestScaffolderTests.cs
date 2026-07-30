using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Schemas;
using Orbyss.ProgramKit.CommandLine.Operations.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Schemas;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.OpenConsole.Contracts.Schemas;
using Orbyss.ProgramKit.OpenConsole.Contracts.Validation;
using Orbyss.ProgramKit.Operations.Contracts.Schemas;
using Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Materialization;

[TestClass]
public sealed class ConsoleRequestScaffolderTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task InterruptedPromotionRemovesStagingAndPublishesNoOutput()
    {
        var root = CopyFixture();
        CommandFileSystem physicalFileSystem = new();
        try
        {
            ThrowingMoveCommandFileSystem fileSystem = new(
                physicalFileSystem);
            var scaffolder = CreateScaffolder(fileSystem);
            var output = Path.Combine(root, "request.json");

            var exception =
                await Assert.ThrowsAsync<ConsoleRequestScaffoldingException>(
                    async () => await scaffolder.ScaffoldAsync(
                        Path.Combine(root, "console-command-sketch.json"),
                        root,
                        "src/JTest.Console.Integration/JTest.Console.Integration.csproj",
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("/output", exception.Path);
            Assert.IsFalse(File.Exists(output));
            Assert.IsFalse(File.Exists(
                string.Concat(output, ".program-kit-staging")));
        }
        finally
        {
            physicalFileSystem.DeleteDirectory(root);
        }
    }

    private static ConsoleRequestScaffolder CreateScaffolder(
        ICommandFileSystem fileSystem)
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder builder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(builder);
        ProgramKitJsonCanonicalizer canonicalizer = new();
        ProgramKitJsonSerializer serializer = new(
            builder.Freeze(),
            canonicalizer);
        OperationsSchemaModule operations = new();
        SecretResolutionSchemaModule secrets = new();
        IProgramKitSchemaModule[] modules =
        [
            new ArtifactsSchemaModule(),
            new OpenConsoleSchemaModule(),
            new DotNetSchemaModule(operations, secrets),
        ];
        SchemaCatalog catalog = new(modules);
        SchemaDependencyClosureProvider closureProvider = new(
            catalog,
            new SchemaDependencyClosureModuleFactory());
        CommandSchemaSelector selector = new(catalog, closureProvider);
        JsonSchemaWorkbenchValidator schemaValidator = new(
            canonicalizer,
            new ProgramKitSchemaModuleValidator());
        DotNetShellValidator shellValidator = new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());
        return new ConsoleRequestScaffolder(
            fileSystem,
            serializer,
            selector,
            schemaValidator,
            shellValidator,
            new OpenConsoleDocumentAlpha2Validator(
                new OpenConsoleDocumentValidator()),
            new DotNetConsoleBindingValidator());
    }

    private static string CopyFixture()
    {
        var source = Path.Combine(
            FindProgramKitRoot(),
            "tests",
            "Fixtures",
            "ConsumerCliConsole");
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-console-scaffold-interruption-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(Path.Combine(root, "inputs"));
        Directory.CreateDirectory(
            Path.Combine(root, "src", "JTest.Console.Integration"));
        Copy("console-command-sketch.json");
        Copy(Path.Combine("inputs", "version-map.json"));
        Copy(Path.Combine("inputs", "version-selection.json"));
        Copy(Path.Combine(
            "src",
            "JTest.Console.Integration",
            "JTest.Console.Integration.csproj"));
        return root;

        void Copy(string relativePath)
        {
            File.Copy(
                Path.Combine(source, relativePath),
                Path.Combine(root, relativePath));
        }
    }

    private static string FindProgramKitRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null &&
               !File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
        {
            current = current.Parent;
        }

        return current?.FullName ??
            throw new InvalidOperationException(
                "The Program Kit repository root was not found.");
    }
}
