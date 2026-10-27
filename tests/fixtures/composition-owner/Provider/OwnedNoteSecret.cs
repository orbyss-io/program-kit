using System.Security.Cryptography;
using System.Text;

namespace Application.PostgreSql;

/// <summary>Admits an externally supplied per-shell key and erases it when DI disposes the generation.</summary>
internal sealed class OwnedNoteSecret : IDisposable
{
    /// <summary>Retains the private key only in the runtime process.</summary>
    private readonly byte[] key;
    /// <summary>Rejects a missing or invalid key without exposing the supplied value.</summary>
    public OwnedNoteSecret(string configured)
    {
        try { key = Convert.FromBase64String(configured); }
        catch (FormatException) { throw new InvalidOperationException("OWNER_SECRET_REQUIRED"); }
        if (key.Length != 32)
        {
            CryptographicOperations.ZeroMemory(key);
            throw new InvalidOperationException("OWNER_SECRET_REQUIRED");
        }
    }
    /// <summary>Binds a persisted note to its actual owner and independent identity.</summary>
    public byte[] Sign(
        string issuer,
        string subject,
        Guid id,
        string value
    )
    {
        var message = issuer + "\n" + subject + "\n" + id.ToString("D") + "\n" + value;
        var payload = Encoding.UTF8.GetBytes(message);
        return HMACSHA256.HashData(key, payload);
    }
    /// <inheritdoc />
    public void Dispose() => CryptographicOperations.ZeroMemory(key);
}
