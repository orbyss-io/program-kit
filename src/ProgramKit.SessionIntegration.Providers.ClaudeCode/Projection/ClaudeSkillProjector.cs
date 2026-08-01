using System.Globalization;
using System.Text;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Manifest;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Projection;

public static class ClaudeSkillProjector
{
    private const string Description = "Use Program Kit to explain, construct, and evaluate contract-bounded software when the user asks to design or build software through Program Kit or needs help resolving Program Kit diagnostics.";

    public static byte[] Project(SessionProjectionContext context)
    {
        StringBuilder skill = new();
        skill.Append("---\nname: program-kit\ndescription: ").Append(Description).Append("\n---\n\n");
        skill.Append("# Program Kit software factory\n\n");
        skill.Append("Use the independently installed, workspace-local Program Kit CLI. Program Kit structured JSON is authoritative; never infer success, authority, remediation, or actual effects from provider prose.\n\n");
        skill.Append("Canonical guarantees: `authority=request-bound`; `disclosure=classified`; `normalization=canonical-json`; `fresh-session=separately-classified`.\n\n");
        skill.Append(CultureInfo.InvariantCulture, $"Resolve the exact executable from the admitted installation record: `{context.Request.CliRelease.WorkspaceRelativeExecutable}`. Verify `version --format json` reports `{context.Request.CliRelease.ReportedVersion}` before a factory operation. Never select a global executable from `PATH`.\n\n");
        skill.Append("## Required workflow\n\n");
        foreach (string step in CanonicalSessionGuidance.WorkflowSteps) skill.Append("- ").Append(step).Append('\n');
        skill.Append("\nInvoke factory operations as an executable plus argument array: `<executable> <operation> --workspace <workspace> --request <request> --format json`. For lifecycle operations insert `session` before the operation.\n\n");
        skill.Append("Ask the human only for bounded missing meaning or current authority identified by the result. Never create, approve, widen, refresh, or reuse a grant. Provider process permission and Program Kit effect authority are separate.\n\n");
        skill.Append("Use evaluation only for read-only assessment. Preserve drift and consumer-owned implementation. Treat repair as a separate proposed request requiring fresh validation and authority.\n\n");
        skill.Append("Stop on unsupported, ambiguous, incompatible, indeterminate, unsafe, unavailable, or disclosure-blocked results. Do not inspect Program Kit source, invent planning state, create provider configuration, persist provider output, or add authoring dependencies to generated runtimes.\n");
        skill.Append(CultureInfo.InvariantCulture, $"\nCanonical definition: `{context.Definition.Identity.StableKey}`; fingerprint: `{context.Definition.Fingerprint}`; provider surface: `anthropic:provider-surface:project-skill@{ClaudeProviderIdentities.ProviderVersion}`.\n");
        return Encoding.UTF8.GetBytes(skill.ToString());
    }
}
