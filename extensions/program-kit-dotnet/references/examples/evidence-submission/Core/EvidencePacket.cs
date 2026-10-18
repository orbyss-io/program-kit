using System.Security.Cryptography;
using System.Text;

namespace ProgramKit.Examples.Evidence;

/// <summary>A valid, immutable fictional submission; no transport, storage or activation dependencies.</summary>
public sealed class EvidencePacket
{
    /// <summary>The Core content bound projected through the actual input contract.</summary>
    public const int MaximumContentBytes = 16384;
    /// <summary>The Core title bound projected through the actual input contract.</summary>
    public const int MaximumTitleLength = 80;
    /// <summary>Private copied bytes; callers receive a new buffer instead of this owned state.</summary>
    private readonly byte[] content;

    /// <summary>Keeps the named admission or projection step within its owning type.</summary>
    private EvidencePacket(
        string title,
        DateOnly date,
        byte[] bytes,
        string hash
    )
    {
        Title = title;
        Date = date;
        content = bytes;
        Hash = hash;
    }

    /// <summary>The owned title value.</summary>
    public string Title { get; }
    /// <summary>The owned date value.</summary>
    public DateOnly Date { get; }
    /// <summary>The owned hash value.</summary>
    public string Hash { get; }
    /// <summary>Returns a new caller-owned buffer.</summary>
    public byte[] CopyContent() => content.ToArray();

    /// <summary>Admits valid UTF-8 content and copies ownership before publication.</summary>
    public static EvidencePacket Create(
        string title,
        DateOnly date,
        byte[] bytes
    )
    {
        ArgumentNullException.ThrowIfNull(bytes);
        if (string.IsNullOrWhiteSpace(title) || title.Length > MaximumTitleLength || title.Any(char.IsControl))
            throw new ArgumentException("Enter a bounded title without control characters.");
        if (date == default || bytes.Length < 1 || bytes.Length > MaximumContentBytes)
            throw new ArgumentException("Select a date and a text file within the declared limit.");
        var utf8 = new UTF8Encoding(false, true);
        _ = utf8.GetString(bytes);
        var owned = bytes.ToArray();
        var digest = SHA256.HashData(owned);
        var hash = Convert.ToHexStringLower(digest);
        return new EvidencePacket(
            title,
            date,
            owned,
            hash
        );
    }
}
