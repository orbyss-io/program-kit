namespace Application.Core;

/// <summary>Owns creation and private reading of one synthetic owner's notes.</summary>
public interface IOwnedNotes
{
    /// <summary>Commits one synthetic note for the authenticated actor.</summary>
    Task<Guid> CreateAsync(OwnedActor actor, CancellationToken cancellationToken);
    /// <summary>Returns a live note only for the exact authenticated owner.</summary>
    Task<string?> ReadAsync(
        OwnedActor actor,
        Guid id,
        CancellationToken cancellationToken
    );
}
