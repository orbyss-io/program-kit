using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace Orbyss.ProgramKit.ConformanceTests.Governance;

[TestClass]
public sealed class BootstrapApprovalByteGateTests
{
    [TestMethod]
    public void ApprovedReviewBytesAndApprovalBindingsRemainExact()
    {
        var bootstrapRoot = Path.Combine(
            AppContext.BaseDirectory,
            "ConformanceInputs",
            "Bootstrap");
        var designPath = Path.Combine(bootstrapRoot, "architecture-design.md");
        var planPath = Path.Combine(bootstrapRoot, "implementation-plan.md");
        var approvalPath = Path.Combine(
            bootstrapRoot,
            "bootstrap-approval-record.json");
        var manifestPath = Path.Combine(bootstrapRoot, "review-manifest.json");

        var designDigest = ComputeSha256(designPath);
        var planDigest = ComputeSha256(planPath);
        var approvalDigest = ComputeSha256(approvalPath);
        var plan = File.ReadAllText(planPath);
        var approval = File.ReadAllText(approvalPath);
        var manifest = File.ReadAllText(manifestPath);

        Assert.Contains(
            $"design-digest: sha256:{designDigest}",
            plan,
            StringComparison.Ordinal);
        AssertArtifactBinding(
            manifest,
            "pkid:design:program-kit:baseline",
            "0.3.0",
            designDigest);
        AssertArtifactBinding(
            manifest,
            "pkid:plan:program-kit:baseline",
            "0.3.0",
            planDigest);
        AssertObjectBinding(
            manifest,
            "approvalRecord",
            "pkid:approval-record:program-kit:bootstrap-review-set:0.3.0",
            approvalDigest);
        AssertObjectBinding(
            approval,
            "design",
            "pkid:design:program-kit:baseline",
            designDigest);
        AssertObjectBinding(
            approval,
            "plan",
            "pkid:plan:program-kit:baseline",
            planDigest);

        Assert.Contains(
            "\"reviewSetVersion\": \"0.3.0\"",
            manifest,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"version\": \"0.3.0\"",
            approval,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"decision\": \"approved\"",
            approval,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"state\": \"active\"",
            approval,
            StringComparison.Ordinal);
    }

    private static string ComputeSha256(string path)
    {
        Assert.IsTrue(File.Exists(path), path);
        return Convert
            .ToHexString(SHA256.HashData(File.ReadAllBytes(path)))
            .ToLowerInvariant();
    }

    private static void AssertArtifactBinding(
        string json,
        string artifactId,
        string artifactVersion,
        string digest)
    {
        var pattern = string.Concat(
            "\\\"artifactId\\\"\\s*:\\s*\\\"",
            Regex.Escape(artifactId),
            "\\\"[\\s\\S]*?\\\"artifactVersion\\\"\\s*:\\s*\\\"",
            Regex.Escape(artifactVersion),
            "\\\"[\\s\\S]*?\\\"sha256\\\"\\s*:\\s*\\\"",
            Regex.Escape(digest),
            "\\\"");
        Assert.IsTrue(
            Regex.IsMatch(json, pattern, RegexOptions.CultureInvariant),
            $"Missing exact artifact binding for {artifactId}@{artifactVersion}.");
    }

    private static void AssertObjectBinding(
        string json,
        string property,
        string identity,
        string digest)
    {
        var pattern = string.Concat(
            "\\\"",
            Regex.Escape(property),
            "\\\"\\s*:\\s*\\{[\\s\\S]*?\\\"",
            property == "approvalRecord" ? "recordId" : "artifactId",
            "\\\"\\s*:\\s*\\\"",
            Regex.Escape(identity),
            "\\\"[\\s\\S]*?\\\"sha256\\\"\\s*:\\s*\\\"",
            Regex.Escape(digest),
            "\\\"");
        Assert.IsTrue(
            Regex.IsMatch(json, pattern, RegexOptions.CultureInvariant),
            $"Missing exact {property} binding for {identity}.");
    }
}
