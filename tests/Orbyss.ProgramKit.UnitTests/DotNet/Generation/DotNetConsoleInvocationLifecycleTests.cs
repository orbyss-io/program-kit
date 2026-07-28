using System.Globalization;
using System.Reflection;
using System.Runtime.Loader;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;
using Orbyss.ProgramKit.ConsoleContractFixtures.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;
using Orbyss.ProgramKit.DotNet.Generation.Console.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
[DoNotParallelize]
public sealed class DotNetConsoleInvocationLifecycleTests
{
    [TestInitialize]
    public void ResetRecorder()
    {
        MetadataFixtureInvocationRecorder.Reset();
    }

    [TestMethod]
    public async Task ScopedHandlerRunsOnceAndItsExitCodePassesThrough()
    {
        var candidate = GenerateCandidate(typeof(MetadataFixtureFeature));

        var result = await RunAsync(
            candidate,
            ["execute", "target-1", "--count", "7", "--confirm"]);

        Assert.AreEqual(7, result.ExitCode);
        Assert.AreEqual(1, MetadataFixtureInvocationRecorder.HandlerCalls);
        Assert.AreEqual(0, MetadataFixtureInvocationRecorder.ValidatorCalls);
        Assert.IsTrue(
            MetadataFixtureInvocationRecorder.HandlerObservedCancellation);
    }

    [TestMethod]
    public async Task OptionalConsumerValidatorRunsBeforeHandlerAndFailureExitsTwo()
    {
        MetadataFixtureInvocationRecorder.ValidatorIsValid = false;
        MetadataFixtureInvocationRecorder.ValidatorMessages =
            ["unreachable [endpoint]"];
        var candidate = GenerateCandidate(
            typeof(MetadataFixtureWithValidatorFeature));

        var result = await RunAsync(
            candidate,
            ["execute", "target-1"]);

        Assert.AreEqual(2, result.ExitCode);
        Assert.AreEqual(1, MetadataFixtureInvocationRecorder.ValidatorCalls);
        Assert.AreEqual(0, MetadataFixtureInvocationRecorder.HandlerCalls);
        Assert.Contains("unreachable [endpoint]", result.StandardOutput);
    }

    [TestMethod]
    public async Task GeneratedConstraintValidationPreventsAllConsumerCode()
    {
        var candidate = GenerateCandidate(
            typeof(MetadataFixtureWithValidatorFeature));

        var exception =
            await Assert.ThrowsExactlyAsync<
                global::Spectre.Console.Cli.CommandRuntimeException>(
                async () => await RunAsync(
                    candidate,
                    [
                        "execute",
                        "target-1",
                        "--count",
                        "1",
                        "--force",
                        "--confirm",
                    ]));

        Assert.Contains("Conflicting options", exception.Message);
        Assert.AreEqual(0, MetadataFixtureInvocationRecorder.ValidatorCalls);
        Assert.AreEqual(0, MetadataFixtureInvocationRecorder.HandlerCalls);
    }

    [TestMethod]
    [DataRow(typeof(MissingHandlerMetadataFixtureFeature))]
    [DataRow(typeof(DuplicateHandlerMetadataFixtureFeature))]
    [DataRow(typeof(WrongLifetimeMetadataFixtureFeature))]
    [DataRow(typeof(FactoryHandlerMetadataFixtureFeature))]
    [DataRow(typeof(DuplicateValidatorMetadataFixtureFeature))]
    [DataRow(typeof(RegisteredFeatureMetadataFixtureFeature))]
    public async Task InvalidFeatureRegistrationShapesFailBeforeProviderUse(
        Type featureType)
    {
        var candidate = GenerateCandidate(featureType);

        var exception = await Assert.ThrowsExactlyAsync<InvalidOperationException>(
            async () => await RunAsync(
                candidate,
                ["execute", "target-1"]));

        Assert.IsFalse(string.IsNullOrWhiteSpace(exception.Message));
        Assert.AreEqual(0, MetadataFixtureInvocationRecorder.ValidatorCalls);
        Assert.AreEqual(0, MetadataFixtureInvocationRecorder.HandlerCalls);
    }

    [TestMethod]
    public void GeneratedCompositionBuildsOneProviderAndOneInvocationScope()
    {
        var candidate = GenerateCandidate(typeof(MetadataFixtureFeature));
        var registrar = Text(
            candidate.Outputs,
            "ProgramKitGenerated/Hosting/ProgramKitTypeRegistrar.cs");
        var program = Text(
            candidate.Outputs,
            "ProgramKitGenerated/Program.cs");

        Assert.AreEqual(
            1,
            Occurrences(registrar, "BuildServiceProvider("));
        Assert.AreEqual(1, Occurrences(registrar, "CreateScope("));
        Assert.Contains(
            "ProgramKitServiceRegistrationAudit.Audit(services);",
            program);
        Assert.IsLessThan(
            program.IndexOf(
                "new global::GeneratedHost.Hosting.ProgramKitTypeRegistrar",
                StringComparison.Ordinal),
            program.IndexOf(
                "ProgramKitServiceRegistrationAudit.Audit(services);",
                StringComparison.Ordinal));
    }

