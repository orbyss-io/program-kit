using System.Diagnostics.CodeAnalysis;

namespace Orbyss.ProgramKit.Artifacts;

/// <summary>A stable Program Kit semantic identifier.</summary>
public readonly record struct ProgramKitIdentifier
{
    /// <summary>Initializes a validated Program Kit identifier.</summary>
    /// <exception cref="ArgumentException">The value does not match the PKID grammar.</exception>
    public ProgramKitIdentifier(string value)
    {
        if (!IsValid(value))
        {
            throw new ArgumentException(
                "A Program Kit identifier must match pkid:<kind>:<scope>:<name> using lowercase ASCII kebab-case tokens.",
                nameof(value));
        }

        Value = value;
    }

    /// <summary>Gets the canonical identifier text.</summary>
    public string Value { get; }

    /// <summary>Gets the identifier kind.</summary>
    public string Kind => GetToken(1);

    /// <summary>Gets the identifier scope.</summary>
    public string Scope => GetToken(2);

    /// <summary>Gets the identifier name.</summary>
    public string Name => GetToken(3);

    /// <summary>Parses a validated Program Kit identifier.</summary>
    public static ProgramKitIdentifier Parse(string value) => new(value);

    /// <summary>Attempts to parse a Program Kit identifier.</summary>
    public static bool TryParse(
        [NotNullWhen(true)] string? value,
        out ProgramKitIdentifier identifier)
    {
        if (IsValid(value))
        {
            identifier = new ProgramKitIdentifier(value);
            return true;
        }

        identifier = default;
        return false;
    }

    /// <summary>Validates identifier text and returns a stable diagnostic on failure.</summary>
    public static ProgramKitValidationResult Validate(
        string? value,
        string path = "")
    {
        return IsValid(value)
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(
            [
                new ProgramKitDiagnostic(
                    ArtifactDiagnosticIds.InvalidProgramKitIdentifier,
                    ProgramKitDiagnosticSeverity.Error,
                    "The value must match pkid:<kind>:<scope>:<name> using lowercase ASCII kebab-case tokens.",
                    path),
            ]);
    }

    /// <inheritdoc />
    public override string ToString() => Value ?? string.Empty;

    private static bool IsValid([NotNullWhen(true)] string? value)
    {
        if (string.IsNullOrEmpty(value) || !value.StartsWith("pkid:", StringComparison.Ordinal))
        {
            return false;
        }

        var segments = value.Split(':');
        return segments.Length == 4 &&
               segments[0] == "pkid" &&
               IsKebabToken(segments[1]) &&
               IsKebabToken(segments[2]) &&
               IsKebabToken(segments[3]);
    }

    private static bool IsKebabToken(string value)
    {
        if (value.Length == 0 || value[0] == '-' || value[^1] == '-')
        {
            return false;
        }

        var previousWasHyphen = false;
        foreach (var character in value)
        {
            var isLowerAscii = character is >= 'a' and <= 'z';
            var isDigit = character is >= '0' and <= '9';
            var isHyphen = character == '-';
            if (!isLowerAscii && !isDigit && !isHyphen)
            {
                return false;
            }

            if (isHyphen && previousWasHyphen)
            {
                return false;
            }

            previousWasHyphen = isHyphen;
        }

        return true;
    }

    private string GetToken(int index)
    {
        if (string.IsNullOrEmpty(Value))
        {
            return string.Empty;
        }

        return Value.Split(':')[index];
    }
}

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

