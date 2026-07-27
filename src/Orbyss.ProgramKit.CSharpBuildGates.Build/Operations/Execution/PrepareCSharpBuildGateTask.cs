using System.Globalization;
using Microsoft.Build.Framework;
using Microsoft.Build.Utilities;

namespace Orbyss.ProgramKit.CSharpBuildGates.Build.Operations.Execution;

/// <summary>
/// Validates an exact lock projection and prepares one isolated compiler
/// invocation without discovering or loading analyzer assemblies.
/// </summary>
public sealed class PrepareCSharpBuildGateTask : ITask
{
    /// <inheritdoc />
    public IBuildEngine BuildEngine { get; set; } = null!;

    /// <inheritdoc />
    public ITaskHost? HostObject { get; set; }

    /// <summary>Exact analyzer selections projected by the binding operation.</summary>
    [Required]
    public ITaskItem[] AnalyzerSelections { get; set; } = [];

    /// <summary>Finite activation cells projected by the binding operation.</summary>
    [Required]
    public ITaskItem[] Activations { get; set; } = [];

    /// <summary>Typed temporary exceptions projected by the binding operation.</summary>
    public ITaskItem[] TemporaryExceptions { get; set; } = [];

    /// <summary>Exact expected compiler-input inventory.</summary>
    [Required]
    public ITaskItem[] ExpectedInputs { get; set; } = [];

    /// <summary>Actual compiler inputs supplied by MSBuild.</summary>
    [Required]
    public ITaskItem[] ExecutedInputs { get; set; } = [];

    /// <summary>Analyzers present before gate attachment.</summary>
    public ITaskItem[] ExistingAnalyzers { get; set; } = [];

    /// <summary>Current exact project path.</summary>
    [Required]
    public string ProjectPath { get; set; } = string.Empty;

    /// <summary>Current project profile identity.</summary>
    [Required]
    public string ProjectProfileId { get; set; } = string.Empty;

    /// <summary>Current source profile identity.</summary>
    [Required]
    public string SourceProfileId { get; set; } = string.Empty;

    /// <summary>Current finite command.</summary>
    [Required]
    public string Command { get; set; } = string.Empty;

    /// <summary>Current finite implementation boundary.</summary>
    [Required]
    public string Boundary { get; set; } = string.Empty;

    /// <summary>Current finite verification profile.</summary>
    [Required]
    public string VerificationProfile { get; set; } = string.Empty;

    /// <summary>Project intermediate-output root.</summary>
    [Required]
    public string IntermediateRoot { get; set; } = string.Empty;

    /// <summary>Bounded base for unique invocation roots.</summary>
    [Required]
    public string ReceiptBase { get; set; } = string.Empty;

    /// <summary>Exact selection-lock digest.</summary>
    [Required]
    public string SelectionLockDigest { get; set; } = string.Empty;

    /// <summary>Observed SDK version.</summary>
    [Required]
    public string SdkVersion { get; set; } = string.Empty;

    /// <summary>Observed compiler/Roslyn version.</summary>
    [Required]
    public string CompilerRoslynVersion { get; set; } = string.Empty;

    /// <summary>Observed language version.</summary>
    [Required]
    public string LanguageVersion { get; set; } = string.Empty;

    /// <summary>Observed target framework.</summary>
    [Required]
    public string TargetFramework { get; set; } = string.Empty;

    /// <summary>Observed RunAnalyzers value.</summary>
    [Required]
    public string RunAnalyzers { get; set; } = string.Empty;

    /// <summary>Observed RunAnalyzersDuringBuild value.</summary>
    [Required]
    public string RunAnalyzersDuringBuild { get; set; } = string.Empty;

    /// <summary>Observed analyzer warning policy.</summary>
    [Required]
    public string CodeAnalysisTreatWarningsAsErrors { get; set; } =
        string.Empty;

    /// <summary>Observed compiler warning policy.</summary>
    [Required]
    public string TreatWarningsAsErrors { get; set; } = string.Empty;

    /// <summary>Observed warning suppressions.</summary>
    public string NoWarn { get; set; } = string.Empty;