    private static (
        ImmutableArray<GeneratedOutput> Outputs,
        ImmutableArray<byte> AssemblyBytes
    ) GenerateCandidate(Type featureType)
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts.Single(static item =>
            item.Kind == DotNetHostKind.Console);
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "lifecycle",
            '9');
        DotNetShellLockBuilder lockBuilder = new(CreateValidator());
        var hostLock = lockBuilder
            .Build(shell, shellRevision)
            .HostLocks.Single(static item =>
                item.Kind == DotNetHostKind.Console);
        DotNetConsoleGenerationInput input =
            DotNetConsoleBindingTestFactory.GenerationInput(
                document,
                DotNetTestContractFactory.Ref(
                    "document",
                    "lifecycle",
                    '8'),
                featureType);
        var outputs = DotNetConsoleGenerationComposition.Create().Generate(
            host,
            hostLock,
            document,
            input,
            CancellationToken.None);
        var sources = outputs
            .Where(static output =>
                output.RelativePath.EndsWith(
                    ".cs",
                    StringComparison.Ordinal))
            .Select(static output => new DotNetConsoleSourceFile(
                output.RelativePath,
                Encoding.UTF8.GetString(output.Content.Span)))
            .ToImmutableArray();
        DotNetConsoleCandidateCompiler compiler = new();
        var compilation = compiler.Compile(
            sources,
            input.CompilationReferences,
            CancellationToken.None);
        Assert.IsTrue(
            compilation.IsValid,
            string.Join(
                Environment.NewLine,
                compilation.Diagnostics.Select(static item =>
                    item.Message)));
        return (outputs, compilation.AssemblyBytes);
    }

    private static async Task<(int ExitCode, string StandardOutput)> RunAsync(
        (
            ImmutableArray<GeneratedOutput> Outputs,
            ImmutableArray<byte> AssemblyBytes
        ) candidate,
        string[] arguments)
    {
        AssemblyLoadContext context = new(
            string.Concat(
                "ProgramKitConsoleLifecycle-",
                Guid.NewGuid().ToString("N")),
            isCollectible: true);
        context.Resolving += ResolveFromCurrentProcess;
        var originalOutput = Console.Out;
        using StringWriter output = new(CultureInfo.InvariantCulture);
        Console.SetOut(output);
        try
        {
            using MemoryStream stream = new(
                candidate.AssemblyBytes.ToArray(),
                writable: false);
            var assembly = context.LoadFromStream(stream);
            var entryPoint = assembly.EntryPoint ??
                throw new AssertFailedException(
                    "The generated candidate has no entry point.");
            var invocation = entryPoint.Invoke(
                null,
                entryPoint.GetParameters().Length == 0
                    ? null
                    : [arguments]);
            var exitCode = invocation switch
            {
                Task<int> task => await task.ConfigureAwait(false),
                int value => value,
                _ => throw new AssertFailedException(
                    "The generated entry point has an unsupported return shape."),
            };
            return (exitCode, output.ToString());
        }
        catch (TargetInvocationException exception)
            when (exception.InnerException is not null)
        {
            System.Runtime.ExceptionServices.ExceptionDispatchInfo
                .Capture(exception.InnerException)
                .Throw();
            throw new System.Diagnostics.UnreachableException();
        }
        finally
        {
            Console.SetOut(originalOutput);
            context.Resolving -= ResolveFromCurrentProcess;
            context.Unload();
        }
    }

    private static Assembly? ResolveFromCurrentProcess(
        AssemblyLoadContext context,
        AssemblyName assemblyName)
    {
        _ = context;
        return AppDomain.CurrentDomain.GetAssemblies().SingleOrDefault(
            assembly =>
                string.Equals(
                    assembly.GetName().Name,
                    assemblyName.Name,
                    StringComparison.Ordinal));
    }

    private static DotNetShellValidator CreateValidator() =>
        new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());

    private static string Text(
        ImmutableArray<GeneratedOutput> outputs,
        string path) =>
        Encoding.UTF8.GetString(
            outputs.Single(output =>
                output.RelativePath == path).Content.Span);

    private static int Occurrences(string value, string fragment) =>
        (value.Length -
         value.Replace(fragment, string.Empty, StringComparison.Ordinal).Length) /
        fragment.Length;
}
