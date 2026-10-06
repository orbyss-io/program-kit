using Microsoft.AspNetCore.Http;
using Notes.Core;
using Orbyss.Foundation.Authentication;

namespace Notes.Api;

internal sealed class NoteOwnerAdapter(IValidatedAccountIdentityReader identities)
{
    internal NoteOwner Read(HttpContext http)
    {
        if (!identities.TryRead(http.User, out var identity))
            throw new InvalidOperationException("The selected authentication profile did not admit an account projection.");
        return new(identity.Issuer, identity.Subject);
    }
}
