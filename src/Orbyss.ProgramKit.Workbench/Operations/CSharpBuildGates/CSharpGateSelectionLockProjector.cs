using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>
/// Projects one exact definition, lock intent, and named repository state into
/// a complete digest-bound selection-lock bind request.
/// </summary>
public sealed class CSharpGateSelectionLockProjector
{
    private static readonly SemanticVersion AlphaOne =
        new("0.1.0-alpha.1");
    private const string LockIntentSchema =
        "pkid:schema:program-kit:csharp-gate-lock-intent@0.1.0-alpha.1";
    private readonly IProgramKitJsonSerializer serializer;
    private readonly JsonSerializationProfileRef profile;
    private readonly JsonSerializationLimits limits;
    private readonly IProgramKitSemanticValidator<CSharpBuildGateDefinitionDocument>
        definitionValidator;
    private readonly IProgramKitSemanticValidator<CSharpBuildGateSelectionLockDocumentAlpha1>
        lockValidator;

    /// <summary>Initializes the projector with exact frozen JSON mechanics.</summary>
    public CSharpGateSelectionLockProjector(
        IProgramKitJsonSerializer serializer,
        JsonSerializationProfileRef profile,
        JsonSerializationLimits limits,
        IProgramKitSemanticValidator<CSharpBuildGateDefinitionDocument>
            definitionValidator,
        IProgramKitSemanticValidator<CSharpBuildGateSelectionLockDocumentAlpha1>
            lockValidator)
    {
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
        this.profile = profile ??
            throw new ArgumentNullException(nameof(profile));
        this.limits = limits ??
            throw new ArgumentNullException(nameof(limits));
        this.definitionValidator = definitionValidator ??
            throw new ArgumentNullException(nameof(definitionValidator));
        this.lockValidator = lockValidator ??
            throw new ArgumentNullException(nameof(lockValidator));
    }

