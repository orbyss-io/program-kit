using Microsoft.Build.Framework;

namespace Orbyss.ProgramKit.CSharpBuildGates.Build.Operations.Execution;

/// <summary>
/// Reconciles controlled compiler inputs after compilation and requires one
/// exact same-assembly receipt for every applicable analyzer.
/// </summary>
public sealed class VerifyCSharpBuildGateTask : ITask
{
    /// <inheritdoc />
    public IBuildEngine BuildEngine { get; set; } = null!;

    /// <inheritdoc />
    public ITaskHost? HostObject { get; set; }

    /// <summary>Applicable analyzers selected before compilation.</summary>
    [Required]
    public ITaskItem[] ApplicableAnalyzers { get; set; } = [];

    /// <summary>Exact expected compiler-input inventory.</summary>
    [Required]
    public ITaskItem[] ExpectedInputs { get; set; } = [];

    /// <summary>Executed compiler inputs to reconcile.</summary>
    [Required]
    public ITaskItem[] ExecutedInputs { get; set; } = [];

    /// <summary>Unique invocation root created before compilation.</summary>
    [Required]
    public string InvocationRoot { get; set; } = string.Empty;

    /// <summary>Unique compilation nonce.</summary>
    [Required]
    public string CompilationNonce { get; set; } = string.Empty;

    /// <summary>Exact project profile identity.</summary>
    [Required]
    public string ProjectProfileId { get; set; } = string.Empty;

    /// <summary>Exact verification profile.</summary>
    [Required]
    public string VerificationProfile { get; set; } = string.Empty;

    /// <summary>Exact selection-lock digest.</summary>
    [Required]
    public string SelectionLockDigest { get; set; } = string.Empty;

    /// <summary>Pre-compiler controlled-input digest.</summary>
    [Required]
    public string PreCompilerInputDigest { get; set; } = string.Empty;

