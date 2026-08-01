using System.Globalization;
using System.Text;
using Orbyss.ProgramKit.SessionIntegration.Definitions;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Projection;

public static class CodexSkillProjector
{
    public static byte[] Project(SessionProjectionContext context)
    {
        string executable = context.Request.CliRelease.WorkspaceRelativeExecutable;
        StringBuilder skill = new();
        skill.Append("---\nname: program-kit\ndescription: Use Program Kit for human-led software construction, explanation, evaluation, and diagnostic recovery.\n---\n\n");
        skill.Append("# Program Kit software factory\n\n");
        skill.Append("This repository uses the independently installed Program Kit CLI through a provider-neutral, human-led workflow. The authoritative result is `program-kit.operation-result/v1` JSON; never infer success, authority, or remediation from prose.\n\n");
        skill.Append(CultureInfo.InvariantCulture, $"Exact workspace-local executable: `{executable}`. First invoke `version --format json` and require release `{context.Request.CliRelease.ReportedVersion}`. Pass shell arguments as an array, keep the workspace root explicit, and do not select a global command.\n\n");
        skill.Append("## Required workflow\n\n");
        foreach (string step in CanonicalSessionGuidance.WorkflowSteps) skill.Append("- ").Append(step).Append('\n');
        skill.Append("\nFor factory operations invoke `<executable> <operation> --workspace <workspace> --request <request> --format json`. For lifecycle operations insert `session` before the operation. Stop on unsupported, ambiguous, incompatible, indeterminate, or unsafe typed dispositions. Preserve custom implementation and every consumer-owned file.\n");
        skill.Append(CultureInfo.InvariantCulture, $"\nCanonical definition binding: `{context.Definition.Identity.StableKey}` with fingerprint `{context.Definition.Fingerprint}`.\n");
        return Encoding.UTF8.GetBytes(skill.ToString());
    }
}
