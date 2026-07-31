using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Planning.Plans;
using Orbyss.ProgramKit.Planning.Schemas;
using Orbyss.ProgramKit.Planning.Validation;
using Orbyss.ProgramKit.Quality.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.UnitTests.Planning.Plans;

[TestClass]
public sealed partial class HostToolingImplementationPlanTests
{
    private const string ApprovedPlanDigest =
        "8144a67d5d919211f87a2d30a4d7a870f299c126e138986c6f079e133734f9a5";

    [TestMethod]
    public void CanonicalPlanPreservesApprovedMarkdownAndValidatesSemantically()
    {
        var extensionRoot = Path.Combine(
            FindProgramKitRoot().FullName,
            ".review-sets",
            "host-tooling");
        var markdownPath = Path.Combine(extensionRoot, "implementation-plan.md");
        var jsonPath = Path.Combine(extensionRoot, "implementation-plan.json");
        var markdownBytes = File.ReadAllBytes(markdownPath);
        var actualDigest = Convert.ToHexString(
                SHA256.HashData(markdownBytes))
            .ToLowerInvariant();
        Assert.AreEqual(ApprovedPlanDigest, actualDigest);

        var markdown = Encoding.UTF8.GetString(markdownBytes);
        var jsonBytes = File.ReadAllBytes(jsonPath);
        using var document = JsonDocument.Parse(jsonBytes);
        var root = document.RootElement;
        var typedPlan = ReadPlan(root);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        ImplementationPlanDocumentValidator semanticValidator =
            new(envelopeValidator);

        var semanticValidation = semanticValidator.Validate(typedPlan);

        Assert.IsTrue(
            semanticValidation.IsValid,
            string.Join(
                Environment.NewLine,
                semanticValidation.Diagnostics.Select(static diagnostic =>
                    string.Concat(
                        diagnostic.Id,
                        " ",
                        diagnostic.Path,
                        " ",
                        diagnostic.Message))));
        AssertApprovedProjection(markdown, root);
    }

    [TestMethod]
    public void CanonicalPlanConformsToV2SchemaAndRoundTripsWithoutJsonDrift()
    {
        var jsonPath = Path.Combine(
            FindProgramKitRoot().FullName,
            ".review-sets",
            "host-tooling",
            "implementation-plan.json");
        var jsonBytes = File.ReadAllBytes(jsonPath);
        PlanCompositeSchemaModule schemas = new(
        [
            new ArtifactsSchemaModule(),
            new QualitySchemaModule(),
            new PlanningSchemaModule(),
        ]);
        var schema = schemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:implementation-plan" &&
            resource.SchemaReference.Version.Value == "2.0.0");
        ProgramKitJsonCanonicalizer canonicalizer = new();
        ProgramKitSchemaModuleValidator moduleValidator = new();
        JsonSchemaWorkbenchValidator validator =
            new(canonicalizer, moduleValidator);

        var validation = validator.Validate(
            jsonBytes,
            schemas,
            schema.SchemaReference,
            new JsonSerializationLimits(
                MaxUtf8Bytes: 1_000_000,
                MaxDepth: 64,
                MaxTokens: 100_000,
                MaxObjectMembers: 100_000,
                MaxBufferedObjectBytes: 1_000_000));
        using var original = JsonDocument.Parse(jsonBytes);
        var roundTripBytes = JsonSerializer.SerializeToUtf8Bytes(
            original.RootElement);
        using var roundTrip = JsonDocument.Parse(roundTripBytes);

