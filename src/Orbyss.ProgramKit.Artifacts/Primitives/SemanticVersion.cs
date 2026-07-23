using System.Diagnostics.CodeAnalysis;

namespace Orbyss.ProgramKit.Artifacts.Primitives;

/// <summary>A strict SemVer 2.0.0 version.</summary>
public readonly record struct SemanticVersion : IComparable<SemanticVersion>
{
    /// <summary>Initializes a validated semantic version.</summary>
    /// <exception cref="ArgumentException">The value is not SemVer 2.0.0.</exception>
    public SemanticVersion(string value)
    {
        if (!SemanticVersionParser.TryParse(value, out _))
        {
            throw new ArgumentException("The value must be a complete SemVer 2.0.0 version.", nameof(value));
        }

        Value = value;
    }

    /// <summary>Gets the original canonical version text.</summary>
    public string Value { get; }

    /// <summary>Parses a strict SemVer 2.0.0 version.</summary>
    public static SemanticVersion Parse(string value) => new(value);

    /// <summary>Attempts to parse a strict SemVer 2.0.0 version.</summary>
    public static bool TryParse(
        [NotNullWhen(true)] string? value,
        out SemanticVersion version)
    {
        if (SemanticVersionParser.TryParse(value, out _))
        {
            version = new SemanticVersion(value);
            return true;
        }

        version = default;
        return false;
    }

    /// <summary>Validates version text and returns a stable diagnostic on failure.</summary>
    public static ProgramKitValidationResult Validate(
        string? value,
        string path = "")
    {
        return SemanticVersionParser.TryParse(value, out _)
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(
            [
                new ProgramKitDiagnostic(
                    ArtifactDiagnosticIds.InvalidSemanticVersion,
                    ProgramKitDiagnosticSeverity.Error,
                    "The value must be a complete SemVer 2.0.0 version.",
                    path),
            ]);
    }

    /// <inheritdoc />
    public int CompareTo(SemanticVersion other)
    {
        if (!SemanticVersionParser.TryParse(Value, out var left))
        {
            return SemanticVersionParser.TryParse(other.Value, out _) ? -1 : 0;
        }

        if (!SemanticVersionParser.TryParse(other.Value, out var right))
        {
            return 1;
        }

        return left.CompareTo(right);
    }

    /// <summary>Returns whether the left version has lower SemVer precedence.</summary>
    public static bool operator <(SemanticVersion left, SemanticVersion right) =>
        left.CompareTo(right) < 0;

    /// <summary>Returns whether the left version has equal or lower SemVer precedence.</summary>
    public static bool operator <=(SemanticVersion left, SemanticVersion right) =>
        left.CompareTo(right) <= 0;

    /// <summary>Returns whether the left version has greater SemVer precedence.</summary>
    public static bool operator >(SemanticVersion left, SemanticVersion right) =>
        left.CompareTo(right) > 0;

    /// <summary>Returns whether the left version has equal or greater SemVer precedence.</summary>
    public static bool operator >=(SemanticVersion left, SemanticVersion right) =>
        left.CompareTo(right) >= 0;

    /// <inheritdoc />
    public override string ToString() => Value ?? string.Empty;
}
