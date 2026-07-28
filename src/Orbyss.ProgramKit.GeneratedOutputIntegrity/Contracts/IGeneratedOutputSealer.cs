namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Creates deterministic integrity artifacts over generated payload bytes.</summary>
public interface IGeneratedOutputSealer
{
    /// <summary>Seals one complete generated payload set.</summary>
    GeneratedOutputSeal Seal(
        IEnumerable<GeneratedOutputPayload> payloads);

    /// <summary>Creates deterministic sibling-anchor bytes for exact manifest bytes.</summary>
    ReadOnlyMemory<byte> CreateAnchorBytes(
        ReadOnlyMemory<byte> manifestBytes);
}
