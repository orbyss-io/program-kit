using System.Diagnostics.CodeAnalysis;

namespace Orbyss.ProgramKit.Artifacts.Primitives;

/// <summary>A lowercase, algorithm-qualified SHA-256 digest.</summary>
public readonly record struct Sha256Digest
{
    private const int PrefixLength = 7;
    private const int HexLength = 64;

    /// <summary>Initializes a validated digest.</summary>
    /// <exception cref="ArgumentException">The value is not a lowercase SHA-256 digest.</exception>
    public Sha256Digest(string value)
    {
        if (!IsValid(value))
        {
            throw new ArgumentException(
                "The value must use the form sha256: followed by 64 lowercase hexadecimal characters.",
                nameof(value));
        }

        Value = value;
    }

    /// <summary>Gets the algorithm-qualified digest text.</summary>
    public string Value { get; }

    /// <summary>Parses a lowercase, algorithm-qualified SHA-256 digest.</summary>
    public static Sha256Digest Parse(string value) => new(value);

    /// <summary>Attempts to parse a lowercase, algorithm-qualified SHA-256 digest.</summary>
    public static bool TryParse(
        [NotNullWhen(true)] string? value,
        out Sha256Digest digest)
    {
        if (IsValid(value))
        {
            digest = new Sha256Digest(value);
            return true;
        }

        digest = default;
        return false;
    }

    /// <summary>Validates digest text and returns a stable diagnostic on failure.</summary>
    public static ProgramKitValidationResult Validate(
        string? value,
        string path = "")
    {
        return IsValid(value)
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(
            [
                new ProgramKitDiagnostic(
                    ArtifactDiagnosticIds.InvalidSha256Digest,
                    ProgramKitDiagnosticSeverity.Error,
                    "The value must use the form sha256: followed by 64 lowercase hexadecimal characters.",
                    path),
            ]);
    }

    /// <inheritdoc />
    public override string ToString() => Value ?? string.Empty;

    private static bool IsValid([NotNullWhen(true)] string? value)
    {
        if (value is null ||
            value.Length != PrefixLength + HexLength ||
            !value.StartsWith("sha256:", StringComparison.Ordinal))
        {
            return false;
        }

        for (var index = PrefixLength; index < value.Length; index++)
        {
            if (value[index] is not (>= '0' and <= '9') and not (>= 'a' and <= 'f'))
            {
                return false;
            }
        }

        return true;
    }
}
