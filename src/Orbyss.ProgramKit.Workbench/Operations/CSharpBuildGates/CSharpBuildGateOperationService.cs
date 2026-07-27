using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>
/// Implements the five gate operations over explicit inputs. Only verification
/// delegates to a compiler process boundary.
/// </summary>
public sealed class CSharpBuildGateOperationService :
    ICSharpBuildGateOperationService
{
    private readonly IProgramKitSemanticValidator<CSharpBuildGateDefinitionDocument>
        definitionValidator;
    private readonly IProgramKitSemanticValidator<CSharpBuildGateSelectionLockDocument>
        lockValidator;
    private readonly IConsumerAnalyzerScaffoldingService scaffolding;
    private readonly ICSharpGateCompilerHarness compilerHarness;

    /// <summary>Initializes the operation service from exact owned behaviors.</summary>
    public CSharpBuildGateOperationService(
        IProgramKitSemanticValidator<CSharpBuildGateDefinitionDocument>
            definitionValidator,
        IProgramKitSemanticValidator<CSharpBuildGateSelectionLockDocument>
            lockValidator,
        IConsumerAnalyzerScaffoldingService scaffolding,
        ICSharpGateCompilerHarness compilerHarness)
    {
        this.definitionValidator = definitionValidator ??
            throw new ArgumentNullException(nameof(definitionValidator));
        this.lockValidator = lockValidator ??
            throw new ArgumentNullException(nameof(lockValidator));
        this.scaffolding = scaffolding ??
            throw new ArgumentNullException(nameof(scaffolding));
        this.compilerHarness = compilerHarness ??
            throw new ArgumentNullException(nameof(compilerHarness));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult ValidateDefinition(
        CSharpBuildGateDefinitionDocument definition) =>
        definitionValidator.Validate(definition);

    /// <inheritdoc />
    public string RenderDefinition(CSharpBuildGateDefinitionDocument definition)
    {
        var validation = definitionValidator.Validate(definition);
        if (!validation.IsValid)
        {
            throw new CSharpBuildGateOperationException(
                CSharpGateEvidenceLayer.Definition,
                "Only a valid exact gate definition can be rendered.");
        }

        var builder = new StringBuilder();
        builder.AppendLine("# C# build gate");
        builder.AppendLine();
        builder.Append("Identity: `").Append(definition.Identity.Value)
            .AppendLine("`  ");
        builder.Append("Version: `").Append(definition.Version.Value)
            .AppendLine("`  ");
        builder.Append("Consumer owner: `").Append(definition.OwnerId.Value)
            .AppendLine("`");
        builder.AppendLine();
        builder.AppendLine("## Analyzer selections");
        builder.AppendLine();
        foreach (var analyzer in definition.AnalyzerComponents)
        {
            builder.Append("- `").Append(analyzer.Identity.Value)
                .Append("` — ")
                .Append(Kebab(analyzer.Kind.ToString()))
                .Append("; semantic owner `")
                .Append(analyzer.SemanticOwnerId.Value)
                .AppendLine("`");
        }

        builder.AppendLine();
        builder.AppendLine("## Rules");
        builder.AppendLine();
        foreach (var rule in definition.RuleCatalog.Rules)
        {
            builder.Append("- `").Append(rule.DiagnosticId)
                .Append("` — ")
                .Append(rule.Title)
                .Append("; owner `")
                .Append(rule.SemanticOwnerId.Value)
                .AppendLine("`");
        }

        builder.AppendLine();
        builder.AppendLine("## Activation matrix");
        builder.AppendLine();
        foreach (var activation in definition.ActivationMatrix.Activations)
        {
            builder.Append("- `")
                .Append(activation.ProjectProfileId.Value)
                .Append("` / `")
                .Append(activation.SourceProfileId.Value)
                .Append("` / `")
                .Append(Kebab(activation.Command.ToString()))
                .Append("` / `")
                .Append(Kebab(activation.Boundary.ToString()))
                .Append("` / `")
                .Append(Kebab(activation.VerificationProfile.ToString()))
                .Append("`: ")
                .AppendLine(string.Join(
                    ", ",
                    activation.AnalyzerComponentIds.Select(
                        identity => string.Concat("`", identity.Value, "`"))));
        }

        builder.AppendLine();
        builder.Append("Temporary exceptions: ")
            .Append(definition.TemporaryExceptions.Length)
            .AppendLine();
        return builder.ToString().Replace("\r\n", "\n", StringComparison.Ordinal);
    }

    /// <inheritdoc />
    public ValueTask<ConsumerAnalyzerScaffoldPlan> ScaffoldAsync(
        ConsumerAnalyzerScaffoldRequest request,
        string outputRoot,
        CancellationToken cancellationToken) =>
        scaffolding.ScaffoldAsync(request, outputRoot, cancellationToken);

    /// <inheritdoc />
    public CSharpBuildGateSelectionLockDocument Bind(CSharpGateBindRequest request)
    {
        ArgumentNullException.ThrowIfNull(request);
        var validation = lockValidator.Validate(request.CandidateLock);
        if (!validation.IsValid)
        {
            throw new CSharpBuildGateOperationException(
                CSharpGateEvidenceLayer.Definition,
                "The candidate selection lock is invalid.");
        }

        var root = Path.GetFullPath(request.RepositoryRoot);
        if (!Directory.Exists(root) ||
            request.LocalAssets.IsDefaultOrEmpty ||
            request.LocalAssets
                .Select(asset => asset.RepositoryRelativePath)
                .Distinct(StringComparer.Ordinal)
                .Count() != request.LocalAssets.Length ||
            !request.LocalAssets
                .Select(asset => asset.RepositoryRelativePath)
                .SequenceEqual(
                    request.LocalAssets
                        .Select(asset => asset.RepositoryRelativePath)
                        .Order(StringComparer.Ordinal)))
        {
            throw new CSharpBuildGateOperationException(
                CSharpGateEvidenceLayer.Inventory,
                "Offline binding requires a stable exact local-asset inventory.");
        }

        foreach (var asset in request.LocalAssets)
        {
            var path = ExactPath(root, asset.RepositoryRelativePath);
            if (!File.Exists(path) ||
                !string.Equals(
                    asset.Digest.Value,
                    string.Concat("sha256:", FileDigest(path)),
                    StringComparison.OrdinalIgnoreCase))
            {
                throw new CSharpBuildGateOperationException(
                    CSharpGateEvidenceLayer.Inventory,
                    $"Local binding asset '{asset.RepositoryRelativePath}' is missing or changed.");
            }
        }

        return request.CandidateLock;
    }

    /// <inheritdoc />
    public ValueTask<CSharpGateCompilerHarnessResult> VerifyAsync(
        CSharpGateVerificationRequest request,
        CancellationToken cancellationToken) =>
        compilerHarness.VerifyAsync(request, cancellationToken);

    private static string ExactPath(string root, string relativePath)
    {
        if (string.IsNullOrWhiteSpace(relativePath) ||
            Path.IsPathRooted(relativePath) ||
            relativePath.Contains('\\', StringComparison.Ordinal) ||
            relativePath.Split('/').Any(segment => segment is "." or ".."))
        {
            throw new CSharpBuildGateOperationException(
                CSharpGateEvidenceLayer.Inventory,
                "Local binding paths must be exact repository-relative paths.");
        }

        var path = Path.GetFullPath(Path.Combine(
            root,
            relativePath.Replace('/', Path.DirectorySeparatorChar)));
        if (!path.StartsWith(
                string.Concat(
                    root.TrimEnd(
                        Path.DirectorySeparatorChar,
                        Path.AltDirectorySeparatorChar),
                    Path.DirectorySeparatorChar),
                StringComparison.OrdinalIgnoreCase))
        {
            throw new CSharpBuildGateOperationException(
                CSharpGateEvidenceLayer.Inventory,
                "A local binding path escapes the repository root.");
        }

        return path;
    }

    private static string FileDigest(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexStringLower(SHA256.HashData(stream));
    }

    private static string Kebab(string value)
    {
        var builder = new StringBuilder(value.Length + 8);
        for (var index = 0; index < value.Length; index++)
        {
            if (index > 0 && char.IsUpper(value[index]))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(value[index]));
        }

        return builder.ToString();
    }
}
