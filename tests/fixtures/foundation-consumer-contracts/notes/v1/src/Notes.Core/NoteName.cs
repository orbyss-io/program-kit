namespace Notes.Core;

/// <summary>Preserves an admitted display name exactly; replay never normalizes different packets.</summary>
public sealed record NoteName
{
    private NoteName(string value) => Value = value;
    public string Value { get; }
    /// <summary>Requires an already valid value; invalid stored/programming input is an argument defect.</summary>
    public static NoteName Create(string value)
    {
        if (!TryCreate(value, out var admitted)) throw new ArgumentException("A note name must satisfy its value invariant.", nameof(value));
        return admitted!;
    }
    public static bool TryCreate(string value, out NoteName? admitted)
    {
        admitted = null;
        if (string.IsNullOrWhiteSpace(value) || value.Length > NoteProtocol.MaximumNameLength || value.Any(char.IsControl)) return false;
        for (var index = 0; index < value.Length; index++)
        {
            if (!char.IsSurrogate(value[index])) continue;
            if (!char.IsHighSurrogate(value[index]) || index + 1 == value.Length || !char.IsLowSurrogate(value[++index])) return false;
        }
        admitted = new(value); return true;
    }
}
