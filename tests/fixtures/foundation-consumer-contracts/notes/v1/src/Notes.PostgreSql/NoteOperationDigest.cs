using System.Globalization;
using Notes.Core;
using Orbyss.Foundation.Json;

namespace Notes.PostgreSql;

internal static class NoteOperationDigest
{
    // This fixture owns its version/order. The reusable writer owns only bounded bytes/hash mechanics.
    internal static string Create(string operation, Guid noteId, long expectedRevision, NoteName name)
    {
        using var writer = new CanonicalUtf8Writer(4096);
        writer.Raw("{\"version\":"); writer.String(NoteProtocol.OperationIdentityVersion);
        writer.Raw(",\"operation\":"); writer.String(operation);
        writer.Raw(",\"noteId\":"); writer.String(noteId.ToString("D"));
        writer.Raw(",\"expectedRevision\":"); writer.Raw(expectedRevision.ToString(CultureInfo.InvariantCulture));
        writer.Raw(",\"name\":"); writer.String(name.Value);
        writer.Raw("}");
        return writer.CompleteSha256();
    }
}
