namespace Orbyss.ProgramKit.Tasks.Core.Schedules;

/// <summary>
/// Versioned trigger intent with an exact typed descriptor and occurrence
/// calculator profile.
/// </summary>
public sealed record TaskScheduleDefinition(
    ArtifactReference Revision,
    ArtifactReference DefinitionRevision,
    ArtifactReference ActivationBindingRevision,
    ArtifactReference DescriptorRevision,
    ArtifactReference DescriptorSchema,
    ArtifactReference OccurrenceCalculatorProfile);
