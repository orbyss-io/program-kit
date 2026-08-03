using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;

namespace Orbyss.ProgramKit.Tests;

internal sealed class SpecKitAdapterPackagedWorkspace : IDisposable
{
    private SpecKitAdapterPackagedWorkspace(string root, Dictionary<string, string> environment, string adapterDll, SpecKitAdapterScenario scenario)
    {
        Root = root;
        Environment = environment;
        AdapterDll = adapterDll;
        Scenario = scenario;
    }

    public string Root { get; }
    public IReadOnlyDictionary<string, string> Environment { get; }
    public string AdapterDll { get; }
    public SpecKitAdapterScenario Scenario { get; }

    public static SpecKitAdapterPackagedWorkspace Create(bool includeDependencyMirror)
    {
        SpecKitAdapterPackagedWorkspace workspace = CreateClean(SpecKitAdapterFixture.ReferenceStatus, includeDependencyMirror);
        try
        {
            workspace.InitializeFactory();
            workspace.StageReviewedFixture();
            return workspace;
        }
        catch
        {
            workspace.Dispose();
            throw;
        }
    }

    public static SpecKitAdapterPackagedWorkspace CreateClean(SpecKitAdapterScenario scenario, bool includeDependencyMirror)
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            Dictionary<string, string> environment = IsolatedEnvironment(workspace);
            string feed = Path.Combine(workspace, ".program-kit", "feed");
            Directory.CreateDirectory(feed);
            string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent?.Name ?? throw new InvalidOperationException("Test configuration unavailable.");
            string project = Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "ProgramKit.Cli.csproj");
            AssertSucceeded(Run("dotnet", TestRepository.Root, environment, "pack", project, "--configuration", configuration, "--no-build", "--no-restore", "--output", feed));
            StageCliDependencyPackages(project, feed);
            string nugetConfig = WriteNuGetConfig(workspace, feed);
            WriteToolManifest(workspace);
            AssertSucceeded(Run("dotnet", workspace, environment, "tool", "restore", "--configfile", nugetConfig, "--no-cache"));

            if (includeDependencyMirror) CopyDirectory(Path.Combine(TestRepository.Root, "artifacts", "dependency-mirror"), Path.Combine(workspace, "dependencies"));
            string adapterDll = StageAdapter(workspace, configuration);
            return new SpecKitAdapterPackagedWorkspace(workspace, environment, adapterDll, scenario);
        }
        catch
        {
            TestRepository.DeleteWorkspace(workspace);
            throw;
        }
    }

    public ProcessResult RunAdapter(string operation, string requestPath) =>
        Run("dotnet", Root, Environment, AdapterDll, operation, "--workspace", Root, "--request", requestPath, "--format", "json");

    public ProcessResult RunProgramKit(params string[] arguments)
    {
        List<string> command = new() { "tool", "run", "program-kit", "--" };
        command.AddRange(arguments);
        return Run("dotnet", Root, Environment, command.ToArray());
    }

    public void InitializeFactory()
    {
        string initRequest = WriteJson("requests/init.json", WorkspaceBootstrapFixture.InitRequest());
        AssertSucceeded(RunProgramKit("init", "--workspace", Root, "--request", initRequest, "--format", "json"));
        string baseRequest = WriteJson("requests/restore-base.json", WorkspaceBootstrapFixture.RestoreRequest("base"));
        AssertSucceeded(RunProgramKit("restore", "--workspace", Root, "--request", baseRequest, "--format", "json"));
        string catalogRequest = WriteJson("requests/catalog.json", WorkspaceBootstrapFixture.CatalogRequest());
        AssertSucceeded(RunProgramKit("catalog", "list", "--workspace", Root, "--request", catalogRequest, "--format", "json"));
        File.WriteAllBytes(Path.Combine(Root, "program-kit.yaml"), CanonicalJson.Encode(WorkspaceBootstrapFixture.ExactFactoryManifest()));
        string factoryRequest = WriteJson("requests/restore-factory.json", WorkspaceBootstrapFixture.RestoreRequest("factory"));
        AssertSucceeded(RunProgramKit("restore", "--workspace", Root, "--request", factoryRequest, "--format", "json"));
    }

    public void StageConsumerIntent() => SpecKitAdapterFixture.StageConsumerIntent(Root, Scenario);

    public void StageReviewedHandoff() => SpecKitAdapterFixture.StageReviewedHandoff(Root, Scenario);

    public void StageReviewedFixture() => SpecKitAdapterFixture.StageReviewedFixture(Root, Scenario);

    public string WriteAdapterRequest(string operation, JsonObject? grant = null, string? requestedEffect = null)
    {
        JsonObject request = SpecKitAdapterFixture.AdapterRequest(Scenario, operation);
        if (requestedEffect is not null) request["requestedEffect"] = requestedEffect;
        if (grant is not null) request["grant"] = grant.DeepClone();
        return WriteJson($"requests/adapter-{operation}.json", request);
    }

    public string WriteJson(string logicalPath, JsonObject document)
    {
        string path = Path.Combine(Root, logicalPath.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllBytes(path, CanonicalJson.Encode(document));
        return path;
    }

    public JsonObject Read(string logicalPath) => CanonicalJson.Parse(File.ReadAllBytes(Path.Combine(Root, logicalPath.Replace('/', Path.DirectorySeparatorChar)))).AsObject();

    public JsonObject ApproveCommittedHandoff()
    {
        string handoffPath = Path.Combine(Root, "specs", Scenario.FeatureKey, "program-kit", "handoff.yaml");
        JsonObject handoff = RestrictedYaml.Parse(File.ReadAllText(handoffPath));
        handoff["maximumEffect"] = "committed";
        JsonObject trace = handoff["trace"]!.AsArray().OfType<JsonObject>().Single(item => item["targetPointer"]!.GetValue<string>() == "/maximumEffect");
        trace["observedValue"] = "committed";
        File.WriteAllBytes(handoffPath, CanonicalJson.Encode(handoff));
        return RebindReview();
    }

    public JsonObject RebindReview()
    {
        string handoffPath = Path.Combine(Root, "specs", Scenario.FeatureKey, "program-kit", "handoff.yaml");
        BoundHandoff rebound = new HandoffBinder().Bind(RestrictedYaml.Parse(File.ReadAllText(handoffPath)), requireComplete: true);

        string reviewPath = Path.Combine(Root, "specs", Scenario.FeatureKey, "program-kit", "handoff-review.json");
        JsonObject review = CanonicalJson.Parse(File.ReadAllBytes(reviewPath)).AsObject();
        review["handoff"]!["digest"] = rebound.Digest;
        review["digest"] = null;
        review.Remove("digest");
        review["digest"] = CanonicalDocument.Digest(review);
        File.WriteAllBytes(reviewPath, CanonicalDocument.Encode(review));
        return review;
    }

    public JsonObject RecordAuthority(string effect)
    {
        string preparationPath = $"specs/{Scenario.FeatureKey}/program-kit/generated/results/prepare.json";
        JsonObject preparationReference = Artifact(preparationPath, "preparation-result", $"{Scenario.ArtifactPrefix}-preparation", "application/vnd.program-kit.operation-result+json", "generated-owned");
        JsonObject proposal = Read(preparationPath)["payload"]!["proposal"]!.AsObject();
        string reviewPath = $"specs/{Scenario.FeatureKey}/program-kit/handoff-review.json";
        JsonObject decision = new()
        {
            ["schema"] = "program-kit.authority-decision-record/v1",
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["proposal"] = preparationReference.DeepClone(),
            ["reviewer"] = "joey-orbyss",
            ["decision"] = "approve",
            ["subjects"] = proposal["subjects"]!.DeepClone(),
            ["operations"] = new JsonArray("construct"),
            ["effects"] = new JsonArray(effect),
            ["conditions"] = new JsonArray(),
            ["validity"] = new JsonObject { ["notBefore"] = "2026-01-01T00:00:00Z", ["notAfter"] = "2027-01-01T00:00:00Z" },
            ["provenance"] = Artifact(reviewPath, "handoff-review", $"{Scenario.ArtifactPrefix}-handoff", "application/json", "consumer-owned"),
            ["recordedAt"] = "2026-08-02T10:10:00Z",
        };
        string decisionPath = $".program-kit/authority/{Scenario.ArtifactPrefix}.decision.json";
        WriteJson(decisionPath, decision);
        JsonObject request = new()
        {
            ["schema"] = "program-kit.authority-record-request/v1",
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["proposal"] = preparationReference,
            ["decision"] = Artifact(decisionPath, "authority-decision", $"{Scenario.ArtifactPrefix}-decision", "application/json", "consumer-owned"),
            ["grantPath"] = $".program-kit/authority/{Scenario.ArtifactPrefix}.grant.json",
            ["revocationPath"] = $".program-kit/authority/{Scenario.ArtifactPrefix}.revocations.json",
        };
        string requestPath = WriteJson("requests/authority-record.json", request);
        ProcessResult recorded = RunProgramKit("authority", "record", "--workspace", Root, "--request", requestPath, "--format", "json");
        AssertSucceeded(recorded);
        JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, recorded.Output);
        return (JsonObject)result["payload"]!["grant"]!.DeepClone();
    }

    public void Dispose() => TestRepository.DeleteWorkspace(Root);

    public static JsonObject AssertAdapterResult(ProcessResult result, string outcome, string effect)
    {
        JsonObject document = CanonicalDocument.Parse(System.Text.Encoding.UTF8.GetBytes(result.Output)).AsObject();
        AdapterSchemaValidator.Validate("adapter-result.schema.json", document);
        Assert.AreEqual(outcome, document["outcome"]!.GetValue<string>(), result.Output + result.Error);
        Assert.AreEqual(effect, document["effectState"]!.GetValue<string>(), result.Output + result.Error);
        return document;
    }

    public static void AssertSucceeded(ProcessResult result) => Assert.AreEqual(0, result.ExitCode, result.Output + result.Error);

    private static void StageCliDependencyPackages(string project, string feed)
    {
        string assetsPath = Path.Combine(Path.GetDirectoryName(project)!, "obj", "project.assets.json");
        JsonObject assets = JsonNode.Parse(File.ReadAllBytes(assetsPath))!.AsObject();
        string[] packageFolders = assets["packageFolders"]!.AsObject().Select(static item => item.Key).ToArray();
        foreach ((string library, JsonNode? metadata) in assets["libraries"]!.AsObject())
        {
            if (metadata?["type"]?.GetValue<string>() != "package") continue;
            string relative = metadata["path"]?.GetValue<string>() ?? library.Replace('/', Path.DirectorySeparatorChar).ToLowerInvariant();
            string? package = packageFolders
                .Select(folder => Path.Combine(folder, relative.Replace('/', Path.DirectorySeparatorChar)))
                .Where(Directory.Exists)
                .SelectMany(directory => Directory.EnumerateFiles(directory, "*.nupkg", SearchOption.TopDirectoryOnly))
                .SingleOrDefault();
            if (package is null) throw new InvalidOperationException($"The acquired package archive for {library} is unavailable.");
            File.Copy(package, Path.Combine(feed, Path.GetFileName(package)), overwrite: true);
        }
    }

    private static string StageAdapter(string workspace, string configuration)
    {
        string source = Path.Combine(TestRepository.Root, "src", "ProgramKit.SpecKitAdapter", "bin", configuration, "net10.0");
        string destination = Path.Combine(workspace, ".specify", "extensions", "orbyss-program-kit-adapter", "tools");
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source)) File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        string dll = Path.Combine(destination, "program-kit-spec-kit-adapter.dll");
        Assert.IsTrue(File.Exists(dll));
        return dll;
    }

    private static string WriteNuGetConfig(string workspace, string feed)
    {
        string path = Path.Combine(workspace, "NuGet.Config");
        string escaped = SecurityElement.Escape(feed) ?? throw new InvalidOperationException("Feed path could not be encoded.");
        File.WriteAllText(path, $"<?xml version=\"1.0\" encoding=\"utf-8\"?><configuration><packageSources><clear/><add key=\"local\" value=\"{escaped}\"/></packageSources></configuration>");
        return path;
    }

    private static void WriteToolManifest(string workspace)
    {
        string path = Path.Combine(workspace, ".config", "dotnet-tools.json");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        JsonObject manifest = new()
        {
            ["version"] = 1,
            ["isRoot"] = true,
            ["tools"] = new JsonObject
            {
                ["orbyss.programkit.cli"] = new JsonObject
                {
                    ["version"] = "1.0.0-alpha.2",
                    ["commands"] = new JsonArray("program-kit"),
                    ["rollForward"] = false,
                },
            },
        };
        File.WriteAllBytes(path, CanonicalJson.Encode(manifest));
    }

    private static Dictionary<string, string> IsolatedEnvironment(string workspace)
    {
        string state = Path.Combine(workspace, ".program-kit", "dotnet-state");
        Directory.CreateDirectory(state);
        Dictionary<string, string> environment = new(StringComparer.Ordinal)
        {
            ["DOTNET_CLI_HOME"] = Path.Combine(state, "home"),
            ["NUGET_PACKAGES"] = Path.Combine(state, "packages"),
            ["NUGET_HTTP_CACHE_PATH"] = Path.Combine(state, "http-cache"),
            ["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1",
            ["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1",
            ["DOTNET_NOLOGO"] = "1",
            ["DOTNET_CLI_USE_MSBUILD_SERVER"] = "0",
            ["MSBUILDDISABLENODEREUSE"] = "1",
            ["NUGET_XMLDOC_MODE"] = "skip",
            ["http_proxy"] = "http://127.0.0.1:1",
            ["https_proxy"] = "http://127.0.0.1:1",
        };
        environment[OperatingSystem.IsWindows() ? "APPDATA" : "XDG_CONFIG_HOME"] = Path.Combine(state, "config");
        return environment;
    }

    private static ProcessResult Run(string executable, string workingDirectory, IReadOnlyDictionary<string, string> environment, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        foreach ((string key, string value) in environment) start.Environment[key] = value;
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Could not start acceptance process.");
        Task<string> output = process.StandardOutput.ReadToEndAsync();
        Task<string> error = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(120_000))
        {
            process.Kill(entireProcessTree: true);
            process.WaitForExit();
            throw new TimeoutException("Acceptance process exceeded two minutes.");
        }

        return new ProcessResult(process.ExitCode, output.GetAwaiter().GetResult(), error.GetAwaiter().GetResult());
    }

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source)) File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        foreach (string directory in Directory.EnumerateDirectories(source)) CopyDirectory(directory, Path.Combine(destination, Path.GetFileName(directory)));
    }

    private JsonObject Artifact(string logicalPath, string kind, string name, string mediaType, string ownership)
    {
        byte[] bytes = File.ReadAllBytes(Path.Combine(Root, logicalPath.Replace('/', Path.DirectorySeparatorChar)));
        string digest = Digests.Sha256(bytes);
        return new JsonObject
        {
            ["identity"] = new JsonObject
            {
                ["authority"] = "consumer.reference",
                ["kind"] = kind,
                ["name"] = name,
                ["revision"] = "1.0.0",
                ["digest"] = digest,
            },
            ["mediaType"] = mediaType,
            ["logicalPath"] = logicalPath,
            ["digest"] = digest,
            ["ownership"] = ownership,
        };
    }
}

internal sealed record ProcessResult(int ExitCode, string Output, string Error);
