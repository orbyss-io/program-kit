using System.Linq;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeWorkflowAcceptanceTests
{
    [TestMethod]
    public void Projected_workflow_contains_every_canonical_step_without_reordering()
    {
        ClaudeSessionProviderAdapter adapter = new();
        string text = Encoding.UTF8.GetString(adapter.Project(ClaudeTestContext.Create(adapter.Manifest)).Single().Content);
        int prior = -1;
        foreach (string step in CanonicalSessionGuidance.WorkflowSteps)
        {
            int current = text.IndexOf(step, System.StringComparison.Ordinal);
            Assert.IsGreaterThan(prior, current, step);
            prior = current;
        }
    }
}
