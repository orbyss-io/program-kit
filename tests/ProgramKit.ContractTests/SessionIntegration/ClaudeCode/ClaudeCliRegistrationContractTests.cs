using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Cli.Commands;
using Orbyss.ProgramKit.Cli.Composition;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeCliRegistrationContractTests
{
    [TestMethod]
    public void Cli_catalogs_Claude_explicitly_without_new_lifecycle_grammar()
    {
        SessionProviderManifest claude = ProgramKitComposition.CreateSessionServices().Providers.Catalog()
            .Single(item => item.ProviderIdentity.Name == "claude-code");
        Assert.AreEqual(SessionProviderSupport.NotEvaluated, claude.SupportClaim);
        OperationResult help = HelpCommand.Help();
        Assert.AreEqual("program-kit session <explain|install|verify|remove> --workspace <path> --request <path> [--format text|json]", help.Utility!["sessionGrammar"]!.GetValue<string>());
        string[] adapters = help.Utility["installedSessionAdapters"]!.AsArray().Select(static item => item!.GetValue<string>()).ToArray();
        CollectionAssert.Contains(adapters, claude.ProviderIdentity.StableKey);
    }
}
