using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Files;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

/// <summary>Deterministic Markdown projection of the canonical capability index.</summary>
public sealed class CapabilityCatalogRenderer : ICapabilityCatalogRenderer
{
    private const string CanonicalIndexPath =
        ".agent-capabilities/capabilities/INDEX.md";
    private readonly ICommandFileSystem fileSystem;
    private readonly ICapabilityIndexParser parser;

    /// <summary>Initializes the renderer with explicit file and parsing behavior.</summary>
    public CapabilityCatalogRenderer(
        ICommandFileSystem fileSystem,
        ICapabilityIndexParser parser)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.parser = parser ??
            throw new ArgumentNullException(nameof(parser));
    }

    /// <inheritdoc />
    public async ValueTask<ReadOnlyMemory<byte>> RenderAsync(
        string indexPath,
        string outputPath,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(indexPath);
        ArgumentException.ThrowIfNullOrWhiteSpace(outputPath);
        RequireCanonicalIndexPath(indexPath);
        var content = await fileSystem.ReadAllBytesAsync(
            indexPath,
            cancellationToken).ConfigureAwait(false);
        var document = parser.Parse(content.Span);
        var digest = string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content.Span))
                .ToLowerInvariant());
        var rendered = Render(document, digest);
        if (string.Equals(outputPath, "-", StringComparison.Ordinal))
        {
            return rendered;
        }

        await fileSystem.WriteAllBytesAsync(
            outputPath,
            rendered,
            cancellationToken).ConfigureAwait(false);
        return default;
    }

    /// <summary>Renders one parsed document with an exact source digest.</summary>
    public static ReadOnlyMemory<byte> Render(
        CapabilityIndexDocument document,
        string sourceDigest)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceDigest);
        var builder = new StringBuilder();
        builder.AppendLine("# Capability catalog");
        builder.AppendLine();
        builder.AppendLine(
            "This file is a generated, non-authoritative projection of " +
            "[`INDEX.md`](INDEX.md).");
        builder.AppendLine(
            "Capability availability is owned only by the canonical index.");
        builder.AppendLine();
        builder.Append("Source path: `");
        builder.Append(CanonicalIndexPath);
        builder.AppendLine("`");
        builder.Append("Source digest: `");
        builder.Append(sourceDigest);
        builder.AppendLine("`");
        builder.AppendLine();
        builder.AppendLine(
            "| Capability ID | Flow category | Status | Canonical definition | Provider adapter template | Notes |");
        builder.AppendLine("| --- | --- | --- | --- | --- | --- |");
        foreach (var entry in document.Entries)
        {
            builder.Append("| `");
            builder.Append(entry.CapabilityId);
            builder.Append("` | ");
            builder.Append(entry.FlowCategory);
            builder.Append(" | ");
            builder.Append(entry.Status);
            builder.Append(" | ");
            builder.Append(
                entry.CanonicalDefinition is null
                    ? "Not created"
                    : $"[CAPABILITY.md]({entry.CanonicalDefinition})");
            builder.Append(" | ");
            builder.Append(
                entry.ProviderAdapterTemplate is null
                    ? "Not registered"
                    : $"[Codex adapter template]({entry.ProviderAdapterTemplate})");
            builder.Append(" | ");
            builder.Append(entry.Notes);
            builder.AppendLine(" |");
        }

        return Encoding.UTF8.GetBytes(
            builder.ToString().Replace("\r\n", "\n", StringComparison.Ordinal));
    }

    private static void RequireCanonicalIndexPath(string indexPath)
    {
        var normalized = Path
            .GetFullPath(indexPath)
            .Replace('\\', '/');
        if (!normalized.EndsWith(
                string.Concat("/", CanonicalIndexPath),
                StringComparison.Ordinal))
        {
            throw new CapabilityOperationException(
                CommandExitCode.UsageOrInputFailure,
                CommandDiagnosticIds.InvalidCapabilityIndex,
                "/index",
                $"The catalog source must be the canonical path '{CanonicalIndexPath}'.");
        }
    }
}
