using Orbyss.ProgramKit.Contracts.Identity;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Manifest;

public static class ClaudeProviderIdentities
{
    public const string ProviderVersion = "2.1.220";
    public const string AdapterVersion = "1.0.0";
    public const string SkillLogicalPath = ".claude/skills/program-kit/SKILL.md";

    public static GovernedIdentity Provider(string digest) =>
        new("anthropic", "session-provider", "claude-code", ProviderVersion, digest);

    public static GovernedIdentity Adapter(string digest) =>
        new("orbyss.program-kit", "session-provider-adapter", "claude-code-project-skill", AdapterVersion, digest);
}
