namespace Notes.Core;

/// <summary>Owns lifecycle identities and domain capacities independently of transport configuration.</summary>
public static class NoteProtocol
{
    public const string OperationIdentityVersion = "notes-operation-v1";
    public const string Create = "create-note";
    public const string Rename = "rename-note";
    public const int MaximumNameLength = 256;
}