    /// <summary>Observed warning demotions.</summary>
    public string WarningsNotAsErrors { get; set; } = string.Empty;

    /// <summary>Matrix-applicable, non-excepted analyzers.</summary>
    [Output]
    public ITaskItem[] ApplicableAnalyzers { get; private set; } = [];

    /// <summary>Unique isolated invocation root.</summary>
    [Output]
    public string InvocationRoot { get; private set; } = string.Empty;

    /// <summary>Unique per-compilation lower-hex nonce.</summary>
    [Output]
    public string CompilationNonce { get; private set; } = string.Empty;

    /// <summary>Digest of validated analyzer and compiler inputs.</summary>
    [Output]
    public string PreCompilerInputDigest { get; private set; } = string.Empty;

    /// <inheritdoc />
    public bool Execute()
    {
        try
        {
            ValidateFiniteContext();
            ValidateExecutionCannotBeDemoted();
            ValidateSelectionLockDigest();
            var inventoryLines = ValidateAndReconcileInputs();
            var selected = ValidateSelections();
            var applicable = EvaluateActivations(selected);
            var nonce = Guid.NewGuid().ToString("N", CultureInfo.InvariantCulture);
            var root = PrepareInvocationRoot(nonce);
            WriteExceptionReceipts(root, nonce, applicable.Excepted);

            ApplicableAnalyzers = applicable.Applicable.ToArray();
            CompilationNonce = nonce;
            InvocationRoot = root;
            PreCompilerInputDigest = CSharpBuildGateTaskSupport.TextDigest(
                inventoryLines.Concat(
                    ApplicableAnalyzers.Select(analyzer =>
                        string.Concat(
                            "analyzer|",
                            analyzer.GetMetadata("ComponentId"),
                            "|",
                            CSharpBuildGateTaskSupport.CanonicalPath(
                                analyzer.ItemSpec),
                            "|",
                            CSharpBuildGateTaskSupport.FileDigest(
                                analyzer.ItemSpec)))));
            File.WriteAllLines(
                Path.Combine(root, "pre-compiler-inputs.lock"),
                [
                    $"selection-lock|{SelectionLockDigest}",
                    $"project-profile|{ProjectProfileId}",
                    $"source-profile|{SourceProfileId}",
                    $"command|{Command}",
                    $"boundary|{Boundary}",
                    $"verification-profile|{VerificationProfile}",
                    $"input-digest|{PreCompilerInputDigest}",
                    .. inventoryLines.Order(StringComparer.Ordinal),
                ]);
            return true;
        }
        catch (Exception exception)
        {
            BuildEngine.LogErrorEvent(
                new BuildErrorEventArgs(
                    "ProgramKit.CSharpBuildGate",
                    "PKCG100",
                    ProjectPath,
                    0,
                    0,
                    0,
                    0,
                    exception.Message,
                    string.Empty,
                    nameof(PrepareCSharpBuildGateTask)));
            return false;
        }
    }

    private void ValidateFiniteContext()
    {
        RequireFinite(Command, CSharpBuildGateTaskSupport.Commands, "command");
        RequireFinite(
            Boundary,
            CSharpBuildGateTaskSupport.Boundaries,
            "implementation boundary");
        RequireFinite(
            VerificationProfile,
            CSharpBuildGateTaskSupport.VerificationProfiles,
            "verification profile");
        if (!File.Exists(ProjectPath))
        {
            throw new InvalidOperationException(
                "The exact current project path does not exist.");
        }

        if (string.IsNullOrWhiteSpace(ProjectProfileId) ||
            string.IsNullOrWhiteSpace(SourceProfileId))
        {
            throw new InvalidOperationException(
                "Exact project and source profile identities are required.");
        }
    }

    private void ValidateExecutionCannotBeDemoted()
    {
        if (!IsTrue(RunAnalyzers) ||
            !IsTrue(RunAnalyzersDuringBuild) ||
            !IsTrue(CodeAnalysisTreatWarningsAsErrors) ||
            !IsTrue(TreatWarningsAsErrors))
        {
            throw new InvalidOperationException(
                "Analyzer execution and error severity must remain enabled.");
        }
    }

