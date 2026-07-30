namespace Orbyss.ProgramKit.Serialization.Json.Serialization;

internal readonly record struct StrictJsonReadPathSegment(
    string? PropertyName,
    int ArrayIndex)
{
    internal static StrictJsonReadPathSegment Property(string name) =>
        new(name, -1);

    internal static StrictJsonReadPathSegment Index(int index) =>
        new(null, index);
}
