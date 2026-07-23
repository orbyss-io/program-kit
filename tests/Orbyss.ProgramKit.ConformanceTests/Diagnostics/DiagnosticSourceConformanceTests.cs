using System.Text.RegularExpressions;

namespace Orbyss.ProgramKit.ConformanceTests.Diagnostics;

[TestClass]
public sealed partial class DiagnosticSourceConformanceTests
{
    [TestMethod]
    public void DomainValidatorsUseCatalogConstantsAndPublishNoLegacyFamilies()
    {
        var domainSources = ConformanceInputs
            .Files("Source", "*.cs")
            .Where(path =>
                path.Contains("Orbyss.ProgramKit.Quality", StringComparison.Ordinal) ||
                path.Contains("Orbyss.ProgramKit.Planning", StringComparison.Ordinal) ||
                path.Contains("Orbyss.ProgramKit.Development", StringComparison.Ordinal))
            .ToArray();

        Assert.IsNotEmpty(domainSources);
        foreach (var path in domainSources)
        {
            var source = File.ReadAllText(path);
            Assert.IsFalse(
                LegacyDiagnosticFamily().IsMatch(source),
                $"Legacy diagnostic family found in {path}.");

            if (path.Contains(
                    $"{Path.DirectorySeparatorChar}Validation{Path.DirectorySeparatorChar}",
                    StringComparison.Ordinal))
            {
                Assert.IsFalse(
                    CanonicalDiagnosticStringLiteral().IsMatch(source),
                    $"Validator diagnostic IDs must come from the public catalog: {path}.");
            }
        }
    }

    [GeneratedRegex(@"PK(?:Q|P|D)[0-9]{3}", RegexOptions.CultureInvariant)]
    private static partial Regex LegacyDiagnosticFamily();

    [GeneratedRegex(
        "\"PK(?:QLT|PLN|DEV)[0-9]{3}\"",
        RegexOptions.CultureInvariant)]
    private static partial Regex CanonicalDiagnosticStringLiteral();
}
