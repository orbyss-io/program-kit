using System.Diagnostics.CodeAnalysis;

namespace Orbyss.ProgramKit.Artifacts.Primitives;

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
