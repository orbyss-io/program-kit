using System.Text.Json.Serialization;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Tasks;

namespace ObservatoryScheduling.Core.Configuration;

/// <summary>Source-generated JSON metadata selected explicitly by fixture hosts.</summary>
[JsonSourceGenerationOptions(
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    GenerationMode = JsonSourceGenerationMode.Metadata,
    WriteIndented = false)]
[JsonSerializable(typeof(ViewingRequest))]
[JsonSerializable(typeof(ViewingSession))]
[JsonSerializable(typeof(ScheduleViewingTaskRequest))]
[JsonSerializable(typeof(ScheduleViewingTaskResponse))]
public sealed partial class ObservatoryJsonContext : JsonSerializerContext;
