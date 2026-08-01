using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Cli.Parsing;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionCliContractTests
{
    [TestMethod]
    [DataRow("explain", PublicCommand.SessionExplain)]
    [DataRow("install", PublicCommand.SessionInstall)]
    [DataRow("verify", PublicCommand.SessionVerify)]
    [DataRow("remove", PublicCommand.SessionRemove)]
    public void Session_grammar_is_nested_exact_and_json_capable(string verb, PublicCommand expected)
    {
        CliParseResult parsed = new CliParser().Parse(new[] { "session", verb, "--workspace", "repo", "--request", "repo/request.json", "--format", "json" });
        Assert.IsTrue(parsed.Succeeded, parsed.Error);
        Assert.AreEqual(expected, parsed.Invocation!.Command);
        Assert.AreEqual(OutputFormat.Json, parsed.Invocation.Format);
    }

    [TestMethod]
    public void Session_grammar_rejects_missing_unknown_or_extra_nesting()
    {
        CliParser parser = new();
        Assert.IsFalse(parser.Parse(new[] { "session" }).Succeeded);
        Assert.IsFalse(parser.Parse(new[] { "session", "Install", "--workspace", "x", "--request", "y" }).Succeeded);
        Assert.IsFalse(parser.Parse(new[] { "session", "install", "extra", "--workspace", "x", "--request", "y" }).Succeeded);
        Assert.IsFalse(parser.Parse(new[] { "session", "install", "--provider", "codex", "--workspace", "x", "--request", "y" }).Succeeded);
    }
}
