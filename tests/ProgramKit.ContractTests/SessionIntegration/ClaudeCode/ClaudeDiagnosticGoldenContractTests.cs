using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Diagnostics;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeDiagnosticGoldenContractTests
{
    [TestMethod]
    public void Every_provider_trigger_maps_to_one_exact_catalog_entry_and_safe_action()
    {
        for (int number = 1; number <= 8; number++)
        {
            ClaudeDiagnosticObservation observation = ClaudeDiagnosticFactory.Create(number, "provider-observation", "safe-normalized-value", "none");
            Assert.AreEqual(ClaudeDiagnosticCatalog.Id(number), observation.Definition.Id);
            Assert.AreEqual("provider-observation", observation.Subject);
            Assert.AreEqual("none", observation.EffectState);
            Assert.IsFalse(observation.SafeObserved.Keys.Any(static key => key.Contains("path", System.StringComparison.OrdinalIgnoreCase)));
        }
    }
}