    /// <inheritdoc />
    public bool Execute()
    {
        try
        {
            if (CompilationNonce.Length != 32 ||
                !CompilationNonce.All(character =>
                    character is (>= '0' and <= '9') or (>= 'a' and <= 'f')))
            {
                throw new InvalidOperationException(
                    "The compiler nonce is missing or malformed.");
            }

            if (!Directory.Exists(InvocationRoot))
            {
                throw new InvalidOperationException(
                    "The isolated invocation root no longer exists.");
            }

            var postDigest = ComputePostCompilerInputDigest();
            if (!string.Equals(
                    PreCompilerInputDigest,
                    postDigest,
                    StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    "A controlled compiler input changed after validation.");
            }

            var receiptDirectory = Path.Combine(InvocationRoot, "participation");
            var observedPaths = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase);
            foreach (var analyzer in ApplicableAnalyzers)
            {
                Directory.CreateDirectory(receiptDirectory);
                VerifyAnalyzerReceipt(analyzer, receiptDirectory, observedPaths);
            }

            return true;
        }
        catch (Exception exception)
        {
            BuildEngine.LogErrorEvent(
                new BuildErrorEventArgs(
                    "ProgramKit.CSharpBuildGate",
                    "PKCG200",
                    string.Empty,
                    0,
                    0,
                    0,
                    0,
                    exception.Message,
                    string.Empty,
                    nameof(VerifyCSharpBuildGateTask)));
            return false;
        }
    }

    private string ComputePostCompilerInputDigest()
    {
        var expected = ExpectedInputs
            .Select(item =>
            {
                var kind = CSharpBuildGateTaskSupport.RequiredMetadata(
                    item,
                    "Kind");
                var path = CSharpBuildGateTaskSupport.CanonicalPath(item.ItemSpec);
                if (!File.Exists(path))
                {
                    throw new InvalidOperationException(
                        $"Controlled compiler input '{path}' disappeared.");
                }

                var digest = CSharpBuildGateTaskSupport.FileDigest(path);
                var expectedDigest = CSharpBuildGateTaskSupport.RequiredMetadata(
                    item,
                    "Digest");
                if (!CSharpBuildGateTaskSupport.DigestMatches(
                        expectedDigest,
                        digest))
                {
                    throw new InvalidOperationException(
                        $"Controlled compiler input '{path}' changed.");
                }

                return string.Concat(kind, "|", path, "|", digest);
            });
        var actualKeys = ExecutedInputs
            .Select(item => string.Concat(
                CSharpBuildGateTaskSupport.RequiredMetadata(item, "Kind"),
                "|",
                CSharpBuildGateTaskSupport.CanonicalPath(item.ItemSpec)))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var expectedKeys = ExpectedInputs
            .Select(item => string.Concat(
                CSharpBuildGateTaskSupport.RequiredMetadata(item, "Kind"),
                "|",
                CSharpBuildGateTaskSupport.CanonicalPath(item.ItemSpec)))
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!expectedKeys.SequenceEqual(actualKeys, StringComparer.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "The executed compiler-input inventory changed after validation.");
        }

        return CSharpBuildGateTaskSupport.TextDigest(
            expected.Concat(
                ApplicableAnalyzers.Select(analyzer =>
                {
                    var path = CSharpBuildGateTaskSupport.CanonicalPath(
                        analyzer.ItemSpec);
                    var digest = CSharpBuildGateTaskSupport.FileDigest(path);
                    if (!CSharpBuildGateTaskSupport.DigestMatches(
                            CSharpBuildGateTaskSupport.RequiredMetadata(
                                analyzer,
                                "AssemblyDigest"),
                            digest))
                    {
                        throw new InvalidOperationException(
                            $"Analyzer '{path}' changed after validation.");
                    }

                    return string.Concat(
                        "analyzer|",
                        analyzer.GetMetadata("ComponentId"),
                        "|",
                        path,
                        "|",
                        digest);
                })));
    }

    private void VerifyAnalyzerReceipt(
        ITaskItem analyzer,
        string receiptDirectory,
        HashSet<string> observedPaths)
    {
        var component = CSharpBuildGateTaskSupport.RequiredMetadata(
            analyzer,
            "ComponentId");
        var relativeTemplate = CSharpBuildGateTaskSupport.RequiredMetadata(
            analyzer,
            "ReceiptRelativePathTemplate");
        var relative = CSharpBuildGateTaskSupport.Substitute(
            relativeTemplate,
            CompilationNonce,
            ProjectProfileId,
            VerificationProfile);
        var receiptPath = Path.GetFullPath(
            Path.Combine(InvocationRoot, "generated", relative));
        if (!CSharpBuildGateTaskSupport.IsUnder(
                receiptPath,
                Path.Combine(InvocationRoot, "generated")) ||
            !observedPaths.Add(receiptPath) ||
            !File.Exists(receiptPath))
        {
            throw new InvalidOperationException(
                $"Analyzer component '{component}' did not emit one exact receipt.");
        }

        var expectedMarker = CSharpBuildGateTaskSupport.Substitute(
            CSharpBuildGateTaskSupport.RequiredMetadata(
                analyzer,
                "ReceiptMarkerTemplate"),
            CompilationNonce,
            ProjectProfileId,
            VerificationProfile);
        var content = File.ReadAllText(receiptPath);
        if (!content.Contains(expectedMarker, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Analyzer component '{component}' emitted a mismatched receipt.");
        }

        var assemblyDigest = CSharpBuildGateTaskSupport.FileDigest(
            analyzer.ItemSpec);
        var outputPath = Path.Combine(
            receiptDirectory,
            string.Concat(
                CSharpBuildGateTaskSupport.TextDigest([component])[..16],
                ".json"));
        File.WriteAllText(
            outputPath,
            string.Concat(
                "{\"schemaVersion\":\"1.0.0\",\"identity\":",
                CSharpBuildGateTaskSupport.JsonString(
                    analyzer.GetMetadata("ReceiptIdentity")),
                ",\"selectionLockDigest\":",
                CSharpBuildGateTaskSupport.JsonString(SelectionLockDigest),
                ",\"projectProfileId\":",
                CSharpBuildGateTaskSupport.JsonString(ProjectProfileId),
                ",\"analyzerComponentId\":",
                CSharpBuildGateTaskSupport.JsonString(component),
                ",\"verificationProfile\":",
                CSharpBuildGateTaskSupport.JsonString(VerificationProfile),
                ",\"compilationNonce\":",
                CSharpBuildGateTaskSupport.JsonString(CompilationNonce),
                ",\"analyzerAssemblyDigest\":\"sha256:",
                assemblyDigest,
                "\",\"validatedCompilerInputDigest\":\"sha256:",
                PreCompilerInputDigest,
                "\",\"executedCompilerInputDigest\":\"sha256:",
                PreCompilerInputDigest,
                "\"}\n"));
    }
}
