using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Invocation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeInvocationBindingTests
{
    [TestMethod]
    public void Factory_binding_preserves_executable_workspace_request_and_argument_boundaries()
    {
        ClaudeCliInvocation binding = ClaudeInvocationBinding.Factory(
            ".program-kit/tools/program-kit.exe", "construct", "C:/consumer workspace", "requests/construct request.json");
        Assert.AreEqual(".program-kit/tools/program-kit.exe", binding.Executable);
        CollectionAssert.AreEqual(new[] { "construct", "--workspace", "C:/consumer workspace", "--request", "requests/construct request.json", "--format", "json" }, binding.Arguments.ToArray());
        Assert.AreEqual("C:/consumer workspace", binding.WorkingDirectory);
        Assert.IsFalse(binding.Arguments.Any(static value => value.Contains("&&", System.StringComparison.Ordinal)));
    }

    [TestMethod]
    public void Lifecycle_binding_inserts_only_the_session_nesting_token()
    {
        ClaudeCliInvocation binding = ClaudeInvocationBinding.Session(
            ".program-kit/tools/program-kit", "verify", "/tmp/consumer workspace", "requests/verify.json");
        CollectionAssert.AreEqual(new[] { "session", "verify", "--workspace", "/tmp/consumer workspace", "--request", "requests/verify.json", "--format", "json" }, binding.Arguments.ToArray());
    }
}