    /// <summary>Creates a complete bind request from explicit inputs.</summary>
    public CSharpGateBindRequestAlpha1 Scaffold(
        CSharpBuildGateDefinitionDocument definition,
        string definitionRepositoryRelativePath,
        CSharpGateLockIntent intent,
        string repositoryRoot)
    {
        ArgumentNullException.ThrowIfNull(definition);
        ArgumentNullException.ThrowIfNull(intent);
        var definitionValidation = definitionValidator.Validate(definition);
        if (!definitionValidation.IsValid)
        {
            throw Failure(
                "The gate definition is not valid enough to scaffold a lock.");
        }

        ValidateIntent(intent);
        var root = ExactRoot(repositoryRoot);
        var definitionPath = ExactPath(
            root,
            definitionRepositoryRelativePath);
        if (!File.Exists(definitionPath))
        {
            throw Failure("The exact gate definition file is missing.");
        }

        var onDiskDefinition = serializer.Read<CSharpBuildGateDefinitionDocument>(
            File.ReadAllBytes(definitionPath),
            profile,
            limits);
        var definitionBytes = serializer.Write(
            definition,
            profile,
            limits);
        var onDiskDefinitionBytes = serializer.Write(
            onDiskDefinition,
            profile,
            limits);
        if (!definitionBytes.ToArray().AsSpan().SequenceEqual(
                onDiskDefinitionBytes.ToArray()))
        {
            throw Failure(
                "The supplied definition differs from the exact repository definition bytes.");
        }

        var definitionReference = new ArtifactReference(
            definition.Identity,
            definition.Version,
            definitionBytes.Digest);
        if (intent.Disposition != definition.Disposition)
        {
            throw Failure(
                "The lock intent disposition must equal the definition disposition.");
        }

        var inventories = CreateInventories(definition, intent, root);
        var localAssets = inventories.All
            .Append(new CSharpGateLocalAssetBinding(
                definitionRepositoryRelativePath,
                FileDigest(definitionPath)))
            .OrderBy(
                static asset => asset.RepositoryRelativePath,
                StringComparer.Ordinal)
            .ToImmutableArray();
        RequireUniquePaths(localAssets);
        var receipts = ExpectedReceipts(definition, intent);
        var inputDigest = serializer.Write(
            new CSharpGateLockInputProjection(
                definitionReference,
                intent,
                intent.SdkVersion,
                intent.CompilerRoslynVersion,
                intent.LanguageVersion,
                intent.TargetFramework,
                localAssets),
            profile,
            limits).Digest;
        var lockWithoutOutput = new CSharpGateSelectionLockOutputProjection(
            intent.LockIdentity,
            AlphaOne,
            intent.Disposition,
            definitionReference,
            AnalyzerReferences(definition),
            Reference(definition.RuleCatalog),
            intent.Recipes
                .OrderBy(
                    CSharpBuildGateOrdering.ArtifactReferenceKey,
                    StringComparer.Ordinal)
                .ToImmutableArray(),
            Reference(definition.ActivationMatrix),
            Reference(definition.SuppressionLedger),
            intent.OperationRevisions
                .OrderBy(
                    CSharpBuildGateOrdering.ArtifactReferenceKey,
                    StringComparer.Ordinal)
                .ToImmutableArray(),
            inventories.Project,
            inventories.PhysicalSource,
            inventories.GeneratedSource,
            inventories.Reference,
            inventories.AdditionalFile,
            inventories.AnalyzerConfiguration,
            intent.SdkVersion,
            intent.CompilerRoslynVersion,
            intent.LanguageVersion,
            intent.TargetFramework,
            receipts,
            inputDigest);
        var outputDigest = serializer.Write(
            lockWithoutOutput,
            profile,
            limits).Digest;
        var candidate = new CSharpBuildGateSelectionLockDocumentAlpha1(
            lockWithoutOutput.Identity,
            lockWithoutOutput.Version,
            lockWithoutOutput.Disposition,
            lockWithoutOutput.GateDefinition,
            lockWithoutOutput.AnalyzerComponents,
            lockWithoutOutput.RuleCatalog,
            lockWithoutOutput.Recipes,
            lockWithoutOutput.ActivationMatrix,
            lockWithoutOutput.SuppressionLedger,
            lockWithoutOutput.OperationRevisions,
            lockWithoutOutput.ProjectInventory,
            lockWithoutOutput.PhysicalSourceInventory,
            lockWithoutOutput.GeneratedSourceInventory,
            lockWithoutOutput.ReferenceInventory,
            lockWithoutOutput.AdditionalFileInventory,
            lockWithoutOutput.AnalyzerConfigurationInventory,
            lockWithoutOutput.SdkVersion,
            lockWithoutOutput.CompilerRoslynVersion,
            lockWithoutOutput.LanguageVersion,
            lockWithoutOutput.TargetFramework,
            lockWithoutOutput.ExpectedReceipts,
            lockWithoutOutput.InputDigest,
            outputDigest);
        if (!lockValidator.Validate(candidate).IsValid)
        {
            throw Failure(
                "The derived selection lock did not satisfy its exact alpha.1 contract.");
        }

        return new CSharpGateBindRequestAlpha1(
            AlphaOne,
            root,
            definitionRepositoryRelativePath,
            intent,
            candidate,
            localAssets);
    }

    /// <summary>Recomputes and verifies the complete candidate request.</summary>
    public CSharpBuildGateSelectionLockDocumentAlpha1 Bind(
        CSharpGateBindRequestAlpha1 request)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (request.Version != AlphaOne)
        {
            throw Failure(
                "The bind request version must be 0.1.0-alpha.1.");
        }

        var root = ExactRoot(request.RepositoryRoot);
        var definitionPath = ExactPath(
            root,
            request.DefinitionRepositoryRelativePath);
        if (!File.Exists(definitionPath))
        {
            throw Failure("The exact gate definition file is missing.");
        }

        var definition = serializer.Read<CSharpBuildGateDefinitionDocument>(
            File.ReadAllBytes(definitionPath),
            profile,
            limits);
        var expected = Scaffold(
            definition,
            request.DefinitionRepositoryRelativePath,
            request.LockIntent,
            root);
        var candidateBytes = serializer.Write(
            request.CandidateLock,
            profile,
            limits);
        var expectedBytes = serializer.Write(
            expected.CandidateLock,
            profile,
            limits);
        if (!candidateBytes.ToArray().AsSpan().SequenceEqual(
                expectedBytes.ToArray()))
        {
            throw Failure(
                "The candidate lock differs from the mechanically recomputed lock.");
        }

