using System.Collections.Generic;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeInstallationRepeatabilityAcceptanceTests
{
    [TestMethod]
    public void Ten_fresh_adapter_evaluations_are_byte_identical_and_fail_closed()
    {
        List<string> projectionDigests = new();
        List<string> manifestDigests = new();
        for (int trial = 1; trial <= 10; trial++)
        {
            ClaudeSessionProviderAdapter adapter = new();
            projectionDigests.Add(Digests.Sha256(adapter.Project(ClaudeTestContext.Create(adapter.Manifest)).Single().Content));
            manifestDigests.Add(adapter.Manifest.ProviderIdentity.Digest);
            SessionDiagnosticException exception = Assert.ThrowsExactly<SessionDiagnosticException>(
                () => new SessionProviderRegistry(new[] { adapter }).Resolve(adapter.Manifest.ProviderIdentity),
                $"trial {trial}");
            Assert.AreEqual("program-kit.session/PKSES0003", exception.DiagnosticId, $"trial {trial}");
        }

        Assert.AreEqual(1, projectionDigests.Distinct().Count());
        Assert.AreEqual(1, manifestDigests.Distinct().Count());
        Assert.AreEqual("sha256:37b044db0db48140ec9946d7dff085e75e0f7a121a9abe90e058288da794260a", projectionDigests.Distinct().Single());
    }
}