    private void ValidateSelectionLockDigest()
    {
        if (!SelectionLockDigest.StartsWith("sha256:", StringComparison.Ordinal) ||
            SelectionLockDigest.Length != 71 ||
            !SelectionLockDigest[7..].All(Uri.IsHexDigit))
        {
            throw new InvalidOperationException(
                "The selection lock requires one exact SHA-256 digest.");
        }
    }

    private List<string> ValidateAndReconcileInputs()
    {
        var expected = ExpectedInputs
            .Select(item =>
            {
                var kind = CSharpBuildGateTaskSupport.RequiredMetadata(
                    item,
                    "Kind");
                RequireFinite(
                    kind,
                    CSharpBuildGateTaskSupport.InputKinds,
                    "input kind");
                var path = CSharpBuildGateTaskSupport.CanonicalPath(
                    item.ItemSpec);
                var digest = CSharpBuildGateTaskSupport.RequiredMetadata(
                    item,
                    "Digest");
                return (Key: string.Concat(kind, "|", path), Path: path, Digest: digest);
            })
            .OrderBy(item => item.Key, StringComparer.Ordinal)
            .ToArray();
        var duplicate = expected
            .GroupBy(item => item.Key, StringComparer.OrdinalIgnoreCase)
            .FirstOrDefault(group => group.Count() != 1);
        if (duplicate is not null)
        {
            throw new InvalidOperationException(
                $"Expected compiler input '{duplicate.Key}' is duplicated.");
        }

        var actual = ExecutedInputs
            .Select(item =>
            {
                var kind = CSharpBuildGateTaskSupport.RequiredMetadata(
                    item,
                    "Kind");
                RequireFinite(
                    kind,
                    CSharpBuildGateTaskSupport.InputKinds,
                    "executed input kind");
                var path = CSharpBuildGateTaskSupport.CanonicalPath(
                    item.ItemSpec);
                return (Key: string.Concat(kind, "|", path), Path: path);
            })
            .OrderBy(item => item.Key, StringComparer.Ordinal)
            .ToArray();
        var actualDuplicate = actual
            .GroupBy(item => item.Key, StringComparer.OrdinalIgnoreCase)
            .FirstOrDefault(group => group.Count() != 1);
        if (actualDuplicate is not null)
        {
            throw new InvalidOperationException(
                $"Executed compiler input '{actualDuplicate.Key}' is duplicated.");
        }

        if (!expected.Select(item => item.Key).SequenceEqual(
                actual.Select(item => item.Key),
                StringComparer.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "The exact expected and executed compiler-input inventories differ.");
        }

        var lines = new List<string>(expected.Length);
        foreach (var item in expected)
        {
            if (!File.Exists(item.Path))
            {
                throw new InvalidOperationException(
                    $"Controlled compiler input '{item.Path}' does not exist.");
            }

            var digest = CSharpBuildGateTaskSupport.FileDigest(item.Path);
            if (!CSharpBuildGateTaskSupport.DigestMatches(item.Digest, digest))
            {
                throw new InvalidOperationException(
                    $"Controlled compiler input '{item.Path}' changed.");
            }

            lines.Add(string.Concat(item.Key, "|", digest));
        }

        return lines;
    }

    private Dictionary<string, ITaskItem> ValidateSelections()
    {
        var selected = new Dictionary<string, ITaskItem>(StringComparer.Ordinal);
        var existingPaths = ExistingAnalyzers
            .Select(item => CSharpBuildGateTaskSupport.CanonicalPath(item.ItemSpec))
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        foreach (var analyzer in AnalyzerSelections)
        {
            var component = CSharpBuildGateTaskSupport.RequiredMetadata(
                analyzer,
                "ComponentId");
            if (!selected.TryAdd(component, analyzer))
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{component}' is selected more than once.");
            }

            var kind = CSharpBuildGateTaskSupport.RequiredMetadata(analyzer, "Kind");
            if (kind is not ("program-kit-public-contract" or "consumer-owned"))
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{component}' has forbidden kind '{kind}'.");
            }

