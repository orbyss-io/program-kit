using Application.Core;
using Microsoft.AspNetCore.Http;
using Orbyss.Foundation.Authentication;

namespace Application.Api;

/// <summary>Maps the native validated identity to the owned capability, never to request-supplied owner fields.</summary>
internal sealed class OwnedNotesEndpoints(IValidatedAccountIdentityReader identities, IOwnedNotes notes)
{
    /// <summary>Creates through the authenticated actor after native permission/CSRF admission.</summary>
    public async Task<IResult> CreateAsync(HttpContext context)
    {
        if (!identities.TryRead(context.User, out var identity)) return Results.Unauthorized();
        var actor = new OwnedActor(identity!.Issuer, identity.Subject);
        var id = await notes.CreateAsync(actor, context.RequestAborted);
        var response = new { id };
        return Results.Json(response, statusCode: 201);
    }
    /// <summary>Hides foreign and absent notes behind the same missing result.</summary>
    public async Task<IResult> ReadAsync(HttpContext context, Guid id)
    {
        if (!identities.TryRead(context.User, out var identity)) return Results.Unauthorized();
        var actor = new OwnedActor(identity!.Issuer, identity.Subject);
        var value = await notes.ReadAsync(
            actor,
            id,
            context.RequestAborted
        );
        var response = new { id, value };
        return value is null ? Results.NotFound() : Results.Json(response);
    }
}
