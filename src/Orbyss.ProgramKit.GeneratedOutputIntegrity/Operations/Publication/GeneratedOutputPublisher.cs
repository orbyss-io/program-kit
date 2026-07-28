using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Sealing;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;

namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Publication;

/// <summary>Recoverable all-or-nothing publication for a newly generated host root.</summary>
public sealed class GeneratedOutputPublisher : IGeneratedOutputPublisher
{
    private const string StagedRootName = "root";
    private const string StagedAnchorName = "anchor.json";
    private const string ReadyMarkerName = "ready";

    private readonly IGeneratedOutputSealer sealer;
    private readonly IGeneratedOutputIntegrityVerifier verifier;

    /// <summary>Initializes publication with deterministic sealing and verification.</summary>
    public GeneratedOutputPublisher(
        IGeneratedOutputSealer sealer,
        IGeneratedOutputIntegrityVerifier verifier)
    {
        this.sealer = sealer ??
            throw new ArgumentNullException(nameof(sealer));
        this.verifier = verifier ??
            throw new ArgumentNullException(nameof(verifier));
    }

    /// <summary>Stages, seals, verifies, and publishes one absent generated root.</summary>
    public async ValueTask<GeneratedOutputSeal> PublishCreateAsync(
        string rootPath,
        IEnumerable<GeneratedOutputPayload> payloads,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(payloads);
        var root = GeneratedOutputPathPolicy.RequireAbsoluteRoot(rootPath);
        await RecoverAsync(root, cancellationToken).ConfigureAwait(false);
        var anchorPath = GeneratedOutputPathPolicy.AnchorPath(root);
        if (Directory.Exists(root) ||
            File.Exists(root) ||
            File.Exists(anchorPath) ||
            Directory.Exists(anchorPath))
        {
            throw new IOException(
                "The generated-output root or external anchor already exists.");
        }

        EnsureSafeParent(root);
        var materialized = payloads.ToImmutableArray();
        var seal = sealer.Seal(materialized);
        var transaction = GeneratedOutputPathPolicy.TransactionPath(root);
        Directory.CreateDirectory(transaction);
        var stagedRoot = Path.Combine(transaction, StagedRootName);
        Directory.CreateDirectory(stagedRoot);
        try
        {
            foreach (var payload in materialized
                         .OrderBy(
                             static payload => payload.RelativePath,
                             StringComparer.Ordinal))
            {
                cancellationToken.ThrowIfCancellationRequested();
                var path = GeneratedOutputPathPolicy.ResolveUnderRoot(
                    stagedRoot,
                    payload.RelativePath);
                await WriteNewAsync(
                    path,
                    payload.Content,
                    cancellationToken).ConfigureAwait(false);
            }

            var manifestPath = GeneratedOutputPathPolicy.ResolveUnderRoot(
                stagedRoot,
                GeneratedOutputIntegrityConstants.ManifestRelativePath,
                allowManifest: true);
            await WriteNewAsync(
                manifestPath,
                seal.ManifestBytes,
                cancellationToken).ConfigureAwait(false);
            await WriteNewAsync(
                Path.Combine(transaction, StagedAnchorName),
                seal.AnchorBytes,
                cancellationToken).ConfigureAwait(false);
            await WriteNewAsync(
                Path.Combine(transaction, ReadyMarkerName),
                "ready\n"u8.ToArray(),
                cancellationToken).ConfigureAwait(false);
        }
        catch
        {
            // Preserve the transaction for explicit deterministic recovery.
            throw;
        }

        await CompleteReadyTransactionAsync(root).ConfigureAwait(false);
        return seal;
    }

    /// <summary>Completes an interrupted ready transaction without regenerating.</summary>
    public async ValueTask RecoverAsync(
        string rootPath,
        CancellationToken cancellationToken)
    {
        var root = GeneratedOutputPathPolicy.RequireAbsoluteRoot(rootPath);
        var transaction = GeneratedOutputPathPolicy.TransactionPath(root);
        if (!Directory.Exists(transaction))
        {
            return;
        }

        cancellationToken.ThrowIfCancellationRequested();
        if (IsReparsePoint(transaction) ||
            !File.Exists(Path.Combine(transaction, ReadyMarkerName)))
        {
            throw new IOException(
                "The generated-output transaction is incomplete or unsafe and was preserved.");
        }

        await CompleteReadyTransactionAsync(root).ConfigureAwait(false);
    }

    private async ValueTask CompleteReadyTransactionAsync(string root)
    {
        var transaction = GeneratedOutputPathPolicy.TransactionPath(root);
        var stagedRoot = Path.Combine(transaction, StagedRootName);
        var stagedAnchor = Path.Combine(transaction, StagedAnchorName);
        var anchorPath = GeneratedOutputPathPolicy.AnchorPath(root);
        if (!Directory.Exists(root))
        {
            if (!Directory.Exists(stagedRoot))
            {
                throw new IOException(
                    "The ready generated-output transaction has no staged root.");
            }

            Directory.Move(stagedRoot, root);
        }
        else if (Directory.Exists(stagedRoot))
        {
            throw new IOException(
                "The generated root and staged root both exist; recovery is ambiguous.");
        }

        if (!File.Exists(anchorPath))
        {
            if (!File.Exists(stagedAnchor))
            {
                throw new IOException(
                    "The ready generated-output transaction has no staged anchor.");
            }

            File.Move(stagedAnchor, anchorPath);
        }

        var verification = await verifier.VerifyAsync(
            root,
            CancellationToken.None).ConfigureAwait(false);
        if (!verification.IsValid)
        {
            throw new IOException(
                "The recovered generated-output transaction failed integrity verification.");
        }

        Directory.Delete(transaction, recursive: true);
    }

    private static async ValueTask WriteNewAsync(
        string path,
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        var parent = Path.GetDirectoryName(path) ??
            throw new IOException(
                "A generated-output file has no parent directory.");
        Directory.CreateDirectory(parent);
        await using var stream = new FileStream(
            path,
            FileMode.CreateNew,
            FileAccess.Write,
            FileShare.None,
            bufferSize: 81920,
            FileOptions.Asynchronous | FileOptions.SequentialScan);
        await stream.WriteAsync(content, cancellationToken).ConfigureAwait(false);
        await stream.FlushAsync(cancellationToken).ConfigureAwait(false);
    }

    private static void EnsureSafeParent(string root)
    {
        var parent = Path.GetDirectoryName(root) ??
            throw new IOException(
                "The generated-output root has no parent directory.");
        if (!Directory.Exists(parent) || IsReparsePoint(parent))
        {
            throw new IOException(
                "The generated-output parent must be an existing ordinary directory.");
        }
    }

    private static bool IsReparsePoint(string path) =>
        (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0;
}