        Assert.IsTrue(
            validation.IsValid,
            string.Join(
                Environment.NewLine,
                validation.Diagnostics.Select(static diagnostic =>
                    string.Concat(
                        diagnostic.Id,
                        " ",
                        diagnostic.Path,
                        " ",
                        diagnostic.Message))));
        Assert.IsTrue(JsonElement.DeepEquals(
            original.RootElement,
            roundTrip.RootElement));
    }

    private static void AssertApprovedProjection(
        string markdown,
        JsonElement root)
    {
        var headingMatches = WorkUnitHeadingRegex().Matches(markdown);
        var workUnits = root.GetProperty("workUnits").EnumerateArray().ToArray();
        Assert.HasCount(headingMatches.Count, workUnits);
        Assert.HasCount(16, workUnits);

        for (var index = 0; index < headingMatches.Count; index++)
        {
            var match = headingMatches[index];
            var sectionStart = match.Index + match.Length;
            var sectionEnd = index + 1 < headingMatches.Count
                ? headingMatches[index + 1].Index
                : markdown.Length;
            var section = markdown[sectionStart..sectionEnd];
            var workUnit = workUnits[index];
            Assert.AreEqual(
                match.Groups["id"].Value,
                workUnit.GetProperty("workUnitId").GetString());
            Assert.AreEqual(
                ReadBlock(section, "**Required outcomes:**", "**Verification:**"),
                workUnit.GetProperty("requiredOutcome").GetString());
            Assert.AreEqual(
                ReadBlock(section, "**Allowed edits:**", "**Required outcomes:**"),
                workUnit.GetProperty("allowedEdits")[0].GetString());
            Assert.AreEqual(
                ReadBlock(section, "**Verification:**", "**Stop conditions:**"),
                workUnit.GetProperty("verification")[0]
                    .GetProperty("expectedObservation")
                    .GetString());
            Assert.AreEqual(
                ReadBlock(section, "**Stop conditions:**", null),
                workUnit.GetProperty("stopConditions")[0].GetString());
            Assert.AreSequenceEqual(
                ExpandIds(
                    ReadBlock(
                        section,
                        "**Depends on:**",
                        "**Allowed edits:**"),
                    "W"),
                workUnit.GetProperty("dependsOn")
                    .EnumerateArray()
                    .Select(static value => value.GetString()!)
                    .ToArray());

            var output = workUnit.GetProperty("outputs")[0];
            Assert.AreEqual("prospective", output.GetProperty("state").GetString());
            Assert.AreEqual(JsonValueKind.Null, output.GetProperty("integrityDigest").ValueKind);
        }

        var requirementOutcomes = RequirementRowRegex()
            .Matches(markdown)
            .ToDictionary(
                static match => match.Groups["id"].Value,
                static match => match.Groups["outcome"].Value.Trim(),
                StringComparer.Ordinal);
        Assert.HasCount(29, requirementOutcomes);
        var traces = root.GetProperty("trace")
            .EnumerateArray()
            .ToDictionary(
                static trace => trace.GetProperty("requirementId").GetString()!,
                StringComparer.Ordinal);
        Assert.HasCount(requirementOutcomes.Count, traces);
        foreach (var (requirementId, outcome) in requirementOutcomes)
        {
            Assert.AreEqual(
                outcome,
                traces[requirementId]
                    .GetProperty("implementationOutcome")
                    .GetString());
            Assert.AreEqual(
                outcome,
                traces[requirementId]
                    .GetProperty("observableAcceptanceOutcome")
                    .GetString());
        }
    }

    private static ImplementationPlanDocument ReadPlan(JsonElement root) =>
        new(
            ReadReference(root.GetProperty("design")),
            new ProgramKitIdentifier(root.GetProperty("ownerId").GetString()!),
            ImplementationPlanState.ReadyForHumanDecision,
            ReadStrings(root.GetProperty("requirementIds")),
            root.GetProperty("workUnits")
                .EnumerateArray()
                .Select(ReadWorkUnit)
                .ToImmutableArray(),
            [],
            root.GetProperty("trace")
                .EnumerateArray()
                .Select(ReadTrace)
                .ToImmutableArray(),
            []);

    private static PlanWorkUnit ReadWorkUnit(JsonElement value) =>
        new(
            value.GetProperty("workUnitId").GetString()!,
            value.GetProperty("requiredOutcome").GetString()!,
            value.GetProperty("sequence").GetInt32(),
            null,
            ReadStrings(value.GetProperty("dependsOn")),
            value.GetProperty("inputs")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray(),
            value.GetProperty("outputs")
                .EnumerateArray()
                .Select(ReadOutput)
                .ToImmutableArray(),
            ReadStrings(value.GetProperty("allowedEdits")),
            [],
            [],
            [],
            [],
            ReadStrings(value.GetProperty("stopConditions")),
            value.GetProperty("verification")
                .EnumerateArray()
                .Select(ReadVerification)
                .ToImmutableArray(),
            []);

    private static PlannedArtifactReference ReadOutput(JsonElement value) =>
        new(
            new ProgramKitIdentifier(value.GetProperty("identity").GetString()!),
            new SemanticVersion(value.GetProperty("version").GetString()!),
            PlannedArtifactState.Prospective,
            null);

    private static PlanVerificationCommand ReadVerification(JsonElement value) =>
        new(
            value.GetProperty("executable").GetString()!,
            ReadStrings(value.GetProperty("arguments")),
            value.GetProperty("workingDirectory").GetString()!,
            value.GetProperty("expectedObservation").GetString()!);

    private static RequirementTrace ReadTrace(JsonElement value) =>
        new(
            value.GetProperty("requirementId").GetString()!,
            new ProgramKitIdentifier(value.GetProperty("ownerId").GetString()!),
            ReadReference(value.GetProperty("contractOrArtifact")),
            ReadStrings(value.GetProperty("workUnitIds")),
            value.GetProperty("implementationOutcome").GetString()!,
            [],
            [],
            [],
            value.GetProperty("observableAcceptanceOutcome").GetString()!);

    private static ArtifactReference ReadReference(JsonElement value) =>
        new(
            new ProgramKitIdentifier(value.GetProperty("identity").GetString()!),
            new SemanticVersion(value.GetProperty("version").GetString()!),
            new Sha256Digest(value.GetProperty("digest").GetString()!));

    private static ImmutableArray<string> ReadStrings(JsonElement value) =>
        value.EnumerateArray()
            .Select(static item => item.GetString()!)
            .ToImmutableArray();

    private static string ReadBlock(
        string section,
        string startMarker,
        string? endMarker)
    {
        var start = section.IndexOf(startMarker, StringComparison.Ordinal);
        if (start < 0)
        {
            return string.Empty;
        }

        start += startMarker.Length;
        var end = endMarker is null
            ? section.Length
            : section.IndexOf(endMarker, start, StringComparison.Ordinal);
        if (end < 0)
        {
            end = section.Length;
        }

        return WhitespaceRegex()
            .Replace(section[start..end], " ")
            .Trim();
    }

    private static string[] ExpandIds(string value, string kind)
    {
        var plain = value.Replace("`", string.Empty, StringComparison.Ordinal);
        var result = new HashSet<string>(StringComparer.Ordinal);
        var ranges = Regex.Matches(
            plain,
            string.Concat(
                kind,
                @"(?<start>\d{3})\s*[–-]\s*",
                kind,
                @"(?<end>\d{3})"));
        foreach (Match range in ranges)
        {
            var start = int.Parse(
                range.Groups["start"].Value,
                CultureInfo.InvariantCulture);
            var end = int.Parse(
                range.Groups["end"].Value,
                CultureInfo.InvariantCulture);
            foreach (var number in Enumerable.Range(start, end - start + 1))
            {
                result.Add(string.Concat(
                    "PKHT-",
                    kind,
                    number.ToString("D3", CultureInfo.InvariantCulture)));
            }
        }

        foreach (Match match in Regex.Matches(
                     plain,
                     string.Concat(kind, @"(?<value>\d{3})")))
        {
            result.Add(string.Concat(
                "PKHT-",
                kind,
                match.Groups["value"].Value));
        }

        return result.Order(StringComparer.Ordinal).ToArray();
    }

    private static DirectoryInfo FindProgramKitRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException(
            "The Program Kit repository root could not be found.");
    }

    [GeneratedRegex(@"^### `(?<id>PKHT-W\d{3})`[^\r\n]*", RegexOptions.Multiline)]
    private static partial Regex WorkUnitHeadingRegex();

    [GeneratedRegex(
        @"^\|\s*`(?<id>PKHT-R\d{3})`\s*\|\s*(?<outcome>.+?)\s*\|$",
        RegexOptions.Multiline)]
    private static partial Regex RequirementRowRegex();

    [GeneratedRegex(@"\s+")]
    private static partial Regex WhitespaceRegex();

}