            var path = CSharpBuildGateTaskSupport.CanonicalPath(analyzer.ItemSpec);
            if (!File.Exists(path) ||
                !string.Equals(
                    Path.GetExtension(path),
                    ".dll",
                    StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{component}' is not one exact assembly.");
            }

            if (string.Equals(
                    Path.GetFileName(path),
                    "Orbyss.ProgramKit.CSharpGate.dll",
                    StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException(
                    "The private Program Kit analyzer cannot be selected for consumer source.");
            }

            if (existingPaths.Contains(path))
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{component}' was already attached.");
            }

            var digest = CSharpBuildGateTaskSupport.RequiredMetadata(
                analyzer,
                "AssemblyDigest");
            if (!CSharpBuildGateTaskSupport.DigestMatches(
                    digest,
                    CSharpBuildGateTaskSupport.FileDigest(path)))
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{component}' was substituted or changed.");
            }

            RequireFalseMetadata(analyzer, "HasRuntimeAssets");
            RequireFalseMetadata(analyzer, "HasBuildTransitiveAssets");
            _ = CSharpBuildGateTaskSupport.RequiredMetadata(
                analyzer,
                "ReceiptIdentity");
            var receiptPath = CSharpBuildGateTaskSupport.RequiredMetadata(
                analyzer,
                "ReceiptRelativePathTemplate");
            if (Path.IsPathRooted(receiptPath) ||
                receiptPath.Split('/', '\\').Any(segment => segment == "..") ||
                !receiptPath.Contains("{nonce}", StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{component}' has an unsafe receipt path.");
            }

            var diagnostics = CSharpBuildGateTaskSupport.RequiredMetadata(
                analyzer,
                "DiagnosticIds")
                .Split(';', StringSplitOptions.RemoveEmptyEntries);
            if (diagnostics.Length == 0 ||
                diagnostics.Distinct(StringComparer.Ordinal).Count() != diagnostics.Length)
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{component}' requires unique diagnostics.");
            }

