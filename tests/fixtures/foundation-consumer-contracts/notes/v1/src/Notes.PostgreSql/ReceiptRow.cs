namespace Notes.PostgreSql;

internal sealed class ReceiptRow
{
    public string Issuer { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public Guid OperationId { get; set; }
    public string Digest { get; set; } = string.Empty;
    public Guid Id { get; set; }
    public long Revision { get; set; }
    public string Name { get; set; } = string.Empty;
}
