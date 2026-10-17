using System.Text.Json.Serialization;

namespace ProgramKit.Examples.Ocr;

/// <summary>One consumed local dispatch capability; it is not a human approval record.</summary>
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record WorkerTicket(int SchemaVersion, string Kind, string Execution, string Attempt, string Nonce,
    string OriginalTicketPath, string Action, string Endpoint, string? FixturePath, string? FixtureSha256,
    int MaximumInputBytes, int MaximumResponseBytes, int TimeoutMilliseconds, long DeadlineUnixMilliseconds,
    string? ResultHandle, string? RecordingOutcome);