            var disabled = SplitWarnings(NoWarn)
                .Concat(SplitWarnings(WarningsNotAsErrors))
                .ToHashSet(StringComparer.OrdinalIgnoreCase);
            if (diagnostics.Any(disabled.Contains))
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{component}' has a suppressed or demoted diagnostic.");
            }
        }

        var collision = selected
            .SelectMany(pair =>
                CSharpBuildGateTaskSupport.RequiredMetadata(
                        pair.Value,
                        "DiagnosticIds")
                    .Split(';', StringSplitOptions.RemoveEmptyEntries)
                    .Select(diagnostic => (Diagnostic: diagnostic, Component: pair.Key)))
            .GroupBy(value => value.Diagnostic, StringComparer.Ordinal)
            .FirstOrDefault(group => group.Select(value => value.Component)
                .Distinct(StringComparer.Ordinal)
                .Count() != 1);
        if (collision is not null)
        {
            throw new InvalidOperationException(
                $"Diagnostic identity '{collision.Key}' collides across analyzers.");
        }

        return selected;
    }

    private CSharpBuildGateActivationResult EvaluateActivations(
        IReadOnlyDictionary<string, ITaskItem> selected)
    {
        var applicable = new List<ITaskItem>();
        var excepted = new List<(ITaskItem Analyzer, ITaskItem Exception)>();
        foreach (var pair in selected.OrderBy(pair => pair.Key, StringComparer.Ordinal))
        {
            var matching = Activations
                .Where(activation =>
                    string.Equals(
                        activation.ItemSpec,
                        pair.Key,
                        StringComparison.Ordinal) &&
                    ScopeMatches(activation))
                .ToArray();
            if (matching.Length > 1)
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{pair.Key}' has ambiguous activation.");
            }

            if (matching.Length == 0)
            {
                continue;
            }

            var exceptions = TemporaryExceptions
                .Where(item =>
                    string.Equals(
                        item.GetMetadata("AnalyzerComponentId"),
                        pair.Key,
                        StringComparison.Ordinal) &&
                    ScopeMatches(item))
                .ToArray();
            if (exceptions.Length > 1)
            {
                throw new InvalidOperationException(
                    $"Analyzer component '{pair.Key}' has ambiguous temporary exceptions.");
            }

            if (exceptions.Length == 1 && EvaluateException(exceptions[0]))
            {
                excepted.Add((pair.Value, exceptions[0]));
                continue;
            }

            applicable.Add(pair.Value);
        }

        return new CSharpBuildGateActivationResult(applicable, excepted);
    }

    private bool EvaluateException(ITaskItem exception)
    {
        var digest = CSharpBuildGateTaskSupport.RequiredMetadata(
            exception,
            "ExceptionDigest");
        if (!digest.StartsWith("sha256:", StringComparison.Ordinal) ||
            digest.Length != 71 ||
            !digest[7..].All(Uri.IsHexDigit))
        {
            throw new InvalidOperationException(
                $"Temporary exception '{exception.ItemSpec}' has no exact digest.");
        }

        _ = CSharpBuildGateTaskSupport.RequiredMetadata(exception, "HumanAuthority");
        _ = CSharpBuildGateTaskSupport.RequiredMetadata(
            exception,
            "CompensatingVerification");
        var activated = CSharpBuildGateTaskSupport.ParseTimestamp(
            CSharpBuildGateTaskSupport.RequiredMetadata(exception, "ActivatedAt"),
            "ActivatedAt");
        var evaluatedAt = DateTimeOffset.UtcNow;
        if (evaluatedAt < activated)
        {
            throw new InvalidOperationException(
                $"Temporary exception '{exception.ItemSpec}' is not active yet.");
        }

        var expiresValue = CSharpBuildGateTaskSupport.RequiredMetadata(
            exception,
            "ExpiresAt");
        var expires = CSharpBuildGateTaskSupport.ParseTimestamp(
            expiresValue,
            "ExpiresAt");
        if (evaluatedAt >= expires)
        {
            throw new InvalidOperationException(
                $"Temporary exception '{exception.ItemSpec}' expired.");
        }

        var maximumUses = CSharpBuildGateTaskSupport.ParseNonNegativeInt(
            CSharpBuildGateTaskSupport.RequiredMetadata(exception, "MaximumUses"),
            "MaximumUses");
        var observedUses = CSharpBuildGateTaskSupport.ParseNonNegativeInt(
            CSharpBuildGateTaskSupport.RequiredMetadata(exception, "ObservedUses"),
            "ObservedUses");
        if (maximumUses == 0 || observedUses >= maximumUses)
        {
            throw new InvalidOperationException(
                $"Temporary exception '{exception.ItemSpec}' exhausted its uses.");
        }

        var kind = CSharpBuildGateTaskSupport.RequiredMetadata(
            exception,
            "ConditionKind");
        return kind switch
        {
            "exact-toolchain-incompatibility" =>
                Exact(exception, "SdkVersion", SdkVersion) &&
                Exact(exception, "CompilerRoslynVersion", CompilerRoslynVersion) &&
                Exact(exception, "CompatibilityState", "incompatible"),
            "exact-target-framework-incompatibility" =>
                Exact(exception, "TargetFramework", TargetFramework) &&
                Exact(exception, "CompatibilityState", "incompatible"),
            "unavailable-generated-input" =>
                Exact(exception, "ProducerState", "unavailable-verified") &&
                ExactDigestMetadata(exception, "ProducerStateDigest") &&
                !File.Exists(CSharpBuildGateTaskSupport.RequiredMetadata(
                    exception,
                    "GeneratedInputPath")),
            "gate-establishment-boundary" =>
                Boundary == "gate-establishment" &&
                Exact(exception, "RequiredBoundary", "gate-establishment"),
            _ => throw new InvalidOperationException(
                $"Temporary exception '{exception.ItemSpec}' has unknown condition kind '{kind}'."),
        };
    }

    private string PrepareInvocationRoot(string nonce)
    {
        var intermediate = CSharpBuildGateTaskSupport.CanonicalPath(
            IntermediateRoot);
        var receiptBase = CSharpBuildGateTaskSupport.CanonicalPath(ReceiptBase);
        if (!CSharpBuildGateTaskSupport.IsUnder(receiptBase, intermediate))
        {
            throw new InvalidOperationException(
                "The receipt base must remain inside the project intermediate root.");
        }

        var root = Path.Combine(receiptBase, nonce);
        if (Directory.Exists(root))
        {
            Directory.Delete(root, recursive: true);
        }

        Directory.CreateDirectory(root);
        return root;
    }

    private static void WriteExceptionReceipts(
        string root,
        string nonce,
        IEnumerable<(ITaskItem Analyzer, ITaskItem Exception)> exceptions)
    {
        var receiptDirectory = Path.Combine(root, "exceptions");
        foreach (var pair in exceptions)
        {
            Directory.CreateDirectory(receiptDirectory);
            var component = pair.Analyzer.GetMetadata("ComponentId");
            var exceptionDigest = pair.Exception.GetMetadata("ExceptionDigest");
            var conditionInputs = pair.Exception.CloneCustomMetadata()
                .Cast<KeyValuePair<string, string>>()
                .Where(entry =>
                    entry.Key is not null &&
                    entry.Key is
                        not ("FullPath" or "RootDir" or "Filename" or "Extension"))
                .Select(entry => string.Concat(entry.Key, "=", entry.Value));
            var conditionDigest = CSharpBuildGateTaskSupport.TextDigest(
                conditionInputs);
            var path = Path.Combine(
                receiptDirectory,
                string.Concat(
                    CSharpBuildGateTaskSupport.TextDigest([component])[..16],
                    ".json"));
            File.WriteAllText(
                path,
                string.Concat(
                    "{\"schemaVersion\":\"1.0.0\",\"kind\":\"temporary-exception-use\",",
                    "\"analyzerComponentId\":",
                    CSharpBuildGateTaskSupport.JsonString(component),
                    ",\"exceptionDigest\":",
                    CSharpBuildGateTaskSupport.JsonString(exceptionDigest),
                    ",\"compilationNonce\":",
                    CSharpBuildGateTaskSupport.JsonString(nonce),
                    ",\"conditionMatched\":true,\"evaluatedConditionInputsDigest\":\"sha256:",
                    conditionDigest,
                    "\"}\n"));
        }
    }

    private bool ScopeMatches(ITaskItem item) =>
        Exact(item, "ProjectProfileId", ProjectProfileId) &&
        Exact(item, "SourceProfileId", SourceProfileId) &&
        Exact(item, "Command", Command) &&
        Exact(item, "Boundary", Boundary) &&
        Exact(item, "VerificationProfile", VerificationProfile);

    private static bool Exact(ITaskItem item, string name, string expected) =>
        string.Equals(
            CSharpBuildGateTaskSupport.RequiredMetadata(item, name),
            expected,
            StringComparison.Ordinal);

    private static bool ExactDigestMetadata(ITaskItem item, string name)
    {
        var value = CSharpBuildGateTaskSupport.RequiredMetadata(item, name);
        return value.StartsWith("sha256:", StringComparison.Ordinal) &&
            value.Length == 71 &&
            value[7..].All(Uri.IsHexDigit);
    }

    private static void RequireFalseMetadata(ITaskItem item, string name)
    {
        if (!string.Equals(
                CSharpBuildGateTaskSupport.RequiredMetadata(item, name),
                "false",
                StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Analyzer '{item.ItemSpec}' cannot carry {name}.");
        }
    }

    private static void RequireFinite(
        string value,
        IEnumerable<string> allowed,
        string name)
    {
        if (!allowed.Contains(value, StringComparer.Ordinal))
        {
            throw new InvalidOperationException(
                $"Unknown {name} '{value}'.");
        }
    }

    private static bool IsTrue(string value) =>
        string.Equals(value, "true", StringComparison.OrdinalIgnoreCase);

    private static string[] SplitWarnings(string value) =>
        value.Split(
            [';', ',', ' '],
            StringSplitOptions.RemoveEmptyEntries |
            StringSplitOptions.TrimEntries);

}
