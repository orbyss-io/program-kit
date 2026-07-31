namespace Orbyss.ProgramKit.ConformanceTests.Governance;

[TestClass]
public sealed class ContributorIntegrationGuidanceConformanceTests
{
    [TestMethod]
    public void GuidanceRequiresFocusedLocalChecksAndOneSharedCombinedSource()
    {
        string agents = Read("AGENTS.md");
        string contributing = Read("CONTRIBUTING.md");
        string readme = Read("README.md");
        string integration = Read(
            ".github",
            "workflows",
            "program-kit-integration.yml");

        Assert.Contains("directly affected local checks", agents);
        Assert.Contains("affected tests", contributing);
        Assert.Contains("directly affected checks locally", readme);
        foreach (string guidance in new[] { agents, contributing, readme })
        {
            string normalized = NormalizeWhitespace(guidance);
            Assert.Contains("Program Kit integration", normalized);
            Assert.Contains("combined", normalized);
            Assert.Contains("source", normalized);
            Assert.Contains("repeatedly", normalized);
            Assert.Contains("`main`", normalized);
        }

        Assert.Contains("pull_request:", integration);
        Assert.Contains("merge_group:", integration);
        Assert.Contains("name: Program Kit integration", integration);
        Assert.DoesNotContain("github.event.pull_request.head.sha", integration);
    }

    [TestMethod]
    public void GuidancePreservesConflictResolutionAndHumanAuthority()
    {
        string agents = Read("AGENTS.md");
        string contributing = Read("CONTRIBUTING.md");
        string readme = Read("README.md");

        Assert.Contains("real source conflict", agents);
        Assert.Contains("real Git conflict", contributing);
        Assert.Contains("Real source conflicts", readme);
        Assert.Contains("CI success only as execution evidence", agents);
        Assert.Contains(
            "CI success is execution evidence, not semantic approval",
            contributing);
        Assert.Contains("CI evidence does not approve", readme);
        Assert.Contains("Do not enable automatic merge", contributing);
        Assert.Contains("does not publish it", readme);
    }

    [TestMethod]
    public void ContributorStartupIsProviderNeutralAndFreshTaskBounded()
    {
        string agents = Read("AGENTS.md");
        string contributing = Read("CONTRIBUTING.md");

        Assert.Contains("freshly initialized task", agents);
        Assert.Contains("explicitly requests it", agents);
        Assert.Contains(
            "Never refresh source-contributor skills after a capability has been loaded",
            agents);
        Assert.Contains("beginning of a fresh task", contributing);
        Assert.Contains("not run it after a capability has been loaded", contributing);
        Assert.Contains("human explicitly asks", contributing);

        foreach (string providerBrand in new[]
                 {
                     "Codex",
                     "Claude",
                     "Gemini",
                     "OpenAI",
                     "Anthropic",
                 })
        {
            Assert.DoesNotContain(providerBrand, agents);
            Assert.DoesNotContain(providerBrand, contributing);
        }
    }

    [TestMethod]
    public void AdministrationHandoffNamesExactUnappliedExternalSettings()
    {
        string handoff = Read(
            ".github",
            "PROGRAM-KIT-ADMINISTRATION.md");
        string integration = Read(
            ".github",
            "workflows",
            "program-kit-integration.yml");
        string publication = Read(
            ".github",
            "workflows",
            "publish-nuget.yml");

        Assert.Contains("None of these external settings is applied or confirmed", handoff);
        Assert.Contains("- [ ]", handoff);
        Assert.Contains("ruleset targeting `main`", handoff);
        Assert.Contains("status check named exactly `Program Kit integration`", handoff);
        Assert.Contains("Enable merge queue", handoff);
        Assert.Contains("Do not require a topic branch to be updated", handoff);
        Assert.Contains("environment named exactly `program-kit-publication`", handoff);
        Assert.Contains("reviewer identities", handoff);
        Assert.Contains("Prevent self-review", handoff);
        Assert.Contains("`NUGET_USER` as an environment secret", handoff);
        Assert.Contains("repository owner: `orbyss-io`", handoff);
        Assert.Contains("repository: `program-kit`", handoff);
        Assert.Contains("workflow filename: `publish-nuget.yml`", handoff);
        Assert.Contains("environment: `program-kit-publication`", handoff);
        Assert.Contains("30 days or longer", handoff);
        Assert.Contains("Do not enable automatic publication", handoff);

        Assert.Contains("name: Program Kit integration", integration);
        Assert.Contains("retention-days: 30", integration);
        Assert.Contains("canonical_run_id:", publication);
        Assert.Contains("environment: program-kit-publication", publication);
        Assert.Contains("secrets.NUGET_USER", publication);
    }

    private static string Read(params string[] segments) =>
        File.ReadAllText(Path.Combine(
            [ConformanceInputs.ProgramKitRoot, .. segments]));

    private static string NormalizeWhitespace(string source) =>
        System.Text.RegularExpressions.Regex.Replace(source, @"\s+", " ");
}
