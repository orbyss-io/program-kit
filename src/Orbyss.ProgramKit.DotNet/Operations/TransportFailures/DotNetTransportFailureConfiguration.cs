using Orbyss.ProgramKit.Operations.Contracts.Transport;

namespace Orbyss.ProgramKit.DotNet.Operations.TransportFailures;

/// <summary>Exact ASP.NET Core transport-failure generation intent.</summary>
public sealed record DotNetTransportFailureConfiguration(
    [property: JsonPropertyName("profile")] TransportFailureProfile Profile,
    [property: JsonPropertyName("exceptionMappings")] ImmutableArray<DotNetExceptionFailureMapping> ExceptionMappings,
    [property: JsonPropertyName("statusCodePages")] bool StatusCodePages,
    [property: JsonPropertyName("handledExceptionDiagnostics")] DotNetHandledExceptionDiagnostics HandledExceptionDiagnostics,
    [property: JsonPropertyName("responseStartedDisposition")] DotNetResponseStartedDisposition ResponseStartedDisposition,
    [property: JsonPropertyName("clientDisconnectDisposition")] DotNetClientDisconnectDisposition ClientDisconnectDisposition);
