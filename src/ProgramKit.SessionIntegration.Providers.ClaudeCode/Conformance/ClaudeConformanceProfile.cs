using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Schemas;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

public sealed record ClaudeConformanceProfile(
    GovernedIdentity Provider,
    GovernedIdentity Adapter,
    GovernedIdentity Definition,
    GovernedIdentity DiagnosticCatalog,
    GovernedIdentity NeutralProfile,
    string ReviewSchema,
    IReadOnlyList<string> RequiredOperations,
    string LiveEvidenceStatus);

public static class ClaudeConformanceProfiles
{
    public static ClaudeConformanceProfile ProjectSkillV1(SessionProviderManifest manifest) => new(
        manifest.ProviderIdentity,
        manifest.AdapterIdentity,
        manifest.DefinitionBinding,
        manifest.DiagnosticCatalog,
        manifest.ConformanceProfile,
        ClaudeSchemaResources.MachineReviewId,
        manifest.RequiredCliOperations,
        "not-evaluated");

    public static SessionProviderConformanceReport Compare(IEnumerable<SessionSemanticObservation> observations) =>
        new SessionProviderConformanceEvaluator().CompareSemanticObservations(observations);
}
