namespace Product.Core;

/// <summary>Application-owned resource semantics independent of transport and storage.</summary>
public interface IOwnedResources
{
    /// <summary>Creates an immutable owned resource, returning a conflict for a used identity.</summary>
    Task<CreateResourceOutcome> CreateAsync(Guid id, ResourceOwner owner, CancellationToken cancellationToken);
    /// <summary>Reads only the resource belonging to the admitted public issuer and subject.</summary>
    Task<Guid?> ReadAsync(Guid id, ResourceOwner owner, CancellationToken cancellationToken);
}
