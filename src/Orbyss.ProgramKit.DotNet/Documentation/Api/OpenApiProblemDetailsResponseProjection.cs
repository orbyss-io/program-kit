namespace Orbyss.ProgramKit.DotNet.Documentation.Api;

/// <summary>One explicitly declared Problem Details response for an owned operation.</summary>
public sealed record OpenApiProblemDetailsResponseProjection(
    int StatusCode,
    ProgramKitIdentifier FailureIdentity,
    Uri Type,
    string Title,
    ArtifactReference ProblemSchemaRevision);
