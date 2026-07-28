using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Emit;
using Microsoft.CodeAnalysis.Text;
using Orbyss.ProgramKit.DotNet.Diagnostics;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;

/// <summary>Deterministic in-process Roslyn compiler for isolated candidates.</summary>
public sealed class DotNetConsoleCandidateCompiler :
    IDotNetConsoleCandidateCompiler
{
    /// <inheritdoc />
    public DotNetConsoleCompilationResult Compile(
        ImmutableArray<DotNetConsoleSourceFile> sources,
        ImmutableArray<DotNetConsoleCompilationReference> references,
        CancellationToken cancellationToken)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (sources.IsDefaultOrEmpty || references.IsDefaultOrEmpty)
        {
            Error(
                diagnostics,
                "Candidate sources and exact compilation references are required.",
                string.Empty);
            return Invalid(diagnostics);
        }

        var sourcePaths = new HashSet<string>(StringComparer.Ordinal);
        var syntaxTrees = ImmutableArray.CreateBuilder<SyntaxTree>();
        CSharpParseOptions parseOptions = new(
            LanguageVersion.CSharp14,
            DocumentationMode.Diagnose,
            SourceCodeKind.Regular);
        foreach (var source in sources.OrderBy(
                     static item => item.RelativePath,
                     StringComparer.Ordinal))
        {
            if (source is null ||
                !IsSafeSourcePath(source.RelativePath) ||
                string.IsNullOrEmpty(source.Content) ||
                !sourcePaths.Add(source.RelativePath))
            {
                Error(
                    diagnostics,
                    "Candidate sources require unique safe relative .cs paths and non-empty generated content.",
                    "/sources");
                continue;
            }

            syntaxTrees.Add(
                CSharpSyntaxTree.ParseText(
                    SourceText.From(
                        source.Content,
                        new UTF8Encoding(
                            encoderShouldEmitUTF8Identifier: false),
                        SourceHashAlgorithm.Sha256),
                    parseOptions,
                    source.RelativePath,
                    cancellationToken));
        }

        var referencePaths = new HashSet<string>(
            StringComparer.OrdinalIgnoreCase);
        var metadataReferences = ImmutableArray.CreateBuilder<MetadataReference>();
        foreach (var reference in references.OrderBy(
                     static item => item.Path,
                     StringComparer.Ordinal))
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (reference is null ||
                string.IsNullOrWhiteSpace(reference.Path) ||
                !Path.IsPathFullyQualified(reference.Path) ||
                !File.Exists(reference.Path) ||
                !referencePaths.Add(reference.Path))
            {
                Error(
                    diagnostics,
                    "Compilation references must be unique existing absolute files.",
                    "/references");
                continue;
            }

            try
            {
                var bytes = File.ReadAllBytes(reference.Path);
                var digest = new Sha256Digest(
                    string.Concat(
                        "sha256:",
                        Convert.ToHexStringLower(SHA256.HashData(bytes))));
                if (digest != reference.Digest)
                {
                    Error(
                        diagnostics,
                        "A candidate compilation reference digest is stale or mismatched.",
                        "/references");
                    continue;
                }

                metadataReferences.Add(
                    MetadataReference.CreateFromImage(
                        ImmutableArray.Create(bytes),
                        filePath: reference.Path));
            }
            catch (Exception exception) when (
                exception is IOException or
                    UnauthorizedAccessException or
                    BadImageFormatException)
            {
                Error(
                    diagnostics,
                    "A candidate compilation reference is unreadable or malformed.",
                    "/references");
            }
        }

        if (diagnostics.Count > 0)
        {
            return Invalid(diagnostics);
        }

        CSharpCompilationOptions compilationOptions = new(
            OutputKind.DynamicallyLinkedLibrary,
            optimizationLevel: OptimizationLevel.Release,
            checkOverflow: true,
            allowUnsafe: false,
            platform: Platform.AnyCpu,
            generalDiagnosticOption: ReportDiagnostic.Error,
            warningLevel: 9999,
            concurrentBuild: false,
            deterministic: true,
            nullableContextOptions: NullableContextOptions.Enable,
            metadataImportOptions: MetadataImportOptions.Public);
        var compilation = CSharpCompilation.Create(
            "ProgramKit.GeneratedConsole.Candidate",
            syntaxTrees.ToImmutable(),
            metadataReferences.ToImmutable(),
            compilationOptions);
        using MemoryStream output = new();
        EmitResult result = compilation.Emit(
            output,
            cancellationToken: cancellationToken);
        foreach (var diagnostic in result.Diagnostics
                     .Where(static item =>
                         item.Severity is DiagnosticSeverity.Error or
                             DiagnosticSeverity.Warning)
                     .OrderBy(
                         static item =>
                             item.Location.GetLineSpan().Path,
                         StringComparer.Ordinal)
                     .ThenBy(static item =>
                         item.Location.SourceSpan.Start)
                     .ThenBy(static item => item.Id, StringComparer.Ordinal))
        {
            var span = diagnostic.Location.GetLineSpan();
            Error(
                diagnostics,
                string.Concat(
                    diagnostic.Id,
                    ": ",
                    diagnostic.GetMessage(CultureInfo.InvariantCulture)),
                span.IsValid
                    ? string.Concat(
                        span.Path,
                        ":",
                        (span.StartLinePosition.Line + 1)
                            .ToString(CultureInfo.InvariantCulture))
                    : string.Empty);
        }

        return result.Success
            ? new DotNetConsoleCompilationResult(
                true,
                output.ToArray().ToImmutableArray(),
                diagnostics.ToImmutable())
            : Invalid(diagnostics);
    }

    private static bool IsSafeSourcePath(string value)
    {
        if (string.IsNullOrWhiteSpace(value) ||
            value.Contains('\\') ||
            value.StartsWith('/') ||
            value.Contains(':') ||
            !value.EndsWith(".cs", StringComparison.Ordinal))
        {
            return false;
        }

        return value.Split('/').All(static segment =>
            segment.Length > 0 &&
            segment is not "." and not "..");
    }

    private static DotNetConsoleCompilationResult Invalid(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        new(false, [], diagnostics.ToImmutable());

    private static void Error(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string message,
        string path) =>
        diagnostics.Add(
            new ProgramKitDiagnostic(
                DotNetDiagnosticIds.ConsoleCandidateCompilationFailed,
                ProgramKitDiagnosticSeverity.Error,
                message,
                path));
}
