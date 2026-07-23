using System.Diagnostics.CodeAnalysis;

namespace Orbyss.ProgramKit.Artifacts.Primitives;

/// <summary>A deterministic exact or NuGet-style interval over SemVer versions.</summary>
public readonly record struct SemanticVersionRange
{
    /// <summary>Initializes a validated version range.</summary>
    /// <exception cref="ArgumentException">The range is unsupported or malformed.</exception>
    public SemanticVersionRange(string value)
    {
        if (!TryValidate(value))
        {
            throw new ArgumentException(
                "The value must be a SemVer version or a NuGet-style SemVer interval.",
                nameof(value));
        }

        Value = value;
    }

    /// <summary>Gets the range text.</summary>
    public string Value { get; }

    /// <summary>Parses a supported deterministic version range.</summary>
    public static SemanticVersionRange Parse(string value) => new(value);

    /// <summary>Attempts to parse a supported deterministic version range.</summary>
    public static bool TryParse(
        [NotNullWhen(true)] string? value,
        out SemanticVersionRange range)
    {
        if (TryValidate(value))
        {
            range = new SemanticVersionRange(value);
            return true;
        }

        range = default;
        return false;
    }

    /// <summary>Validates range text and returns a stable diagnostic on failure.</summary>
    public static ProgramKitValidationResult Validate(
        string? value,
        string path = "")
    {
        return TryValidate(value)
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(
            [
                new ProgramKitDiagnostic(
                    ArtifactDiagnosticIds.InvalidSemanticVersionRange,
                    ProgramKitDiagnosticSeverity.Error,
                    "The value must be a SemVer version or a NuGet-style SemVer interval with at least one bound.",
                    path),
            ]);
    }

    /// <summary>Returns whether a version is contained in this exact or interval range.</summary>
    public bool Contains(SemanticVersion version)
    {
        if (!TryValidate(Value) || string.IsNullOrEmpty(version.Value))
        {
            return false;
        }

        if (SemanticVersion.TryParse(Value, out var exact))
        {
            return string.Equals(exact.Value, version.Value, StringComparison.Ordinal);
        }

        var inner = Value[1..^1];
        var commaIndex = inner.IndexOf(',');
        if (commaIndex < 0)
        {
            return string.Equals(inner, version.Value, StringComparison.Ordinal);
        }

        var lowerText = inner[..commaIndex];
        var upperText = inner[(commaIndex + 1)..];
        if (lowerText.Length > 0)
        {
            var comparison = version.CompareTo(SemanticVersion.Parse(lowerText));
            if (comparison < 0 || (comparison == 0 && Value[0] == '('))
            {
                return false;
            }
        }

        if (upperText.Length > 0)
        {
            var comparison = version.CompareTo(SemanticVersion.Parse(upperText));
            if (comparison > 0 || (comparison == 0 && Value[^1] == ')'))
            {
                return false;
            }
        }

        return true;
    }

    /// <inheritdoc />
    public override string ToString() => Value ?? string.Empty;

    private static bool TryValidate([NotNullWhen(true)] string? value)
    {
        if (SemanticVersion.TryParse(value, out _))
        {
            return true;
        }

        if (string.IsNullOrEmpty(value) || value.Length < 3)
        {
            return false;
        }

        var opens = value[0] is '[' or '(';
        var closes = value[^1] is ']' or ')';
        if (!opens || !closes)
        {
            return false;
        }

        var inner = value[1..^1];
        var commaIndex = inner.IndexOf(',');
        if (commaIndex < 0)
        {
            return value[0] == '[' &&
                   value[^1] == ']' &&
                   SemanticVersion.TryParse(inner, out _);
        }

        if (inner.IndexOf(',', commaIndex + 1) >= 0)
        {
            return false;
        }

        var lowerText = inner[..commaIndex];
        var upperText = inner[(commaIndex + 1)..];
        if (lowerText.Length == 0 && upperText.Length == 0)
        {
            return false;
        }

        if (lowerText.Length > 0 && !SemanticVersion.TryParse(lowerText, out _))
        {
            return false;
        }

        if (upperText.Length > 0 && !SemanticVersion.TryParse(upperText, out _))
        {
            return false;
        }

        if (lowerText.Length == 0 && value[0] != '(')
        {
            return false;
        }

        if (upperText.Length == 0 && value[^1] != ')')
        {
            return false;
        }

        if (lowerText.Length > 0 && upperText.Length > 0)
        {
            var boundsComparison =
                SemanticVersion.Parse(lowerText).CompareTo(SemanticVersion.Parse(upperText));
            if (boundsComparison > 0 ||
                (boundsComparison == 0 && (value[0] == '(' || value[^1] == ')')))
            {
                return false;
            }
        }

        return true;
    }
}
