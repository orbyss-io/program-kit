namespace Orbyss.ProgramKit.DevContainers.Contracts.Features;

/// <summary>One exact-version feature plus expected immutable artifact digest.</summary>
public sealed record DevContainerFeature(
    string Reference,
    Sha256Digest ExpectedDigest,
    ImmutableSortedDictionary<string, string> Options);
