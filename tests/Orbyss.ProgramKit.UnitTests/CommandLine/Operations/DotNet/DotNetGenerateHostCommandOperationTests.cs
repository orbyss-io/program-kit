using System.Collections.Immutable;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet;

[TestClass]
public sealed class DotNetGenerateHostCommandOperationTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    [DataRow("api", "docs/openapi.json")]
    [DataRow("console", "docs/open-console.json")]
    [DataRow("worker", "docs/open-worker.json")]
    public async Task HostGenerationUsesOnlyManifestBoundExactInputs(
        string kindValue,
        string expectedDocumentPath)
    {
        if (kindValue == "console")
        {
            await AssertConsoleHostGenerationAsync(expectedDocumentPath);
            return;
        }

        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-host-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var serializer = CreateSerializer();
            var profile = DotNetJsonProfiles.ShellBootstrap.Reference;
            var limits = JsonSerializationLimits.Default;
            var inputBytes = "{}"u8.ToArray();
            var inputDigest = Digest(inputBytes);
            var shell = DotNetTestContractFactory.Shell() with
            {
                InputVersionMapRevision = new ArtifactReference(
                    DotNetTestContractFactory.Id("version-map", "inputs"),
                    new SemanticVersion("1.0.0"),
                    inputDigest),
                InputVersionSelectionRevision = new ArtifactReference(
                    DotNetTestContractFactory.Id("version-selection", "inputs"),
                    new SemanticVersion("1.0.0"),
                    inputDigest),
            };
            var shellBytes = serializer.Write(
                shell,
                profile,
                limits).ToArray();
            var shellRevision = new ArtifactReference(
                DotNetTestContractFactory.Id("shell", "reviewed"),
                new SemanticVersion("1.0.0"),
                Digest(shellBytes));
            var kind = kindValue switch
            {
                "api" => DotNetHostKind.Api,
                "console" => DotNetHostKind.Console,
                "worker" => DotNetHostKind.Worker,
                _ => throw new AssertFailedException("Unsupported test host kind."),
            };
            var documentBytes = kind switch
            {
                DotNetHostKind.Api => serializer.Write(
                    DotNetTestContractFactory.ApiDocument(shell) with
                    {
                        Provenance = DotNetTestContractFactory
                            .ApiDocument(shell)
                            .Provenance with
                        {
                            ShellRevision = shellRevision,
                        },
                    },
                    profile,
                    limits).ToArray(),
                DotNetHostKind.Console => serializer.Write(
                    DotNetTestContractFactory.ConsoleDocument(shell) with
                    {
                        Provenance = DotNetTestContractFactory
                            .ConsoleDocument(shell)
                            .Provenance with
                        {
                            ShellRevision = shellRevision,
                        },
                    },
                    profile,
                    limits).ToArray(),
                DotNetHostKind.Worker => serializer.Write(
                    DotNetTestContractFactory.WorkerDocument(shell) with
                    {
                        Provenance = DotNetTestContractFactory
                            .WorkerDocument(shell)
                            .Provenance with
                        {
                            ShellRevision = shellRevision,
                        },
                    },
                    profile,
                    limits).ToArray(),
                _ => throw new AssertFailedException("Unsupported test host kind."),
            };
            var documentRevision = new ArtifactReference(
                DotNetTestContractFactory.Id("document", kindValue),
                new SemanticVersion("1.0.0"),
                Digest(documentBytes));
            var host = shell.Hosts.Single(candidate =>
                candidate.Kind == kind);
            var manifest = new DotNetArtifactInputManifest(
                "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
                new SemanticVersion("1.0.0"),
                [
                    new DotNetArtifactInputEntry(
                        shell.InputVersionMapRevision,
                        "version-map.json"),
                    new DotNetArtifactInputEntry(
                        shell.InputVersionSelectionRevision,
                        "version-selection.json"),
                    new DotNetArtifactInputEntry(
                        documentRevision,
                        string.Concat("open-", kindValue, ".json")),
                ],
                [
                    new DotNetHostDocumentInput(
                        host.Identity,
                        documentRevision),
                ]);
            var manifestBytes = serializer.Write(
                manifest,
                profile,
                limits).ToArray();
            var shellPath = Path.Combine(root, "shell.json");
            var manifestPath = Path.Combine(root, "artifact-manifest.json");
            await File.WriteAllBytesAsync(
                shellPath,
                shellBytes,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                Path.Combine(root, "version-map.json"),
                inputBytes,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                Path.Combine(root, "version-selection.json"),
                inputBytes,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                Path.Combine(root, string.Concat("open-", kindValue, ".json")),
                documentBytes,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                manifestPath,
                manifestBytes,
                TestContext.CancellationToken);
            var output = Path.Combine(root, "generated");
            TestCommandConsole console = new();
            var application = CommandLineComposition.CreateDefault(console);

            var exitCode = await application.RunAsync(
            [
                "dotnet",
                "generate-host",
                kindValue,
                "--shell",
                shellPath,
                "--host",
                host.Identity.Value,
                "--artifact-manifest",
                manifestPath,
                "--output",
                output,
            ],
            TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.Success, exitCode);
            Assert.IsTrue(File.Exists(Path.Combine(output, "GeneratedHost.csproj")));
            Assert.IsTrue(File.Exists(Path.Combine(output, "shell.lock.json")));
            Assert.IsTrue(File.Exists(
                Path.Combine(
                    output,
                    expectedDocumentPath.Replace('/', Path.DirectorySeparatorChar))));
            GeneratedOutputIntegrityVerifier verifier = new();
            Assert.IsTrue((await verifier.VerifyAsync(
                output,
                TestContext.CancellationToken)).IsValid);
            Assert.IsEmpty(console.StandardError);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task ConsoleRefreshCreatesThenPreservesTheExactGeneratedHost()
    {
        var root = CreateRoot("program-kit-cli-console-refresh-");
        try
        {
            var fixture = await CreateConsoleFixtureAsync(
                root,
                TestContext.CancellationToken);
            var requestPath = Path.Combine(root, "generation-request.json");
            var request = string.Concat(
                """
                {
                  "schemaVersion": "1.0.0",
                  "programKitVersion": "0.1.0-alpha.3",
                  "kind": "console",
                  "shellPath": "shell.json",
                  "hostIdentity": "
                """,
                fixture.Host.Identity.Value,
                """
                ",
                  "artifactManifestPath": "artifact-manifest.json",
                  "outputRoot": "refreshed",
                  "consumerBuild": null
                }

                """);
            await File.WriteAllTextAsync(
                requestPath,
                request,
                new UTF8Encoding(encoderShouldEmitUTF8Identifier: false),
                TestContext.CancellationToken);

            TestCommandConsole firstConsole = new();
            var firstApplication =
                CommandLineComposition.CreateDefault(firstConsole);
            var first = await firstApplication.RunAsync(
                [
                    "dotnet",
                    "refresh-host",
                    "--request",
                    requestPath,
                ],
                TestContext.CancellationToken);
            TestCommandConsole secondConsole = new();
            var secondApplication =
                CommandLineComposition.CreateDefault(secondConsole);
            var second = await secondApplication.RunAsync(
                [
                    "dotnet",
                    "refresh-host",
                    "--request",
                    requestPath,
                ],
                TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.Success, first);
            Assert.AreEqual(CommandExitCode.Success, second);
            Assert.Contains(
                "\"action\":\"create\"",
                Encoding.UTF8.GetString(firstConsole.StandardOutput));
            Assert.Contains(
                "\"action\":\"unchanged\"",
                Encoding.UTF8.GetString(secondConsole.StandardOutput));
            Assert.IsEmpty(firstConsole.StandardError);
            Assert.IsEmpty(secondConsole.StandardError);
            var output = Path.Combine(root, "refreshed");
            GeneratedOutputIntegrityVerifier verifier = new();
            Assert.IsTrue((await verifier.VerifyAsync(
                output,
                TestContext.CancellationToken)).IsValid);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task ConsoleManifestInputFailuresLeaveNoGeneratedOutput()
    {
        var root = CreateRoot("program-kit-cli-console-negative-");
        try
        {
            var fixture = await CreateConsoleFixtureAsync(
                root,
                TestContext.CancellationToken);
            var selected = fixture.Manifest.ConsoleGenerations.Single();
            var staleBinding = selected.BindingRevision with
            {
                Digest = new Sha256Digest(
                    string.Concat("sha256:", new string('f', 64))),
            };
            var mismatchedConsumerPath =
                "references/mismatched-consumer.dll";
            var consumerInput = fixture.Manifest.Inputs.Single(input =>
                input.Revision == selected.ConsumerReferenceAssemblyRevision);
            File.Copy(
                Path.Combine(
                    root,
                    consumerInput.RelativePath.Replace(
                        '/',
                        Path.DirectorySeparatorChar)),
                Path.Combine(
                    root,
                    mismatchedConsumerPath.Replace(
                        '/',
                        Path.DirectorySeparatorChar)));
            var withoutConsumer = selected.CompilationReferenceRevisions
                .Where(revision =>
                    revision != selected.ConsumerReferenceAssemblyRevision)
                .ToImmutableArray();
            var variants = new[]
            {
                (
                    Name: "legacy-contract",
                    Manifest: fixture.Manifest with
                    {
                        Schema =
                            "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
                        Version = new SemanticVersion("1.0.0"),
                        ConsoleGenerations = [],
                    }),
                (
                    Name: "missing-binding",
                    Manifest: fixture.Manifest with
                    {
                        ConsoleGenerations = [],
                    }),
                (
                    Name: "duplicate-binding",
                    Manifest: fixture.Manifest with
                    {
                        ConsoleGenerations = [selected, selected],
                    }),
                (
                    Name: "empty-references",
                    Manifest: fixture.Manifest with
                    {
                        ConsoleGenerations =
                        [
                            selected with
                            {
                                CompilationReferenceRevisions = [],
                            },
                        ],
                    }),
                (
                    Name: "duplicate-references",
                    Manifest: fixture.Manifest with
                    {
                        ConsoleGenerations =
                        [
                            selected with
                            {
                                CompilationReferenceRevisions =
                                [
                                    selected.ConsumerReferenceAssemblyRevision,
                                    selected.ConsumerReferenceAssemblyRevision,
                                ],
                            },
                        ],
                    }),
                (
                    Name: "unordered-references",
                    Manifest: fixture.Manifest with
                    {
                        ConsoleGenerations =
                        [
                            selected with
                            {
                                CompilationReferenceRevisions = selected
                                    .CompilationReferenceRevisions
                                    .Reverse()
                                    .ToImmutableArray(),
                            },
                        ],
                    }),
                (
                    Name: "missing-consumer-reference",
                    Manifest: fixture.Manifest with
                    {
                        ConsoleGenerations =
                        [
                            selected with
                            {
                                CompilationReferenceRevisions =
                                    withoutConsumer,
                            },
                        ],
                    }),
                (
                    Name: "stale-binding",
                    Manifest: fixture.Manifest with
                    {
                        Inputs = ReplaceRevision(
                            fixture.Manifest.Inputs,
                            selected.BindingRevision,
                            staleBinding),
                        ConsoleGenerations =
                        [
                            selected with
                            {
                                BindingRevision = staleBinding,
                            },
                        ],
                    }),
                (
                    Name: "consumer-path-mismatch",
                    Manifest: fixture.Manifest with
                    {
                        Inputs = ReplacePath(
                            fixture.Manifest.Inputs,
                            selected.ConsumerReferenceAssemblyRevision,
                            mismatchedConsumerPath),
                    }),
                (
                    Name: "escaping-binding-path",
                    Manifest: fixture.Manifest with
                    {
                        Inputs = ReplacePath(
                            fixture.Manifest.Inputs,
                            selected.BindingRevision,
                            "../outside.json"),
                    }),
            };

            foreach (var variant in variants)
            {
                await WriteManifestAsync(
                    fixture,
                    variant.Manifest,
                    TestContext.CancellationToken);
                var output = Path.Combine(root, variant.Name);
                TestCommandConsole console = new();
                var application =
                    CommandLineComposition.CreateDefault(console);

                var exitCode = await application.RunAsync(
                    GenerateConsoleTokens(fixture, output),
                    TestContext.CancellationToken);

                Assert.AreNotEqual(
                    CommandExitCode.Success,
                    exitCode,
                    variant.Name);
                Assert.IsFalse(Directory.Exists(output), variant.Name);
                Assert.IsFalse(
                    File.Exists(
                        Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts
                            .GeneratedOutputPathPolicy.AnchorPath(output)),
                    variant.Name);
                Assert.IsNotEmpty(console.StandardError, variant.Name);
            }
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task ConsoleColdConsumerInputsCanBeMaterializedExplicitly()
    {
        var requested = Environment.GetEnvironmentVariable(
            "PROGRAM_KIT_CONSOLE_COLD_FIXTURE_ROOT");
        var root = requested ?? Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-console-cold-inputs-",
                Guid.NewGuid().ToString("N")));
        Assert.IsFalse(
            Directory.Exists(root),
            "The explicit Console fixture destination must not already exist.");
        Directory.CreateDirectory(root);
        try
        {
            var fixture = await CreateConsoleFixtureAsync(
                root,
                TestContext.CancellationToken);

            Assert.IsTrue(File.Exists(fixture.ShellPath));
            Assert.IsTrue(File.Exists(fixture.ManifestPath));
            Assert.IsTrue(File.Exists(Path.Combine(root, "open-console.json")));
            Assert.IsTrue(File.Exists(Path.Combine(root, "console-binding.json")));
            Assert.IsNotEmpty(
                Directory.EnumerateFiles(
                    Path.Combine(root, "references"),
                    "*.dll"));
        }
        finally
        {
            if (requested is null)
            {
                Directory.Delete(root, recursive: true);
            }
        }
    }

    private async Task AssertConsoleHostGenerationAsync(
        string expectedDocumentPath)
    {
        var root = CreateRoot("program-kit-cli-console-");
        try
        {
            var fixture = await CreateConsoleFixtureAsync(
                root,
                TestContext.CancellationToken);
            var output = Path.Combine(root, "generated");
            TestCommandConsole console = new();
            var application = CommandLineComposition.CreateDefault(console);

            var exitCode = await application.RunAsync(
                GenerateConsoleTokens(fixture, output),
                TestContext.CancellationToken);

            Assert.AreEqual(
                CommandExitCode.Success,
                exitCode,
                Encoding.UTF8.GetString(console.StandardError));
            Assert.IsTrue(
                File.Exists(Path.Combine(output, "GeneratedHost.csproj")));
            Assert.IsTrue(File.Exists(Path.Combine(output, "shell.lock.json")));
            Assert.IsTrue(
                File.Exists(
                    Path.Combine(
                        output,
                        expectedDocumentPath.Replace(
                            '/',
                            Path.DirectorySeparatorChar))));
            GeneratedOutputIntegrityVerifier verifier = new();
            Assert.IsTrue((await verifier.VerifyAsync(
                output,
                TestContext.CancellationToken)).IsValid);
            Assert.IsEmpty(console.StandardError);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static async Task<(
        ProgramKitJsonSerializer Serializer,
        string ShellPath,
        string ManifestPath,
        DotNetArtifactInputManifestAlpha1 Manifest,
        DotNetHostDefinition Host)> CreateConsoleFixtureAsync(
            string root,
            CancellationToken cancellationToken)
    {
        var serializer = CreateSerializer();
        var profile = DotNetJsonProfiles.ShellBootstrap.Reference;
        var limits = JsonSerializationLimits.Default;
        var inputBytes = "{}"u8.ToArray();
        var inputDigest = Digest(inputBytes);
        var shell = DotNetTestContractFactory.Shell() with
        {
            InputVersionMapRevision = new ArtifactReference(
                DotNetTestContractFactory.Id("version-map", "console-inputs"),
                new SemanticVersion("1.0.0"),
                inputDigest),
            InputVersionSelectionRevision = new ArtifactReference(
                DotNetTestContractFactory.Id(
                    "version-selection",
                    "console-inputs"),
                new SemanticVersion("1.0.0"),
                inputDigest),
        };
        var shellBytes = serializer.Write(
            shell,
            profile,
            limits).ToArray();
        var shellRevision = new ArtifactReference(
            DotNetTestContractFactory.Id("shell", "console-reviewed"),
            new SemanticVersion("1.0.0"),
            Digest(shellBytes));
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        document = document with
        {
            Provenance = document.Provenance with
            {
                ShellRevision = shellRevision,
            },
        };
        var documentBytes = serializer.Write(
            document,
            profile,
            limits).ToArray();
        var documentRevision = new ArtifactReference(
            DotNetTestContractFactory.Id("document", "console"),
            document.DocumentVersion,
            Digest(documentBytes));
        var host = shell.Hosts.Single(candidate =>
            candidate.Kind == DotNetHostKind.Console);
        var consumerSource =
            typeof(MetadataFixtureRequest).Assembly.Location;
        const string consumerRelative =
            "references/0000-consumer-contracts.dll";
        var consumerBytes = await File.ReadAllBytesAsync(
            consumerSource,
            cancellationToken);
        var consumerRevision = new ArtifactReference(
            DotNetTestContractFactory.Id("assembly", "console-consumer"),
            new SemanticVersion("1.0.0"),
            Digest(consumerBytes));
        var binding = DotNetConsoleBindingTestFactory.MetadataBinding(
            document,
            consumerSource) with
        {
            OpenConsoleDocumentRevision = documentRevision,
            ConsumerProject = DotNetConsoleBindingTestFactory.MetadataBinding(
                    document,
                    consumerSource)
                .ConsumerProject with
            {
                RelativeReferenceAssemblyPath = consumerRelative,
            },
        };
        var bindingBytes = serializer.Write(
            binding,
            profile,
            limits).ToArray();
        var bindingRevision = new ArtifactReference(
            DotNetTestContractFactory.Id("binding", "console"),
            binding.Version,
            Digest(bindingBytes));
        var inputs = ImmutableArray.CreateBuilder<DotNetArtifactInputEntry>();
        inputs.Add(
            new DotNetArtifactInputEntry(
                shell.InputVersionMapRevision,
                "version-map.json"));
        inputs.Add(
            new DotNetArtifactInputEntry(
                shell.InputVersionSelectionRevision,
                "version-selection.json"));
        inputs.Add(
            new DotNetArtifactInputEntry(
                documentRevision,
                "open-console.json"));
        inputs.Add(
            new DotNetArtifactInputEntry(
                bindingRevision,
                "console-binding.json"));
        var compilationRevisions =
            ImmutableArray.CreateBuilder<ArtifactReference>();
        var referenceSources = ConsoleCompilationReferencePaths(
            consumerSource);
        var referenceIndex = 0;
        foreach (var source in referenceSources)
        {
            ArtifactReference revision;
            string relative;
            if (string.Equals(
                    source,
                    consumerSource,
                    StringComparison.OrdinalIgnoreCase))
            {
                revision = consumerRevision;
                relative = consumerRelative;
            }
            else
            {
                referenceIndex++;
                var bytes = await File.ReadAllBytesAsync(
                    source,
                    cancellationToken);
                revision = new ArtifactReference(
                    DotNetTestContractFactory.Id(
                        "assembly",
                        string.Concat(
                            "console-reference-",
                            referenceIndex.ToString(
                                "D4",
                                CultureInfo.InvariantCulture))),
                    new SemanticVersion("1.0.0"),
                    Digest(bytes));
                relative = string.Concat(
                    "references/",
                    referenceIndex.ToString(
                        "D4",
                        CultureInfo.InvariantCulture),
                    "-",
                    Path.GetFileName(source));
            }

            var destination = Path.Combine(
                root,
                relative.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(
                Path.GetDirectoryName(destination) ??
                throw new InvalidDataException(
                    "A Console reference destination has no parent."));
            File.Copy(source, destination);
            inputs.Add(new DotNetArtifactInputEntry(revision, relative));
            compilationRevisions.Add(revision);
        }

        var orderedReferences = compilationRevisions
            .OrderBy(ExactReferenceKey, StringComparer.Ordinal)
            .ToImmutableArray();
        var manifest = new DotNetArtifactInputManifestAlpha1(
            "pkid:schema:program-kit:dotnet-artifact-input-manifest@0.1.0-alpha.1",
            new SemanticVersion("0.1.0-alpha.1"),
            inputs.ToImmutable(),
            [new DotNetHostDocumentInput(host.Identity, documentRevision)],
            [
                new DotNetConsoleGenerationInputBinding(
                    host.Identity,
                    bindingRevision,
                    consumerRevision,
                    orderedReferences),
            ]);
        var shellPath = Path.Combine(root, "shell.json");
        var manifestPath = Path.Combine(root, "artifact-manifest.json");
        await File.WriteAllBytesAsync(
            shellPath,
            shellBytes,
            cancellationToken);
        await File.WriteAllBytesAsync(
            Path.Combine(root, "version-map.json"),
            inputBytes,
            cancellationToken);
        await File.WriteAllBytesAsync(
            Path.Combine(root, "version-selection.json"),
            inputBytes,
            cancellationToken);
        await File.WriteAllBytesAsync(
            Path.Combine(root, "open-console.json"),
            documentBytes,
            cancellationToken);
        await File.WriteAllBytesAsync(
            Path.Combine(root, "console-binding.json"),
            bindingBytes,
            cancellationToken);
        var fixture = (
            Serializer: serializer,
            ShellPath: shellPath,
            ManifestPath: manifestPath,
            Manifest: manifest,
            Host: host);
        await WriteManifestAsync(
            fixture,
            manifest,
            cancellationToken);
        return fixture;
    }

    private static IEnumerable<string> ConsoleCompilationReferencePaths(
        string consumerAssemblyPath)
    {
        var trusted =
            AppContext.GetData("TRUSTED_PLATFORM_ASSEMBLIES") as string ??
            throw new InvalidOperationException(
                "Trusted platform assemblies are unavailable.");
        var outputNames = new[]
        {
            "CShells.Abstractions.dll",
            "Microsoft.Extensions.DependencyInjection.Abstractions.dll",
            "Microsoft.Extensions.DependencyInjection.dll",
            "Spectre.Console.Ansi.dll",
            "Spectre.Console.Cli.dll",
            "Spectre.Console.dll",
        };
        return trusted
            .Split(
                Path.PathSeparator,
                StringSplitOptions.RemoveEmptyEntries)
            .Concat(
                outputNames.Select(name =>
                    Path.Combine(AppContext.BaseDirectory, name)))
            .Append(consumerAssemblyPath)
            .Where(File.Exists)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Order(StringComparer.Ordinal);
    }

    private static IReadOnlyList<string> GenerateConsoleTokens(
        (
            ProgramKitJsonSerializer Serializer,
            string ShellPath,
            string ManifestPath,
            DotNetArtifactInputManifestAlpha1 Manifest,
            DotNetHostDefinition Host
        ) fixture,
        string output) =>
        [
            "dotnet",
            "generate-host",
            "console",
            "--shell",
            fixture.ShellPath,
            "--host",
            fixture.Host.Identity.Value,
            "--artifact-manifest",
            fixture.ManifestPath,
            "--output",
            output,
        ];

    private static async Task WriteManifestAsync(
        (
            ProgramKitJsonSerializer Serializer,
            string ShellPath,
            string ManifestPath,
            DotNetArtifactInputManifestAlpha1 Manifest,
            DotNetHostDefinition Host
        ) fixture,
        DotNetArtifactInputManifestAlpha1 manifest,
        CancellationToken cancellationToken)
    {
        var bytes = fixture.Serializer.Write(
            manifest,
            DotNetJsonProfiles.ShellBootstrap.Reference,
            JsonSerializationLimits.Default);
        await File.WriteAllBytesAsync(
            fixture.ManifestPath,
            bytes.ToArray(),
            cancellationToken);
    }

    private static ImmutableArray<DotNetArtifactInputEntry> ReplaceRevision(
        ImmutableArray<DotNetArtifactInputEntry> inputs,
        ArtifactReference current,
        ArtifactReference replacement) =>
        inputs
            .Select(input =>
                input.Revision == current
                    ? input with
                    {
                        Revision = replacement,
                    }
                    : input)
            .ToImmutableArray();

    private static ImmutableArray<DotNetArtifactInputEntry> ReplacePath(
        ImmutableArray<DotNetArtifactInputEntry> inputs,
        ArtifactReference revision,
        string replacement) =>
        inputs
            .Select(input =>
                input.Revision == revision
                    ? input with
                    {
                        RelativePath = replacement,
                    }
                    : input)
            .ToImmutableArray();

    private static string ExactReferenceKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

    private static string CreateRoot(string prefix)
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(prefix, Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        return root;
    }

    private static ProgramKitJsonSerializer CreateSerializer()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder jsonBuilder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(jsonBuilder);
        return new ProgramKitJsonSerializer(
            jsonBuilder.Freeze(),
            new ProgramKitJsonCanonicalizer());
    }

    private static Sha256Digest Digest(ReadOnlySpan<byte> content) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(
                System.Security.Cryptography.SHA256.HashData(content))));
}
