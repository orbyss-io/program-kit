namespace Orbyss.ProgramKit.Artifacts.Validation;

internal static class ArtifactValidationText
{
    public static bool IsKebabCase(string? value)
    {
        if (string.IsNullOrEmpty(value) || value[0] == '-' || value[^1] == '-')
        {
            return false;
        }

        var previousHyphen = false;
        foreach (var character in value)
        {
            var hyphen = character == '-';
            if (character is not (>= 'a' and <= 'z') and not (>= '0' and <= '9') && !hyphen)
            {
                return false;
            }

            if (hyphen && previousHyphen)
            {
                return false;
            }

            previousHyphen = hyphen;
        }

        return true;
    }
}
