namespace Notes.Core;

/// <summary>Owns exact application account identity without authentication/provider adaptation.</summary>
public sealed record NoteOwner
{
    public NoteOwner(string issuer, string subject)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(issuer);
        ArgumentException.ThrowIfNullOrWhiteSpace(subject);
        Issuer = issuer; Subject = subject;
    }
    public string Issuer { get; }
    public string Subject { get; }
}
