using System;
using System.IO;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Cli.Parsing;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class AdapterCliContractTests
{
    [TestMethod]
    [DataRow("init", null, PublicCommand.Init)]
    [DataRow("catalog", "list", PublicCommand.CatalogList)]
    [DataRow("restore", null, PublicCommand.Restore)]
    [DataRow("prepare", null, PublicCommand.Prepare)]
    [DataRow("authority", "record", PublicCommand.AuthorityRecord)]
    public void New_command_grammar_is_nested_exact_and_reaches_the_single_command_identity(string command, string? subcommand, PublicCommand expected)
    {
        string[] prefix = subcommand is null ? new[] { command } : new[] { command, subcommand };
        string[] arguments = new string[prefix.Length + 6];
        prefix.CopyTo(arguments, 0);
        new[] { "--workspace", "repo", "--request", "repo/request.json", "--format", "json" }.CopyTo(arguments, prefix.Length);
        CliParseResult parsed = new CliParser().Parse(arguments);
        Assert.IsTrue(parsed.Succeeded, parsed.Error);
        Assert.AreEqual(expected, parsed.Invocation!.Command);
        Assert.AreEqual(OutputFormat.Json, parsed.Invocation.Format);
    }

    [TestMethod]
    public void New_command_grammar_rejects_duplicates_missing_values_positionals_and_opaque_tokens_without_echo()
    {
        const string fingerprint = "opaque-36c62b7d-35e7-4f63-a006-secret";
        CliParser parser = new();
        Assert.IsFalse(parser.Parse(new[] { "init", "--workspace", "x", "--workspace", "y", "--request", "r" }).Succeeded);
        Assert.IsFalse(parser.Parse(new[] { "catalog" }).Succeeded);
        Assert.IsFalse(parser.Parse(new[] { "authority", "Record", "--workspace", "x", "--request", "r" }).Succeeded);
        Assert.IsFalse(parser.Parse(new[] { "prepare", "extra", "--workspace", "x", "--request", "r" }).Succeeded);
        CliParseResult unknown = parser.Parse(new[] { "init", $"--{fingerprint}", "x", "--workspace", "w", "--request", "r" });
        Assert.IsFalse(unknown.Succeeded);
        Assert.IsFalse(unknown.Error!.Contains(fingerprint, StringComparison.Ordinal));
    }

    [TestMethod]
    public void New_public_command_emits_one_schema_valid_current_result_and_clean_stderr()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            string request = Path.Combine(workspace, "request.json");
            File.WriteAllText(request, "{}");
            var execution = TestRepository.RunCli("init", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(3, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            Assert.AreEqual(string.Empty, execution.StandardError);
            var result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            Assert.AreEqual("init", result["command"]!.GetValue<string>());
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }
}
