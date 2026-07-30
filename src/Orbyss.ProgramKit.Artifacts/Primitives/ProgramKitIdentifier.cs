using System.Diagnostics.CodeAnalysis;

namespace Orbyss.ProgramKit.Artifacts.Primitives;

/// <summary>A stable Program Kit semantic identifier.</summary>
public readonly record struct ProgramKitIdentifier
{
    /// <summary>The exact canonical Program Kit identifier regular expression.</summary>
    public const string CanonicalPattern =
        "^pkid:[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*(?:\\.[a-z0-9]+(?:-[a-z0-9]+)*)*$";

    /// <summary>The exact human-readable Program Kit identifier grammar.</summary>
    public const string Grammar =
        "pkid:<kind>:<scope>:<name>, where kind and scope are lowercase ASCII kebab tokens and name is one or more lowercase ASCII kebab tokens separated by single dots";

    /// <summary>Initializes a validated Program Kit identifier.</summary>
    /// <exception cref="ArgumentException">The value does not match the PKID grammar.</exception>
    public ProgramKitIdentifier(string value)
    {
        if (!IsValid(value))
        {
            throw new ArgumentException(
                string.Concat(
                    "A Program Kit identifier must match ",
                    Grammar,
                    ". Exact pattern: ",
                    CanonicalPattern),
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
                    string.Concat(
                        "The value must match ",
                        Grammar,
                        ". Exact pattern: ",
                        CanonicalPattern),
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
               IsDottedName(segments[3]);
    }

    private static bool IsDottedName(string value) =>
        value.Split('.').All(IsKebabToken);

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
