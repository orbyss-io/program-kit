namespace Orbyss.ProgramKit.DotNet.Operations.TransportFailures;

/// <summary>Binds one explicit .NET exception type to consumer-owned transport meaning.</summary>
public sealed record DotNetExceptionFailureMapping(
    [property: JsonPropertyName("order")] int Order,
    [property: JsonPropertyName("exceptionType")] string ExceptionType,
    [property: JsonPropertyName("failureIdentity")] ProgramKitIdentifier FailureIdentity);
