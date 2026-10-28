namespace Application.PostgreSql;

/// <summary>Private provider state; identities are never taken from the HTTP request body.</summary>
internal sealed class OwnedNoteRow
{
    /// <summary>Gets or sets the independent note identity.</summary>
    public Guid Id { get; set; }
    /// <summary>Gets or sets the exact authenticated issuer.</summary>
    public string OwnerIssuer { get; set; } = "";
    /// <summary>Gets or sets the exact authenticated subject.</summary>
    public string OwnerSubject { get; set; } = "";
    /// <summary>Gets or sets the synthetic product value.</summary>
    public string Value { get; set; } = "";
    /// <summary>Gets or sets the secret-bound integrity tag, never the key.</summary>
    public byte[] Digest { get; set; } = [];
}
