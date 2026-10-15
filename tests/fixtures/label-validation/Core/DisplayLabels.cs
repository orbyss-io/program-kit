using System.Globalization;
using System.Security.Cryptography;
using System.Text;

namespace LabelOwner.Core;

/// <summary>Owns synthetic fixture label policy independently of JSON export and browser representation.</summary>
public static class DisplayLabels
{
    /// <summary>The immutable semantic owner identity.</summary>
    public const string Owner = "LabelOwner";
    /// <summary>The owner protocol identity; a display label never supplies it.</summary>
    public const string ContractId = "LabelOwner.Creation";
    /// <summary>The current owner contract revision.</summary>
    public const int ContractVersion = 1;
    /// <summary>The stable label-rule identity.</summary>
    public const string RuleId = "LabelOwner.DisplayLabel";
    /// <summary>The current source-owned rule revision.</summary>
    public const int RuleVersion = 1;
    /// <summary>The minimum admitted normalized UTF-16 length.</summary>
    public const int MinimumLength = 1;
    /// <summary>The maximum admitted normalized UTF-16 length.</summary>
    public const int MaximumLength = 120;
    /// <summary>The unit already used by the owned string-length predicate.</summary>
    public const string LengthUnit = "utf16";
    /// <summary>The explicit admission order implemented below.</summary>
    public static IReadOnlyList<string> NormalizationOrder { get; } = Array.AsReadOnly(new[] { "rejectRawControls", "trim", "validateUtf16Length" });
    /// <summary>The exact character predicate used by the owned .NET Trim operation.</summary>
    public static IReadOnlyList<int> TrimCodeUnits { get; } = Array.AsReadOnly(Enumerable.Range(0, 65536).Where(unit => char.IsWhiteSpace((char)unit)).ToArray());
    /// <summary>Rejects raw controls before any normalization can hide them.</summary>
    public static bool IsForbiddenRawCharacter(char value) => char.IsControl(value);

    /// <summary>Returns admitted normalized content, preserving UTF-16 bounds and raw-control refusal.</summary>
    public static string? Normalize(string? raw)
    {
        if (raw is null || raw.Any(IsForbiddenRawCharacter)) return null;
        var value = raw.Trim();
        return value.Length >= MinimumLength && value.Length <= MaximumLength ? value : null;
    }

    /// <summary>Binds the admitted content through a stable UTF-8 byte-length-prefixed protocol.</summary>
    public static string Digest(string normalized)
    {
        var binding = "CreatePolicy:v1\n" + Encoding.UTF8.GetByteCount(normalized).ToString(CultureInfo.InvariantCulture) + ":" + normalized;
        return Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(binding)));
    }
}
