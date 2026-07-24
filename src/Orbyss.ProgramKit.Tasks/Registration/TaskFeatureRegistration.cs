using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Declares one exact feature revision available to task bindings.</summary>
public sealed record TaskFeatureRegistration(ArtifactReference FeatureRevision);
