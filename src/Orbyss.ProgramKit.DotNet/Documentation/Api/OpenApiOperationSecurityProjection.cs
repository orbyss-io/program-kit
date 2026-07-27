namespace Orbyss.ProgramKit.DotNet.Documentation.Api;

/// <summary>Explicit anonymous or named-policy security projection for one operation.</summary>
public sealed record OpenApiOperationSecurityProjection(
    bool Anonymous,
    ProgramKitIdentifier? PolicyIdentity,
    ImmutableArray<string> SchemeNames);
