using System.Security.Cryptography;

namespace Orbyss.ProgramKit.ConformanceTests;

[TestClass]
public sealed class ArtifactVectorConformanceTests
{
    private static readonly IReadOnlyDictionary<string, string> ExpectedDigests =
        new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["official-rfc8785-vectors.json"] =
                "83a6720edbe4c2d58a1e57db4b10cde4a7e1e6ddce607df7da6dc5226ec09c7a",
            ["positive-vectors.json"] =
                "4cd96bd415d27a005739c9fef08b292a6d50ffcf403833b1c0a46587ac5d7dea",
            ["negative-vectors.json"] =
                "d24657f809239bb90f87de37d97edb11d0ac1055ea6c83923653151b530d2f36",
            ["sha256-manifest.json"] =
                "830ba12820fd18f057c156aadc706a6483301615e20a2fde02adf71ab5e904ac",
        };

    [TestMethod]
    public void Rfc8785FixtureBytesCannotDriftSilently()
    {
        var files = ConformanceInputs
            .Files("Schemas", "*.json")
            .Where(path => path.Contains(
                $"{Path.DirectorySeparatorChar}artifacts{Path.DirectorySeparatorChar}" +
                $"fixtures{Path.DirectorySeparatorChar}rfc8785{Path.DirectorySeparatorChar}",
                StringComparison.Ordinal))
            .ToDictionary(
                path => Path.GetFileName(path)
                        ?? throw new InvalidOperationException(
                            string.Concat("Fixture path has no file name: ", path)),
                StringComparer.Ordinal);

        foreach (var expected in ExpectedDigests)
        {
            Assert.IsTrue(files.TryGetValue(expected.Key, out var path), expected.Key);
            var actual = Convert
                .ToHexString(SHA256.HashData(File.ReadAllBytes(path)))
                .ToLowerInvariant();
            Assert.AreEqual(expected.Value, actual, expected.Key);
        }

        var manifest = File.ReadAllText(files["sha256-manifest.json"]);
        foreach (var expected in ExpectedDigests.Where(entry =>
                     !string.Equals(
                         entry.Key,
                         "sha256-manifest.json",
                         StringComparison.Ordinal)))
        {
            StringAssert.Contains(manifest, expected.Key);
            StringAssert.Contains(manifest, string.Concat("sha256:", expected.Value));
        }
    }

    [TestMethod]
    public void OfficialRfc8785SetContainsEveryPublishedAppendixBRow()
    {
        var official = ConformanceInputs
            .Files("Schemas", "official-rfc8785-vectors.json")
            .Single();
        var text = File.ReadAllText(official);

        Assert.AreEqual(28, CountOccurrences(text, "\"id\": "));
        Assert.AreEqual(26, CountOccurrences(text, "\"id\": \"appendix-b-"));
        StringAssert.Contains(text, "\"inputBinary64Hex\": \"0000000000000000\"");
        StringAssert.Contains(text, "\"inputBinary64Hex\": \"43143ff3c1cb0959\"");
    }

    private static int CountOccurrences(string value, string token)
    {
        var count = 0;
        var start = 0;
        while ((start = value.IndexOf(token, start, StringComparison.Ordinal)) >= 0)
        {
            count++;
            start += token.Length;
        }

        return count;
    }
}
