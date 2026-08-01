using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Diagnostics;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionDisclosureTests
{
    [TestMethod]
    [DataRow("password=hunter2")]
    [DataRow("Authorization: Bearer abc")]
    [DataRow("stack trace at C:\\private\\source.cs")]
    [DataRow("conversation id 123")]
    [DataRow("raw tool output: account workspace")]
    public void Protected_text_is_stably_withheld(string value) => Assert.AreEqual("withheld", DisclosureFilter.SafeText(value));

    [TestMethod]
    [DataRow("C:\\Users\\private\\file")]
    [DataRow("\\\\server\\private\\file")]
    [DataRow("/home/private/file")]
    public void Paths_controls_and_large_values_are_bounded(string absolutePath)
    {
        Assert.AreEqual("withheld", DisclosureFilter.SafeLogicalValue(absolutePath));
        Assert.IsFalse(DisclosureFilter.SafeText("safe\u0001value").Contains('\u0001'));
        string bounded = DisclosureFilter.SafeText(new string('a', 2000));
        Assert.IsTrue(bounded.Length <= 500);
        StringAssert.EndsWith(bounded, "[truncated]");
        Assert.AreEqual("withheld", DisclosureFilter.SafeToolOutput("anything"));
    }
}
