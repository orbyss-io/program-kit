namespace Notes.Core;

/// <summary>Prevents contradictory success/failure states at replacement capability boundaries.</summary>
public sealed class NoteOutcome<T> where T : class
{
    private NoteOutcome(T? value, NoteFailure? failure) { Value = value; Failure = failure; }
    public T? Value { get; }
    public NoteFailure? Failure { get; }
    public static NoteOutcome<T> Success(T value) => new(value ?? throw new ArgumentNullException(nameof(value)), null);
    public static NoteOutcome<T> Denied(NoteFailure failure) => new(null, failure);
}
