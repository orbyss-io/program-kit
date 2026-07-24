using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Policies;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>One exact bounded scheduler misfire-policy registration.</summary>
public sealed record TaskMisfirePolicyRegistration(
    ArtifactReference Revision,
    TaskMisfirePolicyKind Kind,
    int MaximumCatchUp);
