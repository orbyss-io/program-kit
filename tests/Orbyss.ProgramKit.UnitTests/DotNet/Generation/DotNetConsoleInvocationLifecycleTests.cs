using System.Diagnostics;
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

        var result = await RunAsync(
            candidate,
            [
                "execute",
                "target-1",
                "--count",
                "1",
                "--force",
                "--confirm",
            ]);

        Assert.AreEqual(2, result.ExitCode);
        Assert.Contains("Conflicting options", result.StandardError);
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

        var result = await RunAsync(
            candidate,
            ["execute", "target-1"]);

        Assert.AreEqual(3, result.ExitCode);
        Assert.Contains("Unexpected internal", result.StandardError);
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

    [TestMethod]
    [DataRow("Execute", "target-1")]
    [DataRow("execute", "target-1", "--unknown")]
    [DataRow("execute", "target-1", "--count", "not-an-int")]
    public async Task ParseFailuresExitTwoBeforeConsumerCode(
        params string[] arguments)
    {
        var candidate = GenerateCandidate(typeof(MetadataFixtureFeature));

        var result = await RunProcessAsync(candidate, arguments);

        Assert.AreEqual(2, result.ExitCode);
        Assert.IsFalse(string.IsNullOrWhiteSpace(result.StandardError));
    }

    [TestMethod]
    public async Task EqualsAliasAndCanonicalDefaultFollowPinnedProfile()
    {
        var candidate = GenerateCandidate(typeof(MetadataFixtureFeature));

        var equals = await RunProcessAsync(
            candidate,
            ["execute", "target-1", "--count=7", "--confirm"]);
        Assert.AreEqual(7, equals.ExitCode);

        var canonical = await RunProcessAsync(
            candidate,
            ["observe", "run", "target-1"]);
        Assert.AreEqual(1, canonical.ExitCode);
    }

    [TestMethod]
    public async Task DuplicateScalarOptionUsesDeclaredLastValueWinsPolicy()
    {
        var candidate = GenerateCandidate(typeof(MetadataFixtureFeature));

        var result = await RunProcessAsync(
            candidate,
            [
                "execute",
                "target-1",
                "--count",
                "3",
                "--count",
                "4",
                "--confirm",
            ]);

        Assert.AreEqual(4, result.ExitCode);
    }

    [TestMethod]
    public async Task NativeAndRepeatedValuesUseSpectreBindingWithInvariantCulture()
    {
        var candidate = GenerateCandidate(typeof(MetadataFixtureFeature));

        var result = await RunProcessAsync(
            candidate,
            [
                "execute",
                "native-types",
                "--total=9223372036854775000",
                "--ratio=1234.50",
                "--correlation=67ed4ad8-cc28-4f98-aecb-852a50d7b04f",
                "--at=2026-07-28T08:15:30.0000000+02:00",
                "--tag=alpha",
                "--tag=beta",
            ]);

        Assert.AreEqual(37, result.ExitCode, result.StandardError);
    }

    [TestMethod]
    public async Task OptionTerminatorIsNotPartOfTheDeclaredProfile()
    {
        var candidate = GenerateCandidate(typeof(MetadataFixtureFeature));

        var result = await RunProcessAsync(
            candidate,
            ["execute", "--", "--literal-target"]);

        Assert.AreEqual(2, result.ExitCode);
    }

    [TestMethod]
    public async Task HelpAndCompletionNeverComposeConsumerFeature()
    {
        var candidate = GenerateCandidate(
            typeof(MissingHandlerMetadataFixtureFeature));

        var help = await RunProcessAsync(candidate, ["execute", "--help"]);
        Assert.AreEqual(0, help.ExitCode, help.StandardError);
        Assert.Contains("USAGE", help.StandardOutput);

        var completion = await RunProcessAsync(candidate, ["--complete"]);
        Assert.AreEqual(0, completion.ExitCode);
        Assert.Contains("--count=<int32>", completion.StandardOutput);
        Assert.Contains("observe run", completion.StandardOutput);
    }

    [TestMethod]
    public async Task UnexpectedConsumerFailureUsesDeclaredInternalCode()
    {
        var candidate = GenerateCandidate(
            typeof(ThrowingMetadataFixtureFeature));

        var result = await RunProcessAsync(
            candidate,
            ["execute", "target-1"]);

        Assert.AreEqual(3, result.ExitCode);
        Assert.Contains("Unexpected internal", result.StandardError);
        Assert.DoesNotContain("Consumer exception detail", result.StandardError);
    }

    [TestMethod]
    public async Task CancelledInvocationUsesDeclaredCancellationCode()
    {
        var candidate = GenerateCandidate(typeof(MetadataFixtureFeature));
        AssemblyLoadContext context = new(
            string.Concat(
                "ProgramKitConsoleCancellation-",
                Guid.NewGuid().ToString("N")),
            isCollectible: true);
        context.Resolving += ResolveFromCurrentProcess;
        try
        {
            using MemoryStream stream = new(
                candidate.AssemblyBytes.ToArray(),
                writable: false);
            var assembly = context.LoadFromStream(stream);
            var outcome = assembly.GetType(
                "GeneratedHost.Hosting.ProgramKitInvocationOutcome",
                throwOnError: true) ??
                throw new AssertFailedException(
                    "The generated cancellation outcome type is missing.");
            var run = outcome.GetMethod(
                "RunAsync",
                BindingFlags.Static | BindingFlags.NonPublic) ??
                throw new AssertFailedException(
                    "The generated cancellation outcome method is missing.");
            using CancellationTokenSource cancellation = new();
            cancellation.Cancel();
            Func<Task<int>> invocation = () =>
                Task.FromCanceled<int>(cancellation.Token);
            var task = run.Invoke(
                null,
                [invocation, cancellation.Token]) as Task<int> ??
                throw new AssertFailedException(
                    "The generated cancellation outcome has an invalid shape.");

            Assert.AreEqual(1, await task);
        }
        finally
        {
            context.Resolving -= ResolveFromCurrentProcess;
            context.Unload();
        }
    }

    [TestMethod]
    public async Task JTestShapedConsumerUsesTypedSpectreCommandsAndExactExitCodes()
    {
        var candidate = GenerateJTestCandidate();

        var run = await RunProcessAsync(
            candidate,
            ["run", "all", "--maximum-parallelism=7"]);
        var validate = await RunProcessAsync(
            candidate,
            ["validate", "jtest.json"]);
        var describe = await RunProcessAsync(
            candidate,
            ["describe", "all"]);
        var wrongType = await RunProcessAsync(
            candidate,
            ["run", "all", "--maximum-parallelism", "many"]);

        Assert.AreEqual(17, run.ExitCode, run.StandardError);
        Assert.AreEqual(23, validate.ExitCode, validate.StandardError);
        Assert.AreEqual(29, describe.ExitCode, describe.StandardError);
        Assert.AreEqual(2, wrongType.ExitCode);
        Assert.IsFalse(string.IsNullOrWhiteSpace(wrongType.StandardError));
    }

    [TestMethod]
    public async Task JTestConsumerValidationPrecedesHandlerAndIsOptionalPerCommand()
    {
        var candidate = GenerateJTestCandidate();

        var rejected = await RunProcessAsync(candidate, ["run", "missing"]);
        Assert.AreEqual(
            2,
            rejected.ExitCode,
            string.Concat(rejected.StandardOutput, rejected.StandardError));
        Assert.Contains(
            "suite 'missing' is unavailable",
            rejected.StandardOutput);
        Assert.DoesNotContain(
            "run handler invoked",
            rejected.StandardOutput);

        var unvalidated = await RunProcessAsync(
            candidate,
            ["validate", "jtest.json"]);
        Assert.AreEqual(23, unvalidated.ExitCode);
        Assert.Contains(
            "validate handler invoked",
            unvalidated.StandardOutput);
        Assert.DoesNotContain(
            "Consumer validation failed",
            unvalidated.StandardOutput);
    }

    [TestMethod]
    public void JTestGenerationIsByteIdenticalAndContainsNoSecondParser()
    {
        var first = GenerateJTestCandidate().Outputs;
        var second = GenerateJTestCandidate().Outputs;

        Assert.AreSequenceEqual(
            first.Select(static item => item.RelativePath).ToArray(),
            second.Select(static item => item.RelativePath).ToArray());
        for (var index = 0; index < first.Length; index++)
        {
            Assert.AreSequenceEqual(
                first[index].Content.ToArray(),
                second[index].Content.ToArray(),
                first[index].RelativePath);
        }

        Assert.IsTrue(first.Any(static item =>
            item.RelativePath ==
                "ProgramKitGenerated/Commands/Run/RunCommand.cs"));
        Assert.IsTrue(first.Any(static item =>
            item.RelativePath ==
                "ProgramKitGenerated/Commands/Validate/ValidateCommand.cs"));
        Assert.IsTrue(first.Any(static item =>
            item.RelativePath ==
                "ProgramKitGenerated/Commands/Describe/DescribeCommand.cs"));
        var generatedText = string.Join(
            Environment.NewLine,
            first
                .Where(static item =>
                    item.RelativePath.EndsWith(".cs", StringComparison.Ordinal))
                .Select(static item => Encoding.UTF8.GetString(item.Content.Span)));
        Assert.Contains("Spectre.Console.Cli.CommandApp", generatedText);
        Assert.DoesNotContain("GeneratedConsoleParser", generatedText);
        Assert.DoesNotContain("ConsoleCommandDispatcher", generatedText);
        Assert.DoesNotContain("GeneratedConsoleParseResult", generatedText);
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

    private static (
        ImmutableArray<GeneratedOutput> Outputs,
        ImmutableArray<byte> AssemblyBytes
    ) GenerateJTestCandidate()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts.Single(static item =>
            item.Kind == DotNetHostKind.Console);
        var document = DotNetTestContractFactory.JTestConsoleDocument(shell);
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "jtest-lifecycle",
            '7');
        DotNetShellLockBuilder lockBuilder = new(CreateValidator());
        var hostLock = lockBuilder
            .Build(shell, shellRevision)
            .HostLocks.Single(static item =>
                item.Kind == DotNetHostKind.Console);
        var documentRevision = DotNetTestContractFactory.Ref(
            "document",
            "jtest-console",
            '6');
        var input = DotNetConsoleBindingTestFactory.JTestGenerationInput(
            document,
            documentRevision);
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

    private static async Task<(
        int ExitCode,
        string StandardOutput,
        string StandardError)> RunAsync(
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
        var originalError = Console.Error;
        using StringWriter output = new(CultureInfo.InvariantCulture);
        using StringWriter error = new(CultureInfo.InvariantCulture);
        Console.SetOut(output);
        Console.SetError(error);
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
            return (exitCode, output.ToString(), error.ToString());
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
            Console.SetError(originalError);
            context.Resolving -= ResolveFromCurrentProcess;
            context.Unload();
        }
    }

    private static async Task<(
        int ExitCode,
        string StandardOutput,
        string StandardError)> RunProcessAsync(
        (
            ImmutableArray<GeneratedOutput> Outputs,
            ImmutableArray<byte> AssemblyBytes
        ) candidate,
        string[] arguments)
    {
        var candidatePath = Path.Combine(
            AppContext.BaseDirectory,
            string.Concat(
                "ProgramKitConsoleProcess-",
                Guid.NewGuid().ToString("N"),
                ".dll"));
        await File.WriteAllBytesAsync(
            candidatePath,
            candidate.AssemblyBytes.ToArray());
        try
        {
            ProcessStartInfo start = new("dotnet")
            {
                WorkingDirectory = AppContext.BaseDirectory,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
            };
            start.ArgumentList.Add("exec");
            start.ArgumentList.Add("--runtimeconfig");
            start.ArgumentList.Add(
                Path.Combine(
                    AppContext.BaseDirectory,
                    "Orbyss.ProgramKit.UnitTests.runtimeconfig.json"));
            start.ArgumentList.Add("--depsfile");
            start.ArgumentList.Add(
                Path.Combine(
                    AppContext.BaseDirectory,
                    "Orbyss.ProgramKit.UnitTests.deps.json"));
            start.ArgumentList.Add(candidatePath);
            foreach (var argument in arguments)
            {
                start.ArgumentList.Add(argument);
            }

            using var process = Process.Start(start) ??
                throw new AssertFailedException(
                    "The generated Console process did not start.");
            var standardOutput = process.StandardOutput.ReadToEndAsync();
            var standardError = process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();
            return (
                process.ExitCode,
                await standardOutput,
                await standardError);
        }
        finally
        {
            File.Delete(candidatePath);
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
