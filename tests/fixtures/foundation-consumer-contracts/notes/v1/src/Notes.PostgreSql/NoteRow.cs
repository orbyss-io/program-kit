namespace Notes.PostgreSql;

internal sealed class NoteRow
{
    public string Issuer { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public Guid Id { get; set; }
    public long Revision { get; set; }
    public string Name { get; set; } = string.Empty;
}