internal readonly record struct ParsedSemanticVersion(
    string Major,
    string Minor,
    string Patch,
    string[] Prerelease) : IComparable<ParsedSemanticVersion>
{
    public int CompareTo(ParsedSemanticVersion other)
    {
        var coreComparison = CompareNumericIdentifier(Major, other.Major);
        if (coreComparison != 0)
        {
            return coreComparison;
        }

        coreComparison = CompareNumericIdentifier(Minor, other.Minor);
        if (coreComparison != 0)
        {
            return coreComparison;
        }

        coreComparison = CompareNumericIdentifier(Patch, other.Patch);
        if (coreComparison != 0)
        {
            return coreComparison;
        }

        if (Prerelease.Length == 0)
        {
            return other.Prerelease.Length == 0 ? 0 : 1;
        }

        if (other.Prerelease.Length == 0)
        {
            return -1;
        }

        for (var index = 0; index < Math.Min(Prerelease.Length, other.Prerelease.Length); index++)
        {
            var left = Prerelease[index];
            var right = other.Prerelease[index];
            var leftNumeric = left.All(static character => character is >= '0' and <= '9');
            var rightNumeric = right.All(static character => character is >= '0' and <= '9');
            int comparison;
            if (leftNumeric && rightNumeric)
            {
                comparison = CompareNumericIdentifier(left, right);
            }
            else if (leftNumeric)
            {
                comparison = -1;
            }
            else if (rightNumeric)
            {
                comparison = 1;
            }
            else
            {
                comparison = string.CompareOrdinal(left, right);
            }

            if (comparison != 0)
            {
                return comparison;
            }
        }

        return Prerelease.Length.CompareTo(other.Prerelease.Length);
    }

    private static int CompareNumericIdentifier(string left, string right)
    {
        var lengthComparison = left.Length.CompareTo(right.Length);
        return lengthComparison != 0
            ? lengthComparison
            : string.CompareOrdinal(left, right);
    }
}

internal static class SemanticVersionParser
{
    public static bool TryParse(
        [NotNullWhen(true)] string? value,
        out ParsedSemanticVersion version)
    {
        version = default;
        if (string.IsNullOrEmpty(value) || value.Any(char.IsWhiteSpace))
        {
            return false;
        }

        var plusIndex = value.IndexOf('+');
        var versionWithoutBuild = plusIndex >= 0 ? value[..plusIndex] : value;
        var build = plusIndex >= 0 ? value[(plusIndex + 1)..] : null;
        if (plusIndex >= 0 &&
            (string.IsNullOrEmpty(build) ||
             value.IndexOf('+', plusIndex + 1) >= 0 ||
             !IdentifiersAreValid(build, allowLeadingZero: true)))
        {
            return false;
        }

        var dashIndex = versionWithoutBuild.IndexOf('-');
        var core = dashIndex >= 0 ? versionWithoutBuild[..dashIndex] : versionWithoutBuild;
        var prereleaseText = dashIndex >= 0 ? versionWithoutBuild[(dashIndex + 1)..] : null;
        if (dashIndex >= 0 &&
            (string.IsNullOrEmpty(prereleaseText) ||
             !IdentifiersAreValid(prereleaseText, allowLeadingZero: false)))
        {
            return false;
        }

        var coreParts = core.Split('.');
        if (coreParts.Length != 3 ||
            !TryParseCoreNumber(coreParts[0], out var major) ||
            !TryParseCoreNumber(coreParts[1], out var minor) ||
            !TryParseCoreNumber(coreParts[2], out var patch))
        {
            return false;
        }

        version = new ParsedSemanticVersion(
            major,
            minor,
            patch,
            prereleaseText?.Split('.') ?? []);
        return true;
    }

    private static bool TryParseCoreNumber(string text, out string value)
    {
        value = text;
        return text.Length > 0 &&
               (text.Length == 1 || text[0] != '0') &&
               text.All(static character => character is >= '0' and <= '9');
    }

    private static bool IdentifiersAreValid(string value, bool allowLeadingZero)
    {
        foreach (var identifier in value.Split('.'))
        {
            if (identifier.Length == 0 ||
                identifier.Any(static character =>
                    character is not (>= '0' and <= '9') and
                    not (>= 'A' and <= 'Z') and
                    not (>= 'a' and <= 'z') and
                    not '-'))
            {
                return false;
            }

            var numeric = identifier.All(static character => character is >= '0' and <= '9');
            if (!allowLeadingZero && numeric && identifier.Length > 1 && identifier[0] == '0')
            {
                return false;
            }
        }

        return true;
    }
}
