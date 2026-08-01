using System;
using System.Linq;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeGuidanceContractTests
{
    [TestMethod]
    public void Guidance_preserves_every_canonical_human_authority_boundary()
    {
        ClaudeSessionProviderAdapter adapter = new();
        string text = Encoding.UTF8.GetString(adapter.Project(ClaudeTestContext.Create(adapter.Manifest)).Single().Content);
        string[] required =
        {
            "explain before effects",
            "current exact grant",
            "never widen, refresh, or reuse a grant",
            "read-only assessment",
            "separate proposed request",
            "Provider process permission and Program Kit effect authority are separate",
            "structured JSON is authoritative",
            "Never select a global executable",
            "Stop on unsupported, ambiguous, incompatible, indeterminate, unsafe, unavailable",
        };
        foreach (string value in required) StringAssert.Contains(text, value, StringComparison.OrdinalIgnoreCase);
    }
}
