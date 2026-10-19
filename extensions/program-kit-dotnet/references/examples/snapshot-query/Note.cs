namespace SnapshotLesson;

/// <summary>Represents an immutable row supplied by the accepted snapshot owner.</summary>
/// <param name="Id">Opaque row identity; duplicate rows remain distinct entries.</param>
/// <param name="Owner">Exact ordinal owner identity.</param>
public sealed record Note(string Id, string Owner);