        if (!request.LocalAssets.SequenceEqual(expected.LocalAssets))
        {
            throw Failure(
                "The local-asset inventory differs from the mechanically recomputed inventory.");
        }

        return expected.CandidateLock;
    }

    private static void ValidateIntent(CSharpGateLockIntent intent)
    {
        if (!string.Equals(
                intent.Schema,
                LockIntentSchema,
                StringComparison.Ordinal) ||
            intent.Version != AlphaOne ||
            intent.LockIdentity.Value is null ||
            intent.Disposition is null ||
            intent.OperationRevisions.IsDefaultOrEmpty ||
            string.IsNullOrWhiteSpace(intent.TargetFramework) ||
            !string.Equals(
                intent.ReceiptIdentityNamespace.Kind,
                "receipt",
                StringComparison.Ordinal) ||
            intent.LocalAssets.IsDefault)
        {
            throw Failure(
                "The lock intent is incomplete or has an unsupported alpha.1 value.");
        }

        var operationKeys = intent.OperationRevisions
            .Select(CSharpBuildGateOrdering.ArtifactReferenceKey)
            .ToArray();
        if (!operationKeys.SequenceEqual(
                operationKeys.Order(StringComparer.Ordinal)) ||
            operationKeys.Distinct(StringComparer.Ordinal).Count() !=
                operationKeys.Length)
        {
            throw Failure(
                "Operation revisions must be unique and ordered by exact artifact-reference key.");
        }

        var recipeKeys = intent.Recipes
            .Select(CSharpBuildGateOrdering.ArtifactReferenceKey)
            .ToArray();
        if (!recipeKeys.SequenceEqual(recipeKeys.Order(StringComparer.Ordinal)) ||
            recipeKeys.Distinct(StringComparer.Ordinal).Count() !=
                recipeKeys.Length)
        {
            throw Failure(
                "Recipe references must be unique and ordered by exact artifact-reference key.");
        }

        var assetKeys = intent.LocalAssets
            .Select(static asset => string.Join(
                "|",
                CSharpBuildGateOrdering.Kebab(asset.Kind),
                asset.RepositoryRelativePath))
            .ToArray();
        if (!assetKeys.SequenceEqual(assetKeys.Order(StringComparer.Ordinal)) ||
            assetKeys.Distinct(StringComparer.Ordinal).Count() !=
                assetKeys.Length)
        {
            throw Failure(
                "Local asset intents must be unique and ordered by kind|repositoryRelativePath.");
        }
    }

    private static CSharpGateLockInventorySet CreateInventories(
        CSharpBuildGateDefinitionDocument definition,
        CSharpGateLockIntent intent,
        string root)
    {
        Dictionary<string, InventoryRow> selected =
            new(StringComparer.Ordinal);
        foreach (var project in definition.Profiles.Projects)
        {
            Add(
                selected,
                CSharpGateLockInventoryKind.Project,
                project.RepositoryRelativeProjectPath,
                expectedDigest: null,
                root,
                fromIntent: false);
        }

        foreach (var component in definition.AnalyzerComponents.Where(
                     static component =>
                         component.Artifact.Kind ==
                         CSharpAnalyzerArtifactKind.LocalNonPackableProject))
        {
            Add(
                selected,
                CSharpGateLockInventoryKind.Project,
                component.Artifact.RepositoryRelativeProjectPath!,
                expectedDigest: null,
                root,
                fromIntent: false);
        }

        foreach (var profile in definition.Profiles.Inputs)
        {
            var kind = profile.Kind switch
            {
                CSharpGateInputKind.PhysicalSource =>
                    CSharpGateLockInventoryKind.PhysicalSource,
                CSharpGateInputKind.ConsumerGeneratedSource or
                CSharpGateInputKind.ExternalGeneratedSource =>
                    CSharpGateLockInventoryKind.GeneratedSource,
                CSharpGateInputKind.AdditionalFile =>
                    CSharpGateLockInventoryKind.AdditionalFile,
                CSharpGateInputKind.AnalyzerConfiguration =>
                    CSharpGateLockInventoryKind.AnalyzerConfiguration,
                _ => throw Failure(
                    "The definition contains an unsupported input inventory kind."),
            };
            foreach (var item in profile.Inventory)
            {
                Add(
                    selected,
                    kind,
                    item.RepositoryRelativePath,
                    item.Digest,
                    root,
                    fromIntent: false);
            }
        }

        foreach (var profile in definition.Profiles.GeneratedSources)
        {
            foreach (var item in profile.Inventory)
            {
                Add(
                    selected,
                    CSharpGateLockInventoryKind.GeneratedSource,
                    item.RepositoryRelativePath,
                    item.Digest,
                    root,
                    fromIntent: false);
            }
        }

        foreach (var asset in intent.LocalAssets)
        {
            Add(
                selected,
                asset.Kind,
                asset.RepositoryRelativePath,
                expectedDigest: null,
                root,
                fromIntent: true);
        }

        var referenceRows = selected.Values
            .Where(static row =>
                row.Kind == CSharpGateLockInventoryKind.Reference)
            .ToArray();
        foreach (var component in definition.AnalyzerComponents)
        {
            var matches = referenceRows.Count(row =>
                string.Equals(
                    Path.GetFileName(row.Content.RepositoryRelativePath),
                    component.Artifact.AssemblyFileName,
                    StringComparison.Ordinal) &&
                row.Content.Digest == component.Artifact.AssemblyDigest);
            if (matches != 1)
            {
                throw Failure(
                    string.Concat(
                        "Analyzer component '",
                        component.Identity.Value,
                        "' requires exactly one explicit reference asset whose file name and digest match the selected assembly."));
            }
        }

        return new CSharpGateLockInventorySet(
            Rows(selected, CSharpGateLockInventoryKind.Project),
            Rows(selected, CSharpGateLockInventoryKind.PhysicalSource),
            Rows(selected, CSharpGateLockInventoryKind.GeneratedSource),
            Rows(selected, CSharpGateLockInventoryKind.Reference),
            Rows(selected, CSharpGateLockInventoryKind.AdditionalFile),
            Rows(
                selected,
                CSharpGateLockInventoryKind.AnalyzerConfiguration));
    }

    private static void Add(
        Dictionary<string, InventoryRow> selected,
        CSharpGateLockInventoryKind kind,
        string relativePath,
        Sha256Digest? expectedDigest,
        string root,
        bool fromIntent)
    {
        var path = ExactPath(root, relativePath);
        if (!File.Exists(path))
        {
            throw Failure(
                string.Concat(
                    "The exact local asset is missing: ",
                    relativePath,
                    "."));
        }

        var digest = FileDigest(path);
        if (expectedDigest is not null && digest != expectedDigest.Value)
        {
            throw Failure(
                string.Concat(
                    "The exact local asset is stale: ",
                    relativePath,
                    "."));
        }

        if (selected.TryGetValue(relativePath, out var existing))
        {
            if (!fromIntent &&
                existing.Kind == kind &&
                existing.Content.Digest == digest)
            {
                return;
            }

            throw Failure(
                string.Concat(
                    "The local asset is selected more than once: ",
                    relativePath,
                    "."));
        }

        selected.Add(
            relativePath,
            new InventoryRow(
                kind,
                new CSharpGateLockedContent(relativePath, digest)));
    }

    private static ImmutableArray<ArtifactReference> AnalyzerReferences(
        CSharpBuildGateDefinitionDocument definition) =>
        definition.AnalyzerComponents
            .Select(component => new ArtifactReference(
                component.Identity,
                component.Artifact.Package?.Version ?? definition.Version,
                component.Artifact.AssemblyDigest))
            .OrderBy(
                CSharpBuildGateOrdering.ArtifactReferenceKey,
                StringComparer.Ordinal)
            .ToImmutableArray();

    private ArtifactReference Reference(CSharpGateRuleCatalog catalog) =>
        new(
            catalog.Identity,
            catalog.Version,
            serializer.Write(catalog, profile, limits).Digest);

    private ArtifactReference Reference(CSharpGateActivationMatrix matrix) =>
        new(
            matrix.Identity,
            matrix.Version,
            serializer.Write(matrix, profile, limits).Digest);

    private ArtifactReference Reference(CSharpGateSuppressionLedger ledger) =>
        new(
            ledger.Identity,
            ledger.Version,
            serializer.Write(ledger, profile, limits).Digest);

    private static ImmutableArray<CSharpGateExpectedReceipt> ExpectedReceipts(
        CSharpBuildGateDefinitionDocument definition,
        CSharpGateLockIntent intent) =>
        definition.ActivationMatrix.Activations
            .SelectMany(activation =>
                activation.AnalyzerComponentIds.Select(component =>
                    new CSharpGateExpectedReceipt(
                        activation.ProjectProfileId,
                        component,
                        activation.VerificationProfile,
                        ReceiptIdentity(
                            intent.ReceiptIdentityNamespace,
                            activation.ProjectProfileId,
                            component,
                            activation.VerificationProfile))))
            .Distinct()
            .OrderBy(
                CSharpBuildGateOrdering.ExpectedReceiptKey,
                StringComparer.Ordinal)
            .ToImmutableArray();

    private static ProgramKitIdentifier ReceiptIdentity(
        ProgramKitIdentifier @namespace,
        ProgramKitIdentifier project,
        ProgramKitIdentifier analyzer,
        CSharpGateVerificationProfileKind profile) =>
        new(
            string.Join(
                ":",
                "pkid",
                "receipt",
                @namespace.Scope,
                string.Join(
                    "-",
                    @namespace.Name,
                    project.Name,
                    analyzer.Name,
                    CSharpBuildGateOrdering.Kebab(profile))));

    private static ImmutableArray<CSharpGateLockedContent> Rows(
        IReadOnlyDictionary<string, InventoryRow> selected,
        CSharpGateLockInventoryKind kind) =>
        selected.Values
            .Where(row => row.Kind == kind)
            .Select(static row => row.Content)
            .OrderBy(
                CSharpBuildGateOrdering.InventoryKey,
                StringComparer.Ordinal)
            .ToImmutableArray();

    private static string ExactRoot(string repositoryRoot)
    {
        var root = Path.GetFullPath(repositoryRoot);
        if (!Directory.Exists(root))
        {
            throw Failure("The exact repository root does not exist.");
        }

        return root.TrimEnd(
            Path.DirectorySeparatorChar,
            Path.AltDirectorySeparatorChar);
    }

    private static string ExactPath(string root, string relativePath)
    {
        if (string.IsNullOrWhiteSpace(relativePath) ||
            relativePath != relativePath.Trim() ||
            Path.IsPathRooted(relativePath) ||
            relativePath.Contains('\\', StringComparison.Ordinal) ||
            relativePath.Contains('*', StringComparison.Ordinal) ||
            relativePath.Contains('?', StringComparison.Ordinal) ||
            relativePath.Split('/').Any(static segment =>
                segment.Length == 0 || segment is "." or ".."))
        {
            throw Failure(
                "Local binding paths must be exact normalized repository-relative paths.");
        }

        var path = Path.GetFullPath(
            Path.Combine(
                root,
                relativePath.Replace(
                    '/',
                    Path.DirectorySeparatorChar)));
        if (!path.StartsWith(
                string.Concat(root, Path.DirectorySeparatorChar),
                StringComparison.OrdinalIgnoreCase))
        {
            throw Failure("A local binding path escapes the repository root.");
        }

        return path;
    }

    private static Sha256Digest FileDigest(string path)
    {
        using var stream = File.OpenRead(path);
        return new Sha256Digest(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(stream))));
    }

    private static void RequireUniquePaths(
        ImmutableArray<CSharpGateLocalAssetBinding> assets)
    {
        var duplicate = assets
            .GroupBy(
                static asset => asset.RepositoryRelativePath,
                StringComparer.Ordinal)
            .FirstOrDefault(static group => group.Count() > 1);
        if (duplicate is not null)
        {
            throw Failure(
                string.Concat(
                    "The local-asset inventory contains duplicate path '",
                    duplicate.Key,
                    "'."));
        }
    }

    private static CSharpBuildGateOperationException Failure(string message) =>
        new(CSharpGateEvidenceLayer.Inventory, message);

}
