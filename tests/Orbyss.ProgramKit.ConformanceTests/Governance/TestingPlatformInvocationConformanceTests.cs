namespace Orbyss.ProgramKit.ConformanceTests.Governance;

[TestClass]
public sealed class TestingPlatformInvocationConformanceTests
{
    [TestMethod]
    public void ActiveTestCommandsUseExplicitMicrosoftTestingPlatformSelectors()
    {
        string globalJson = Read("global.json");
        string workflow = Read(".github", "workflows", "publish-nuget.yml");
        string contributing = Read("CONTRIBUTING.md");
        string readme = Read("README.md");
        string gateTestPlan = Read("build", "Invoke-CSharpGateTestPlan.ps1");

        Assert.Contains("\"runner\": \"Microsoft.Testing.Platform\"", globalJson);

        foreach (string solutionCommandSource in new[]
                 {
                     workflow,
                     contributing,
                     readme,
                 })
        {
            Assert.Contains(
                "dotnet test --solution ProgramKit.sln",
                solutionCommandSource);
            Assert.DoesNotContain(
                "dotnet test ProgramKit.sln",
                solutionCommandSource);
            Assert.DoesNotContain(
                "dotnet test --solution ProgramKit.sln --maxcpucount",
                solutionCommandSource);
        }

        foreach (string contributorGuidance in new[] { contributing, readme })
        {
            Assert.Contains(
                "Do not pass the legacy `--maxcpucount` switch",
                contributorGuidance);
        }

        Assert.AreEqual(2, Count(gateTestPlan, "'--project'"));
        Assert.AreEqual(
            2,
            Count(gateTestPlan, "'--minimum-expected-tests'"));
        Assert.DoesNotContain("'--maxcpucount", gateTestPlan);
        Assert.DoesNotContain(
            "'test',\r\n        $conformanceProject",
            gateTestPlan);
        Assert.DoesNotContain(
            "'test',\n        $conformanceProject",
            gateTestPlan);
    }

    private static int Count(string source, string value)
    {
        int count = 0;
        int offset = 0;
        while ((offset = source.IndexOf(value, offset, StringComparison.Ordinal)) >= 0)
        {
            count++;
            offset += value.Length;
        }

        return count;
    }

    private static string Read(params string[] segments) =>
        File.ReadAllText(Path.Combine(
            [ConformanceInputs.ProgramKitRoot, .. segments]));
}
