using System.Collections.Immutable;
using System.Net;
using System.Net.Sockets;
using System.Text;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Processes;
using Orbyss.ProgramKit.ConformanceTests.Infrastructure;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Clients;

[TestClass]
[DoNotParallelize]
public sealed class KiotaForeignClientConformanceTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task PinnedLocalToolProducesIdenticalLockedClientTrees()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-kiota-conformance-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            CommandFileSystem fileSystem = new();
            var generator = new KiotaForeignClientGenerator(
                fileSystem,
                new CommandProcessRunner(),
                new KiotaToolPackageMaterializer(fileSystem));
            var input = Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                "tests",
                "Orbyss.ProgramKit.ConformanceTests",
                "Fixtures",
                "KiotaForeignClient",
                "foreign-api.openapi.json");
            var manifest = Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                ".config",
                "dotnet-tools.json");
            var package = ResolveKiotaPackage();

            var first = await generator.GenerateAsync(
                Request(input, Path.Combine(root, "first"), manifest, package),
                TestContext.CancellationToken);
            var second = await generator.GenerateAsync(
                Request(input, Path.Combine(root, "second"), manifest, package),
                TestContext.CancellationToken);

            Assert.AreEqual(first.InputDigest, second.InputDigest);
            Assert.AreEqual(first.LockDigest, second.LockDigest);
            Assert.AreEqual(
                first.GeneratedTreeDigest,
                second.GeneratedTreeDigest);
            Assert.AreSequenceEqual(first.Files, second.Files);
            Assert.IsTrue(first.Files.Any(static file =>
                file.RelativePath == "kiota-lock.json"));
            Assert.IsTrue(first.Files.Any(static file =>
                file.RelativePath == "program-kit.client-generation.json"));
            Assert.HasCount(8, first.RuntimeDependencies);
            await BuildAndCallFixtureAsync(
                first.OutputRoot,
                root,
                TestContext.CancellationToken);
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    private static KiotaForeignClientGenerationRequest Request(
        string input,
        string output,
        string manifest,
        string package) =>
        new(
            input,
            output,
            manifest,
            package,
            "Orbyss.ProgramKit.ForeignClientFixture",
            "ForeignApiClient",
            [],
            []);

    private static string ResolveKiotaPackage() =>
        ExternalPackageArchives.EnsureDownloaded(
            "Microsoft.OpenApi.Kiota",
            "1.34.1");

    private static async Task BuildAndCallFixtureAsync(
        string generatedRoot,
        string root,
        CancellationToken cancellationToken)
    {
        var consumerRoot = Path.Combine(root, "consumer");
        Directory.CreateDirectory(consumerRoot);
        var projectPath = Path.Combine(
            consumerRoot,
            "KiotaForeignClientConsumer.csproj");
        await File.WriteAllTextAsync(
            projectPath,
            ConsumerProject(),
            cancellationToken);
        await File.WriteAllTextAsync(
            Path.Combine(consumerRoot, "Program.cs"),
            ConsumerProgram(),
            cancellationToken);
        var nugetConfig = Path.Combine(consumerRoot, "NuGet.Config");
        await File.WriteAllTextAsync(
            nugetConfig,
            ConsumerNuGetConfig(),
            cancellationToken);

        var processRunner = new CommandProcessRunner();
        var environment = ImmutableDictionary<string, string>.Empty
            .Add("DOTNET_CLI_HOME", Path.Combine(root, "consumer-dotnet-home"))
            .Add("DOTNET_CLI_TELEMETRY_OPTOUT", "1")
            .Add("DOTNET_NOLOGO", "1")
            .Add("NUGET_HTTP_CACHE_PATH", Path.Combine(root, "nuget-http-cache"))
            .Add("NUGET_PACKAGES", Path.Combine(root, "nuget-packages"));
        var restore = await processRunner.RunAsync(
            new CommandProcessRequest(
                "dotnet",
                consumerRoot,
                [
                    "restore",
                    projectPath,
                    "--configfile",
                    nugetConfig,
                    "--force-evaluate",
                ],
                environment),
            cancellationToken);
        Assert.AreEqual(
            0,
            restore.ExitCode,
            string.Concat(restore.StandardError, restore.StandardOutput));

        using TcpListener listener = new(IPAddress.Loopback, 0);
        listener.Start();
        var endpoint = (IPEndPoint)listener.LocalEndpoint;
        using var fixtureCancellation =
            CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        fixtureCancellation.CancelAfter(TimeSpan.FromSeconds(180));
        var server = ServeOneRequestAsync(
            listener,
            fixtureCancellation.Token);
        var run = await processRunner.RunAsync(
            new CommandProcessRequest(
                "dotnet",
                consumerRoot,
                [
                    "run",
                    "--no-restore",
                    "--project",
                    projectPath,
                    "--configuration",
                    "Release",
                    "--",
                    string.Concat("http://127.0.0.1:", endpoint.Port),
                ],
                environment),
            fixtureCancellation.Token);
        var observedRequest = await server;
        Assert.AreEqual(
            0,
            run.ExitCode,
            string.Concat(run.StandardError, run.StandardOutput));
        Assert.Contains("kiota-fixture-ok", run.StandardOutput);
        Assert.AreEqual(
            "GET /widgets/widget-42 HTTP/1.1",
            observedRequest.RequestLine);
        Assert.IsFalse(observedRequest.HasAuthorizationHeader);

        var provenance = await File.ReadAllTextAsync(
            Path.Combine(
                generatedRoot,
                "program-kit.client-generation.json"),
            cancellationToken);
        Assert.Contains(
            "\"inputOwnership\": \"foreign\"",
            provenance);
        Assert.Contains(
            "\"package\": \"Microsoft.Kiota.Bundle\"",
            provenance);
    }

    private static async Task<(string? RequestLine, bool HasAuthorizationHeader)>
        ServeOneRequestAsync(
        TcpListener listener,
        CancellationToken cancellationToken)
    {
        using var client = await listener.AcceptTcpClientAsync(
            cancellationToken);
        await using var stream = client.GetStream();
        using StreamReader reader = new(
            stream,
            Encoding.ASCII,
            detectEncodingFromByteOrderMarks: false,
            leaveOpen: true);
        var requestLine = await reader.ReadLineAsync(cancellationToken);
        string? header;
        var hasAuthorizationHeader = false;
        do
        {
            header = await reader.ReadLineAsync(cancellationToken);
            hasAuthorizationHeader |= header?.StartsWith(
                "Authorization:",
                StringComparison.OrdinalIgnoreCase) is true;
        }
        while (!string.IsNullOrEmpty(header));

        const string body =
            """{"id":"widget-42","name":"Deterministic widget"}""";
        var bodyBytes = Encoding.UTF8.GetBytes(body);
        var headers = Encoding.ASCII.GetBytes(
            string.Concat(
                "HTTP/1.1 200 OK\r\n",
                "Content-Type: application/json\r\n",
                "Content-Length: ",
                bodyBytes.Length.ToString(
                    System.Globalization.CultureInfo.InvariantCulture),
                "\r\n",
                "Connection: close\r\n",
                "\r\n"));
        await stream.WriteAsync(headers, cancellationToken);
        await stream.WriteAsync(bodyBytes, cancellationToken);
        await stream.FlushAsync(cancellationToken);
        return (requestLine, hasAuthorizationHeader);
    }

    private static string ConsumerProject() =>
        """
        <Project Sdk="Microsoft.NET.Sdk">
          <PropertyGroup>
            <OutputType>Exe</OutputType>
            <TargetFramework>net10.0</TargetFramework>
            <LangVersion>14.0</LangVersion>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
            <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
            <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
            <NuGetAudit>true</NuGetAudit>
            <NuGetAuditMode>all</NuGetAuditMode>
            <NuGetAuditLevel>low</NuGetAuditLevel>
          </PropertyGroup>
          <ItemGroup>
            <PackageReference Include="Microsoft.Kiota.Bundle" Version="[2.0.0]" />
            <Compile Include="../first/**/*.cs" LinkBase="Generated" />
          </ItemGroup>
        </Project>
        """;

    private static string ConsumerProgram() =>
        """
        using Microsoft.Kiota.Abstractions.Authentication;
        using Microsoft.Kiota.Http.HttpClientLibrary;
        using Orbyss.ProgramKit.ForeignClientFixture;

        var adapter = new HttpClientRequestAdapter(
            new AnonymousAuthenticationProvider())
        {
            BaseUrl = args[0],
        };
        var client = new ForeignApiClient(adapter);
        var widget = await client.Widgets["widget-42"].GetAsync();
        if (widget?.Id != "widget-42" ||
            widget.Name != "Deterministic widget")
        {
            throw new InvalidDataException("The generated client response is invalid.");
        }

        Console.WriteLine("kiota-fixture-ok");
        """;

    private static string ConsumerNuGetConfig() =>
        """
        <?xml version="1.0" encoding="utf-8"?>
        <configuration>
          <packageSources>
            <clear />
            <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />
          </packageSources>
          <auditSources>
            <clear />
            <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />
          </auditSources>
          <packageSourceMapping>
            <clear />
            <packageSource key="nuget.org">
              <package pattern="Microsoft.*" />
              <package pattern="Azure.*" />
              <package pattern="System.*" />
              <package pattern="Std.UriTemplate" />
            </packageSource>
          </packageSourceMapping>
        </configuration>
        """;

    private static void DeleteTemporaryRoot(string root)
    {
        var fullRoot = Path.GetFullPath(root);
        var temporaryRoot = Path.GetFullPath(Path.GetTempPath());
        Assert.IsTrue(
            fullRoot.StartsWith(
                temporaryRoot,
                OperatingSystem.IsWindows()
                    ? StringComparison.OrdinalIgnoreCase
                    : StringComparison.Ordinal));
        if (Directory.Exists(fullRoot))
        {
            Directory.Delete(fullRoot, recursive: true);
        }
    }
}
