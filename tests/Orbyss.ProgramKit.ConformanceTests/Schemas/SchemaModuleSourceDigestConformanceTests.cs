using System.Security.Cryptography;
using Orbyss.ProgramKit.Architecture.Schemas;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Schemas;
using Orbyss.ProgramKit.Development.Schemas;
using Orbyss.ProgramKit.DotNet.Schemas;
using Orbyss.ProgramKit.OpenConsole.Contracts.Schemas;
using Orbyss.ProgramKit.Operations.Contracts.Schemas;
using Orbyss.ProgramKit.Planning.Schemas;
using Orbyss.ProgramKit.Quality.Schemas;
using Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Schemas;
using Orbyss.ProgramKit.Tasks.Core.Schemas;
using Orbyss.ProgramKit.Tasks.Schedules.Schemas;

namespace Orbyss.ProgramKit.ConformanceTests.Schemas;

[TestClass]
public sealed class SchemaModuleSourceDigestConformanceTests
{
    [TestMethod]
    public void CliSchemaModulePinsMatchCanonicalRepositoryFiles()
    {
        var root = ConformanceInputs.RepositoryRoot;
        List<string> failures = [];
        OperationsSchemaModule operations = new();
        SecretResolutionSchemaModule secretResolution = new();
        (IProgramKitSchemaModule Module, string[] SourceRoots)[] modules =
        [
            (new ArtifactsSchemaModule(), ["schemas/artifacts", "schemas/versioning"]),
            (new ArchitectureSchemaModule(), ["schemas/architecture"]),
            (new QualitySchemaModule(), ["schemas/quality"]),
            (new PlanningSchemaModule(), ["schemas/planning"]),
            (new DevelopmentSchemaModule(), ["schemas/development"]),
            (new SerializationJsonSchemaModule(), ["schemas/serialization"]),
            (new TasksCoreSchemaModule(), ["schemas/tasks"]),
            (new TaskSchedulesSchemaModule(), ["schemas/task-schedules"]),
            (new OpenConsoleSchemaModule(), ["schemas/open-console"]),
            (
                new DotNetSchemaModule(operations, secretResolution),
                ["schemas/dotnet", "schemas/operations", "schemas/secret-resolution"]),
            (new CSharpBuildGateSchemaModule(), ["schemas/csharp-build-gates"]),
        ];

        foreach (var (module, sourceRoots) in modules)
        {
            foreach (var resource in module.Resources)
            {
                var candidates = sourceRoots
                    .Select(sourceRoot => Path.Combine(
                        root,
                        sourceRoot.Replace('/', Path.DirectorySeparatorChar)))
                    .SelectMany(sourceRoot => Directory.EnumerateFiles(
                        sourceRoot,
                        resource.ResourceName,
                        SearchOption.AllDirectories))
                    .Distinct(StringComparer.Ordinal)
                    .ToArray();
                if (candidates.Length != 1)
                {
                    failures.Add(string.Concat(
                        module.Identity.Value,
                        " must resolve ",
                        resource.ResourceName,
                        " to exactly one canonical repository file; found ",
                        candidates.Length,
                        "."));
                    continue;
                }

                var sourceBytes = File.ReadAllBytes(candidates[0]);
                if (sourceBytes.Contains((byte)'\r'))
                {
                    failures.Add(string.Concat(
                        candidates[0],
                        " must use canonical LF bytes before its digest is pinned."));
                }

                var sourceDigest = Digest(sourceBytes);
                if (!string.Equals(
                        resource.SchemaReference.Digest.Value,
                        sourceDigest,
                        StringComparison.Ordinal))
                {
                    failures.Add(string.Concat(
                        resource.SchemaReference.Identity.Value,
                        "@",
                        resource.SchemaReference.Version.Value,
                        " pins ",
                        resource.SchemaReference.Digest.Value,
                        " but canonical repository bytes at ",
                        candidates[0],
                        " are ",
                        sourceDigest,
                        "."));
                }

                using var stream = module.OpenRead(resource.SchemaReference);
                using MemoryStream embeddedBytes = new();
                stream.CopyTo(embeddedBytes);
                var embeddedDigest = Digest(embeddedBytes.ToArray());
                if (!string.Equals(
                        sourceDigest,
                        embeddedDigest,
                        StringComparison.Ordinal))
                {
                    failures.Add(string.Concat(
                        resource.SchemaReference.Identity.Value,
                        "@",
                        resource.SchemaReference.Version.Value,
                        " embeds ",
                        embeddedDigest,
                        " but canonical repository bytes at ",
                        candidates[0],
                        " are ",
                        sourceDigest,
                        "."));
                }
            }
        }

        Assert.HasCount(
            0,
            failures,
            string.Join(Environment.NewLine, failures));
    }

    private static string Digest(byte[] bytes) =>
        string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(bytes)));
}
