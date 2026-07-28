using System.Security.Cryptography;
using Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;
using Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetConsoleCandidateCompilerTests
{
    [TestMethod]
    public void CandidateCompilesAgainstOnlyExplicitDigestCheckedReferences()
    {
        DotNetConsoleCandidateCompiler sut = new();

        var result = sut.Compile(
            [
                new DotNetConsoleSourceFile(
                    "Commands/Candidate.cs",
                    """
                    namespace GeneratedHost.Commands;

                    /// <summary>Generated compilation candidate.</summary>
                    public sealed class Candidate
                    {
                        /// <summary>Creates the typed consumer request.</summary>
                        public global::Orbyss.ProgramKit.ConsoleContractFixtures.Contracts.MetadataFixtureRequest Create() =>
                            new(
                                "target",
                                1,
                                false,
                                false,
                                8L,
                                1.5M,
                                global::System.Guid.Parse("d2719a8c-3ae5-49b1-a6ab-f57ad42f51ee"),
                                global::System.DateTimeOffset.Parse("2026-01-01T00:00:00.0000000+00:00"),
                                global::System.Collections.Immutable.ImmutableArray<string>.Empty);
                    }
                    """),
            ],
            References(),
            CancellationToken.None);

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(static item => item.Message)));
        Assert.IsNotEmpty(result.AssemblyBytes);
    }

    [TestMethod]
    public void StaleReferenceAndUnsafeSourcePathFailClosed()
    {
        var references = References();
        references = references.SetItem(
            0,
            references[0] with
            {
                Digest = new Sha256Digest(
                    string.Concat("sha256:", new string('f', 64))),
            });
        DotNetConsoleCandidateCompiler sut = new();

        var result = sut.Compile(
            [
                new DotNetConsoleSourceFile(
                    "../Injected.cs",
                    "public sealed class Injected {}"),
            ],
            references,
            CancellationToken.None);

        Assert.IsFalse(result.IsValid);
        Assert.IsGreaterThanOrEqualTo(2, result.Diagnostics.Length);
    }

    [TestMethod]
    public void ScriptDirectiveAndCompileErrorFailClosed()
    {
        DotNetConsoleCandidateCompiler sut = new();

        var result = sut.Compile(
            [
                new DotNetConsoleSourceFile(
                    "Commands/Injected.cs",
                    """
                    #r "unapproved.dll"
                    public sealed class Injected
                    {
                        public MissingType Value { get; }
                    }
                    """),
            ],
            References(),
            CancellationToken.None);

        Assert.IsFalse(result.IsValid);
    }

    private static ImmutableArray<DotNetConsoleCompilationReference> References()
    {
        var trusted = AppContext.GetData("TRUSTED_PLATFORM_ASSEMBLIES") as string ??
            throw new InvalidOperationException(
                "Trusted platform assemblies are unavailable.");
        var paths = trusted
            .Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries)
            .Append(typeof(MetadataFixtureRequest).Assembly.Location)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Order(StringComparer.Ordinal)
            .ToArray();
        return paths
            .Select(static path =>
                new DotNetConsoleCompilationReference(
                    path,
                    new Sha256Digest(
                        string.Concat(
                            "sha256:",
                            Convert.ToHexStringLower(
                                SHA256.HashData(
                                    File.ReadAllBytes(path)))))))
            .ToImmutableArray();
    }
}
