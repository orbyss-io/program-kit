namespace Orbyss.ProgramKit.CommandLine.Contracts.Capabilities;

/// <summary>
/// One finite reviewed AI-provider project-skill discovery contract.
/// </summary>
public sealed record CapabilityProviderContract(
    string ProviderId,
    string ProjectSkillRoot,
    string? LegacyProjectSkillRoot);
