using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Definitions;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class InvocationTransportGuidanceContractTests
{
    [TestMethod]
    public void Pre_result_transport_failures_are_classified_without_fabricating_a_product_result()
    {
        CollectionAssert.AreEqual(new[] { "cli-unavailable", "shell-timeout", "nonzero-without-envelope", "malformed-json", "missing-result" }, InvocationTransportGuidance.Cases.Select(static item => item.Kind).ToArray());
        foreach (InvocationTransportCase item in InvocationTransportGuidance.Cases)
        {
            Assert.AreEqual("program-kit.session/PKSES0007", item.DiagnosticId);
            Assert.IsFalse(item.FabricateOperationResult);
            Assert.IsFalse(item.LaunchProvider);
        }
    }
}
