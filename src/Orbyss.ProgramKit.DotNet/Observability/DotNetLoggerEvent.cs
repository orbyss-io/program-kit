namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>One stable source-generated structured log event.</summary>
public sealed record DotNetLoggerEvent(
    [property: JsonPropertyName("category")] string Category,
    [property: JsonPropertyName("eventId")] int EventId,
    [property: JsonPropertyName("eventName")] string EventName,
    [property: JsonPropertyName("level")] DotNetLogLevel Level,
    [property: JsonPropertyName("messageTemplate")] string MessageTemplate,
    [property: JsonPropertyName("scopeFields")] ImmutableArray<string> ScopeFields);
