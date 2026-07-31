using System.Security.Cryptography;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
public sealed class CSharpBuildGateCompatibilityMatrixConformanceTests
{
    private static readonly string[] ExpectedClocks =
    [
        "architecture",
        "build-mechanics",
        "capabilities",
        "capability-bundle",
        "consumer-owned-analyzers",
        "disposition",
        "evidence",
        "gate-contracts",
        "operations",
        "planning",
        "public-analyzers",
        "recipes",
        "selection-locks",
        "toolchain",
    ];

    [TestMethod]
    public void ExactMatrixBindsEveryIndependentClockAndMigration()
    {
        var matrix = ReadMatrix();

        Assert.IsTrue(Validate(matrix));
        var clockIds = matrix["clocks"]!.AsArray()
            .Select(clock => clock!["clockId"]!.GetValue<string>())
            .Order(StringComparer.Ordinal)
            .ToArray();
        Assert.AreSequenceEqual(ExpectedClocks, clockIds);

        var migrations = matrix["migrations"]!.AsArray();
        Assert.HasCount(2, migrations);
        foreach (var migration in migrations)
        {
            Assert.IsTrue(
                migration!["humanDecisionRequired"]!.GetValue<bool>());
            Assert.IsTrue(File.Exists(ResolveRepositoryPath(
                migration["manifest"]!.GetValue<string>())));
        }
    }

    [TestMethod]
    public void MixedPartialStaleAndFloatingSelectionsFailClosed()
    {
        var partial = ReadMatrix();
        partial["clocks"]!.AsArray().RemoveAt(0);
        Assert.IsFalse(Validate(partial));

        var stale = ReadMatrix();
        stale["clocks"]!.AsArray()[0]!["sha256"] =
            string.Concat("sha256:", new string('0', 64));
        Assert.IsFalse(Validate(stale));

        var floating = ReadMatrix();
        floating["edges"]!.AsArray()[0]!["acceptedVersion"] = "*";
        Assert.IsFalse(Validate(floating));

        var mixed = ReadMatrix();
        mixed["clocks"]!.AsArray()[0]!["version"] = "2.0.1";
        Assert.IsFalse(Validate(mixed));
    }

    private static JsonObject ReadMatrix() =>
        JsonNode.Parse(File.ReadAllBytes(Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            ".review-sets",
            "reusable-csharp-build-gates",
            "compatibility-version-matrix.json")))!.AsObject();

    private static bool Validate(JsonObject matrix)
    {
        var policy = matrix["selectionPolicy"]?.AsObject();
        if (policy is null ||
            policy.Any(item => item.Value?.GetValue<bool>() != false))
        {
            return false;
        }

        var clockArray = matrix["clocks"]?.AsArray();
        var edgeArray = matrix["edges"]?.AsArray();
        if (clockArray is null || edgeArray is null)
        {
            return false;
        }

        var clocks = new Dictionary<
            string,
            (string Version, string RelativePath, string Digest)>(
                StringComparer.Ordinal);
        foreach (var node in clockArray)
        {
            if (node is not JsonObject value)
            {
                return false;
            }

            var id = Text(value, "clockId");
            var version = Text(value, "version");
            var relativePath = Text(value, "path");
            var digest = Text(value, "sha256");
            if (id is null ||
                version is null ||
                relativePath is null ||
                digest is null ||
                version.Contains('*', StringComparison.Ordinal) ||
                relativePath.Contains('*', StringComparison.Ordinal) ||
                Path.IsPathRooted(relativePath) ||
                relativePath.Split('/').Any(segment =>
                    segment is "." or "..") ||
                !clocks.TryAdd(
                    id,
                    (version, relativePath, digest)))
            {
                return false;
            }

            var fullPath = ResolveRepositoryPath(relativePath);
            if (!File.Exists(fullPath) ||
                !string.Equals(
                    digest,
                    string.Concat(
                        "sha256:",
                        Convert.ToHexStringLower(
                            SHA256.HashData(File.ReadAllBytes(fullPath)))),
                    StringComparison.Ordinal))
            {
                return false;
            }
        }

        if (!clocks.Keys
                .Order(StringComparer.Ordinal)
                .SequenceEqual(ExpectedClocks, StringComparer.Ordinal))
        {
            return false;
        }

        var keys = new HashSet<string>(StringComparer.Ordinal);
        foreach (var node in edgeArray)
        {
            if (node is not JsonObject edge)
            {
                return false;
            }

            var source = Text(edge, "source");
            var target = Text(edge, "target");
            var acceptedVersion = Text(edge, "acceptedVersion");
            var acceptedDigest = Text(edge, "acceptedSha256");
            if (source is null ||
                target is null ||
                acceptedVersion is null ||
                acceptedDigest is null ||
                !clocks.ContainsKey(source) ||
                !clocks.TryGetValue(target, out var targetClock) ||
                !keys.Add(string.Concat(source, "->", target)) ||
                !string.Equals(
                    acceptedVersion,
                    string.Concat("[", targetClock.Version, "]"),
                    StringComparison.Ordinal) ||
                !string.Equals(
                    acceptedDigest,
                    targetClock.Digest,
                    StringComparison.Ordinal))
            {
                return false;
            }
        }

        return edgeArray.Count > 0;
    }

    private static string ResolveRepositoryPath(string relativePath)
    {
        const string historicalReviewSetPrefix = "extensions/";
        var livePath = relativePath.StartsWith(
            historicalReviewSetPrefix,
            StringComparison.Ordinal)
            ? string.Concat(
                ".review-sets/",
                relativePath[historicalReviewSetPrefix.Length..])
            : relativePath;
        return Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            livePath.Replace('/', Path.DirectorySeparatorChar));
    }

    private static string? Text(JsonObject value, string property) =>
        value[property]?.GetValue<string>();
}
