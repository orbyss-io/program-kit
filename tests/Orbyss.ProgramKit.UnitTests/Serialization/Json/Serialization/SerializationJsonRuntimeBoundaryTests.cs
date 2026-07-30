using System.Collections.Immutable;
using System.Text;
using System.Text.RegularExpressions;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

[TestClass]
public sealed class SerializationJsonRuntimeBoundaryTests
{
    private static readonly Sha256Digest ValidDigest = new("sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
    [TestMethod]
    public void SerializerContractRequiresExplicitPerOperationLimits()
    {
        var operations = typeof(IProgramKitJsonSerializer).GetMethods().Where(static method => method.Name is "Read" or "Write").ToArray();
        Assert.HasCount(2, operations);
        foreach (var operation in operations)
        {
            var limits = operation.GetParameters().Single(static parameter => parameter.ParameterType == typeof(JsonSerializationLimits));
            Assert.IsFalse(limits.HasDefaultValue, operation.Name);
        }
    }

    [TestMethod]
    [DataRow(
        """{"identity":"invalid","version":"1.0.0","digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}""",
        "/identity",
        "identity",
        "Orbyss.ProgramKit.Artifacts.Primitives.ProgramKitIdentifier")]
    [DataRow(
        """{"identity":"pkid:profile:tests:valid","version":"1","digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}""",
        "/version",
        "version",
        "Orbyss.ProgramKit.Artifacts.Primitives.SemanticVersion")]
    [DataRow(
        """{"identity":"pkid:profile:tests:valid","version":"1.0.0","digest":"invalid"}""",
        "/digest",
        "digest",
        "Orbyss.ProgramKit.Artifacts.Primitives.Sha256Digest")]
    public void MalformedPrimitiveTextNeverEscapesPrimitiveExceptions(
        string json,
        string expectedPath,
        string expectedMember,
        string expectedType)
    {
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() => CreateMetaSerializer().Read<JsonSerializationProfileRef>(Encoding.UTF8.GetBytes(json), ProgramKitJsonProfiles.JsonMeta.Reference, JsonSerializationLimits.Default));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidJson, exception.Diagnostic.Id);
        Assert.AreEqual(expectedPath, exception.Diagnostic.Path);
        Assert.Contains($"Member '{expectedMember}'", exception.Message);
        Assert.Contains($"expected CLR type '{expectedType}'", exception.Message);
        Assert.IsInstanceOfType<JsonException>(exception.InnerException);
        Assert.IsNotInstanceOfType<ArgumentException>(exception);
        Assert.IsNotInstanceOfType<NullReferenceException>(exception);
    }

    [TestMethod]
    public void DefaultPrimitiveValuesNeverSerializeAsNullWireValues()
    {
        AssertInvalidWrite(new JsonSerializationProfileRef(default, new SemanticVersion("1.0.0"), ValidDigest));
        AssertInvalidWrite(new JsonSerializationProfileRef(ProgramKitJsonProfiles.JsonMeta.Reference.Identity, default, ValidDigest));
        AssertInvalidWrite(new JsonSerializationProfileRef(ProgramKitJsonProfiles.JsonMeta.Reference.Identity, new SemanticVersion("1.0.0"), default));
    }

    [TestMethod]
    [DataRow("""{"identity":"pkid:profile:tests:valid","version":"1.0.0"}""")]
    [DataRow("""{"identity":null,"version":"1.0.0","digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}""")]
    public void RequiredConstructorAndNullabilityRulesAreEnforced(string json)
    {
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() => CreateMetaSerializer().Read<JsonSerializationProfileRef>(Encoding.UTF8.GetBytes(json), ProgramKitJsonProfiles.JsonMeta.Reference, JsonSerializationLimits.Default));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidJson, exception.Diagnostic.Id);
        var expectedPath = json.Contains(
            "\"digest\"",
            StringComparison.Ordinal)
            ? "/identity"
            : "/digest";
        Assert.AreEqual(expectedPath, exception.Diagnostic.Path);
        Assert.Contains(
            $"Member '{expectedPath[1..]}'",
            exception.Message);
    }

    [TestMethod]
    public void NonNullableConstructorParametersRejectJsonNull()
    {
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() => CreateNullableReadSerializer().Read<NonNullableReadModel>("""{"Value":null}"""u8.ToArray(), ProgramKitJsonProfiles.JsonContracts.Reference, JsonSerializationLimits.Default));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidJson, exception.Diagnostic.Id);
        Assert.AreEqual("/Value", exception.Diagnostic.Path);
        Assert.Contains("Member 'Value'", exception.Message);
        Assert.Contains(
            "expected CLR type 'System.String'",
            exception.Message);
        Assert.IsInstanceOfType<JsonException>(exception.InnerException);
    }

    [TestMethod]
    [DataRow(
        """{"profile":{"identity":"pkid:profile:program-kit:json-meta","version":"1.0.0","digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},"contributions":{}}""",
        "/contributions",
        "contributions",
        "System.Collections.Immutable.ImmutableArray")]
    [DataRow(
        """{"profile":{"identity":"pkid:profile:program-kit:json-meta","version":"1.0.0","digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},"contributions":[],"unknown":true}""",
        "/unknown",
        "unknown",
        "Orbyss.ProgramKit.Serialization.Json.Profiles.JsonSerializationProfileSelection")]
    public void WrongContainerAndUnknownMemberFailuresAreLocated(
        string json,
        string expectedPath,
        string expectedMember,
        string expectedTypeFragment)
    {
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            CreateMetaSerializer().Read<JsonSerializationProfileSelection>(
                Encoding.UTF8.GetBytes(json),
                ProgramKitJsonProfiles.JsonMeta.Reference,
                JsonSerializationLimits.Default));

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidJson,
            exception.Diagnostic.Id);
        Assert.AreEqual(expectedPath, exception.Diagnostic.Path);
        Assert.Contains($"Member '{expectedMember}'", exception.Message);
        Assert.Contains(expectedTypeFragment, exception.Message);
    }

    [TestMethod]
    public void ReadSideNotSupportedFailureMapsToMetadataDiagnostic()
    {
        var serializer = CreateNotSupportedReadSerializer();
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() => serializer.Read<NotSupportedReadModel>("\"value\""u8.ToArray(), ProgramKitJsonProfiles.JsonContracts.Reference, JsonSerializationLimits.Default));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.TypeMetadataUnavailable, exception.Diagnostic.Id);
        Assert.IsInstanceOfType<NotSupportedException>(exception.InnerException);
    }

    [TestMethod]
    public void ConverterFailureBoundaryNormalizesNonfatalAndPreservesFatalExceptions()
    {
        var serializer = CreateFailureBoundarySerializer();

        var readException = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            serializer.Read<BoundaryToken>(
                "\"nonfatal\""u8.ToArray(),
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));
        var writeException = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            serializer.Write(
                new BoundaryToken("nonfatal"),
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidJson,
            readException.Diagnostic.Id);
        Assert.AreEqual(string.Empty, readException.Diagnostic.Path);
        Assert.Contains("Member '<root>'", readException.Message);
        Assert.Contains(
            $"expected CLR type '{typeof(BoundaryToken).FullName}'",
            readException.Message);
        Assert.IsInstanceOfType<FormatException>(readException.InnerException);
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidJson,
            writeException.Diagnostic.Id);
        Assert.IsInstanceOfType<OverflowException>(writeException.InnerException);
        Assert.ThrowsExactly<SimulatedFatalJsonException>(() =>
            serializer.Read<BoundaryToken>(
                "\"fatal\""u8.ToArray(),
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));
        Assert.ThrowsExactly<SimulatedFatalJsonException>(() =>
            serializer.Write(
                new BoundaryToken("fatal"),
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));
    }

    [TestMethod]
    public void WriteEnforcesTheByteLimitWhileTheSerializerProducesBytes()
    {
        var selection = new JsonSerializationProfileSelection(ProgramKitJsonProfiles.JsonContracts.Reference, []);
        var serializer = CreateMetaSerializer();
        var baseline = serializer.Write(selection, ProgramKitJsonProfiles.JsonMeta.Reference, JsonSerializationLimits.Default);
        var exactLimits = new JsonSerializationLimits(MaxUtf8Bytes: baseline.Length, MaxDepth: 16, MaxTokens: 1_000, MaxObjectMembers: 100, MaxBufferedObjectBytes: baseline.Length);
        var exact = serializer.Write(selection, ProgramKitJsonProfiles.JsonMeta.Reference, exactLimits);
        Assert.AreEqual(baseline, exact);
        var smallerLimits = exactLimits with
        {
            MaxUtf8Bytes = baseline.Length - 1,
            MaxBufferedObjectBytes = baseline.Length - 1,
        };
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() => serializer.Write(selection, ProgramKitJsonProfiles.JsonMeta.Reference, smallerLimits));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.ByteLimitExceeded, exception.Diagnostic.Id);
    }

    [TestMethod]
    public void NullOperationLimitsMapToAStableProfileDiagnostic()
    {
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() => CreateMetaSerializer().Write(new JsonSerializationProfileSelection(ProgramKitJsonProfiles.JsonContracts.Reference, []), ProgramKitJsonProfiles.JsonMeta.Reference, null!));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidProfile, exception.Diagnostic.Id);
        Assert.AreEqual("/limits", exception.Diagnostic.Path);
    }

    [TestMethod]
    public void SerializationProfileSchemaRequiresTheExactCanonicalProfile()
    {
        SerializationJsonSchemaModule module = new();
        var resource = module.Resources.Single(static candidate => candidate.SchemaReference.Identity.Name == "json-serialization-profile");
        using var stream = module.OpenRead(resource.SchemaReference);
        using var reader = new StreamReader(stream, Encoding.UTF8, detectEncodingFromByteOrderMarks: false);
        var schema = reader.ReadToEnd();
        Assert.Contains("""
            "canonicalizationProfile": {
                  "allOf": [
                    {
                      "$ref": "definitions.schema.json#/$defs/profileReference"
                    },
                    {
                      "const": {
                        "identity": "pkid:profile:program-kit:canonical-json-rfc8785",
                        "version": "1.0.0",
                        "digest": "sha256:5f6b81547f1c025ec20fafbd5701b4506970cb58ca89e1679ebbe40a9551aa8b"
                      }
                    }
                  ]
                }
            """, schema);
    }

    [TestMethod]
    [DataRow("1.0.0-0", true)]
    [DataRow("1.0.0-alpha.01", false)]
    [DataRow("1.0.0-01", false)]
    [DataRow("01.0.0", false)]
    public void SerializationSemanticVersionSchemaMatchesTheRuntime(
        string version,
        bool expected)
    {
        const string pattern =
            """^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$""";
        SerializationJsonSchemaModule module = new();
        var resource = module.Resources.Single(static candidate =>
            candidate.SchemaReference.Identity.Name ==
                "serialization-definitions");
        using var stream = module.OpenRead(resource.SchemaReference);
        using var reader = new StreamReader(
            stream,
            Encoding.UTF8,
            detectEncodingFromByteOrderMarks: false);
        var schema = reader.ReadToEnd();

        Assert.Contains(
            pattern.Replace("\\", "\\\\", StringComparison.Ordinal),
            schema);
        Assert.AreEqual(
            expected,
            Regex.IsMatch(
                version,
                pattern,
                RegexOptions.CultureInvariant));
        Assert.AreEqual(
            expected,
            SemanticVersion.TryParse(version, out _));
    }

    private static ProgramKitJsonSerializer CreateMetaSerializer()
    {
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        return new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);
    }

    private static ProgramKitJsonSerializer CreateFailureBoundarySerializer()
    {
        var target = JsonTargetTypeClaim.For<BoundaryToken>();
        var resolver = new JsonTypeInfoResolverContribution(
            JsonContributionTestFactory.CreateDescriptor(
                "failure-boundary-metadata",
                "4",
                JsonSerializationContributionKind.TypeInfoResolver,
                target),
            BoundaryTokenJsonContext.Default);
        var converter = new TypedJsonConverterContribution<BoundaryToken>(
            JsonContributionTestFactory.CreateDescriptor(
                "failure-boundary-converter",
                "5",
                JsonSerializationContributionKind.TypedConverter,
                target),
            new FailureBoundaryTokenConverter());
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            resolver);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            converter);
        return new ProgramKitJsonSerializer(
            builder.Freeze(),
            new ProgramKitJsonCanonicalizer());
    }

    private static ProgramKitJsonSerializer CreateNotSupportedReadSerializer()
    {
        var resolverIdentity = new ProgramKitIdentifier("pkid:json-contribution:tests:not-supported-read-metadata");
        var converterIdentity = new ProgramKitIdentifier("pkid:json-contribution:tests:not-supported-read-converter");
        var resolverDescriptor = new JsonSerializationContributionDescriptor(new JsonSerializationContributionRef(resolverIdentity, new SemanticVersion("1.0.0"), new Sha256Digest("sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")), new ProgramKitIdentifier("pkid:package:tests:serialization-fixtures"), ProgramKitJsonProfiles.JsonContracts.Reference.Identity, new SemanticVersionRange("[1.0.0,2.0.0)"), JsonSerializationContributionKind.TypeInfoResolver, [JsonTargetTypeClaim.For<NotSupportedReadModel>()], ImmutableArray<ProgramKitIdentifier>.Empty, [converterIdentity]);
        var converterDescriptor = new JsonSerializationContributionDescriptor(new JsonSerializationContributionRef(converterIdentity, new SemanticVersion("1.0.0"), new Sha256Digest("sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")), new ProgramKitIdentifier("pkid:package:tests:serialization-fixtures"), ProgramKitJsonProfiles.JsonContracts.Reference.Identity, new SemanticVersionRange("[1.0.0,2.0.0)"), JsonSerializationContributionKind.TypedConverter, [JsonTargetTypeClaim.For<NotSupportedReadModel>()], [resolverIdentity], ImmutableArray<ProgramKitIdentifier>.Empty);
        var resolver = new JsonTypeInfoResolverContribution(
            resolverDescriptor,
            JsonNotSupportedReadTestContext.Default);
        var converter = new TypedJsonConverterContribution<NotSupportedReadModel>(
            converterDescriptor,
            new NotSupportedReadModelConverter());
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            resolver);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            converter);
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        return new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);
    }

    private static ProgramKitJsonSerializer CreateNullableReadSerializer()
    {
        var descriptor = new JsonSerializationContributionDescriptor(new JsonSerializationContributionRef(new ProgramKitIdentifier("pkid:json-contribution:tests:nullable-read-metadata"), new SemanticVersion("1.0.0"), new Sha256Digest("sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd")), new ProgramKitIdentifier("pkid:package:tests:serialization-fixtures"), ProgramKitJsonProfiles.JsonContracts.Reference.Identity, new SemanticVersionRange("[1.0.0,2.0.0)"), JsonSerializationContributionKind.TypeInfoResolver, [JsonTargetTypeClaim.For<NonNullableReadModel>()], ImmutableArray<ProgramKitIdentifier>.Empty, ImmutableArray<ProgramKitIdentifier>.Empty);
        var resolver = new JsonTypeInfoResolverContribution(
            descriptor,
            JsonNonNullableReadTestContext.Default);
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            resolver);
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        return new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);
    }

    private static void AssertInvalidWrite(JsonSerializationProfileRef value)
    {
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() => CreateMetaSerializer().Write(value, ProgramKitJsonProfiles.JsonMeta.Reference, JsonSerializationLimits.Default));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidJson, exception.Diagnostic.Id);
        Assert.IsInstanceOfType<JsonException>(exception.InnerException);
        Assert.IsNotInstanceOfType<ArgumentException>(exception);
        Assert.IsNotInstanceOfType<NullReferenceException>(exception);
    }
}
