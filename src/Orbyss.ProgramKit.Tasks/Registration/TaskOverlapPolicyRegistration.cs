using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Policies;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>One exact scheduler overlap-policy registration.</summary>
public sealed record TaskOverlapPolicyRegistration(
    ArtifactReference Revision,
    TaskOverlapPolicyKind Kind);
