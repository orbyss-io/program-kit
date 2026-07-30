namespace Orbyss.ProgramKit.ConformanceTests.Governance;

[TestClass]
public sealed class BranchLifecyclePolicyConformanceTests
{
    [TestMethod]
    public void ContributorGuidanceRequiresSafeMergedBranchCleanup()
    {
        string agents = Read("AGENTS.md");
        string contributing = Read("CONTRIBUTING.md");

        Assert.Contains("Treat every non-default branch as short-lived", agents);
        Assert.Contains("After its tip is verified as", agents);
        Assert.Contains("reachable from `main`", agents);
        Assert.Contains("unmerged branch", agents);
        Assert.Contains("dirty branch", agents);
        Assert.Contains("active work", agents);

        Assert.Contains("`delete_branch_on_merge`", contributing);
        Assert.Contains(
            "git merge-base --is-ancestor <topic-branch> origin/main",
            contributing);
        Assert.Contains("git branch -d", contributing);
        Assert.Contains("Do not substitute `git branch -D`", contributing);
        Assert.Contains("report its unique commits", contributing);
    }

    [TestMethod]
    public void ConsumerGuidanceAndCompletionProfileCarryTheSameRule()
    {
        string readme = Read("README.md");
        string profile = Read(
            ".agent-capabilities",
            "supporting-resources",
            "completion-profiles",
            "software-change",
            "profiles",
            "commit-and-push-coherently.md");

        Assert.Contains("`delete_branch_on_merge`", readme);
        Assert.Contains("proven reachable", readme);
        Assert.Contains("clean, inactive local branch/worktree", readme);
        Assert.Contains("report the exact retained branch", readme);

        Assert.Contains("automatic merged-head-branch deletion", profile);
        Assert.Contains("prove the topic-branch tip is reachable", profile);
        Assert.Contains("clean, inactive local", profile);
        Assert.Contains("an unmerged", profile);
        Assert.Contains("a dirty branch", profile);
        Assert.Contains("report its unique commits", profile);
    }

    private static string Read(params string[] segments) =>
        File.ReadAllText(Path.Combine(
            [ConformanceInputs.ProgramKitRoot, .. segments]));
}
