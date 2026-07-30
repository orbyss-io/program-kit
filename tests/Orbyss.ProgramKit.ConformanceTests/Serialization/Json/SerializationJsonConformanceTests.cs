using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;
using System.Xml.Linq;
namespace Orbyss.ProgramKit.ConformanceTests.Serialization.Json;

[TestClass]
public sealed class SerializationJsonConformanceTests
{
    private static readonly string[] ExpectedProjectReferences =
        ["Orbyss.ProgramKit.Artifacts"];
    private static readonly string[] ExpectedPackageReferences =
        ["Microsoft.Extensions.DependencyInjection.Abstractions"];
    private static readonly string[] ExpectedStrictRules =
    [
        "source-generated-metadata-only",
        "schema-declared-property-names",
        "case-sensitive-reads",
        "comments-disallowed",
        "trailing-commas-disallowed",
        "unmapped-members-disallowed",
        "null-properties-written",
        "strict-numbers",
        "reference-preservation-disallowed",
        "nfc-strings-required",
    ];
    private static readonly string[] ExpectedPrimitiveConverterTargets =
    [
        JsonTargetTypeClaim.For<ProgramKitIdentifier>(),
        JsonTargetTypeClaim.For<SemanticVersion>(),
        JsonTargetTypeClaim.For<SemanticVersionRange>(),
        JsonTargetTypeClaim.For<Sha256Digest>(),
    ];
    private static readonly string[] ExpectedJsonMetaMetadataTargets =
    [
        JsonTargetTypeClaim.For<ArtifactReference>(),
        JsonTargetTypeClaim.For<ProfileReference>(),
        JsonTargetTypeClaim.For<ArtifactContract>(),
        JsonTargetTypeClaim.For<ArtifactIdentity>(),
        JsonTargetTypeClaim.For<ArtifactCompatibility>(),
        JsonTargetTypeClaim.For<ArtifactProvenance>(),
        JsonTargetTypeClaim.For<ArtifactRepresentation>(),
        JsonTargetTypeClaim.For<ArtifactIntegrity>(),
        JsonTargetTypeClaim.For<JsonSerializationProfileRef>(),
        JsonTargetTypeClaim.For<JsonSerializationContributionRef>(),
        JsonTargetTypeClaim.For<JsonSerializationRules>(),
        JsonTargetTypeClaim.For<JsonSerializationLimits>(),
        JsonTargetTypeClaim.For<JsonSerializationProfile>(),
        JsonTargetTypeClaim.For<JsonSerializationProfileSelection>(),
        JsonTargetTypeClaim.For<JsonOwnedMechanicsSource>(),
        JsonTargetTypeClaim.For<JsonProfileSourceDescriptor>(),
        JsonTargetTypeClaim.For<JsonSerializationContributionDescriptor>(),
        JsonTargetTypeClaim.For<
            ArtifactEnvelope<JsonSerializationProfileSelection>>(),
    ];
    private static readonly string[] ExpectedJsonMetaConverterTargets =
    [
        .. ExpectedPrimitiveConverterTargets,
        JsonTargetTypeClaim.For<ArtifactStatus>(),
        JsonTargetTypeClaim.For<CompatibilityDimension>(),
        JsonTargetTypeClaim.For<CompatibilityClassification>(),
        JsonTargetTypeClaim.For<JsonProfileExtensibility>(),
        JsonTargetTypeClaim.For<JsonProfileSourceKind>(),
        JsonTargetTypeClaim.For<JsonSerializationContributionKind>(),
    ];
    private static readonly string[] ExpectedJsonContractsMechanicsSources =
    [
        "Orbyss.ProgramKit.Serialization.JSON/Composition/BuiltInPrimitiveConverterComposition.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ExactDecimalStringConverterPolicy.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/FrozenJsonProfile.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonBuilder.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonBuilderState.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonRegistrationMarker.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonRegistry.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonRegistryFactory.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonRegistryKey.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonServiceCollectionExtensions.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/JsonContributionTargetContract.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/JsonConverterFactoryContribution.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/JsonSerializationContribution.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/JsonTypeInfoResolverContribution.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/TypedJsonConverterContribution.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/DeclaredTargetJsonConverterFactory.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/ExactDecimalStringJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/ProgramKitIdentifierJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/SemanticVersionJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/SemanticVersionRangeJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/Sha256DigestJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Diagnostics/JsonExceptionBoundary.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Diagnostics/ProgramKitJsonDiagnosticIds.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Diagnostics/ProgramKitJsonException.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Metadata/DeclaredTargetJsonTypeInfoResolver.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Metadata/JsonTargetTypeIdentity.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Metadata/NullJsonTypeInfoResolver.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Profiles/JsonProfileOwnedConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Profiles/JsonProfileOwnedMechanics.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Profiles/JsonSerializationLimits.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/BoundedJsonBufferWriter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/JsonByteLimitExceededException.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/ProgramKitJsonSerializer.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/StrictJsonReadFailure.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/StrictJsonReadFailureLocator.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/StrictJsonReadPathSegment.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/StrictJsonResolvedFailure.cs",
    ];
    private static readonly string[] ExpectedJsonMetaMechanicsSources =
    [
        "Orbyss.ProgramKit.Serialization.JSON/Composition/BuiltInPrimitiveConverterComposition.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ExactDecimalStringConverterPolicy.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/FrozenJsonProfile.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/JsonMetaComposition.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonBuilder.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonBuilderState.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonRegistrationMarker.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonRegistry.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonRegistryFactory.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonRegistryKey.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Composition/ProgramKitJsonServiceCollectionExtensions.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/JsonContributionTargetContract.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/JsonConverterFactoryContribution.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/JsonSerializationContribution.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/JsonTypeInfoResolverContribution.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Contributions/TypedJsonConverterContribution.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/DeclaredTargetJsonConverterFactory.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/ExactDecimalStringJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/KebabCaseEnumJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/ProgramKitIdentifierJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/SemanticVersionJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/SemanticVersionRangeJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Converters/Sha256DigestJsonConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Diagnostics/JsonExceptionBoundary.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Diagnostics/ProgramKitJsonDiagnosticIds.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Diagnostics/ProgramKitJsonException.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Metadata/DeclaredTargetJsonTypeInfoResolver.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Metadata/JsonTargetTypeIdentity.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Metadata/NullJsonTypeInfoResolver.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Metadata/ProgramKitJsonMetaContext.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Profiles/JsonProfileOwnedConverter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Profiles/JsonProfileOwnedMechanics.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Profiles/JsonSerializationLimits.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/BoundedJsonBufferWriter.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/JsonByteLimitExceededException.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/ProgramKitJsonSerializer.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/StrictJsonReadFailure.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/StrictJsonReadFailureLocator.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/StrictJsonReadPathSegment.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Serialization/StrictJsonResolvedFailure.cs",
    ];
    private static readonly string[] ExpectedCanonicalMechanicsSources =
    [
        "Orbyss.ProgramKit.Serialization.JSON/Canonicalization/CanonicalJsonMember.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Canonicalization/CanonicalJsonValue.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Canonicalization/CanonicalizationState.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Canonicalization/IProgramKitJsonCanonicalizer.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Canonicalization/ProgramKitJsonCanonicalizer.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Diagnostics/ProgramKitJsonDiagnosticIds.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Diagnostics/ProgramKitJsonException.cs",
        "Orbyss.ProgramKit.Serialization.JSON/Profiles/JsonSerializationLimits.cs",
    ];

    [TestMethod]
    public void SerializationPackageHasTheExactApprovedDependencyClosure()
    {
        var projectFile = ConformanceInputs
            .Files("Projects", "Orbyss.ProgramKit.Serialization.JSON.csproj")
            .Single();
        var project = XDocument.Load(projectFile);
        var projectReferences = project
            .Descendants("ProjectReference")
            .Select(reference => Path.GetFileNameWithoutExtension(
                reference.Attribute("Include")?.Value))
            .ToArray();
        var packageReferences = project
            .Descendants("PackageReference")
            .Select(reference => reference.Attribute("Include")?.Value)
            .ToArray();

        Assert.AreSequenceEqual(
            ExpectedProjectReferences,
            projectReferences);
        Assert.AreSequenceEqual(
            ExpectedPackageReferences,
            packageReferences);
        Assert.IsEmpty(project.Descendants("FrameworkReference"));
        Assert.IsEmpty(project.Descendants("TargetFramework"));
        Assert.IsEmpty(project.Descendants("TargetFrameworks"));
        var schemaPackItem = project
            .Descendants("None")
            .Single(item => item.Attribute("Include")?.Value.Contains(
                @"schemas\serialization",
                StringComparison.Ordinal) == true);
        var packAttribute = schemaPackItem.Attribute("Pack");
        var packagePathAttribute = schemaPackItem.Attribute("PackagePath");
        Assert.IsNotNull(packAttribute);
        Assert.IsNotNull(packagePathAttribute);
        Assert.AreEqual("true", packAttribute.Value);
        Assert.AreEqual(
            "schemas/serialization/",
            packagePathAttribute.Value);
    }

    [TestMethod]
    public void SerializationSourceDoesNotUseDomTypesOrReflectionFallbacks()
    {
        var serializationSources = ConformanceInputs
            .Files("Source", "*.cs")
            .Where(path => path.Contains(
                "Orbyss.ProgramKit.Serialization.JSON",
                StringComparison.Ordinal))
            .ToArray();
        Assert.IsNotEmpty(serializationSources);
        var forbidden = new[]
        {
            "Newtonsoft",
            "DefaultJsonTypeInfoResolver",
            "TypeNameHandling",
            "AppDomain.CurrentDomain.GetAssemblies",
        };

        foreach (var sourceFile in serializationSources)
        {
            var source = File.ReadAllText(sourceFile);
            foreach (var token in forbidden)
            {
                Assert.IsFalse(
                    source.Contains(token, StringComparison.Ordinal),
                    $"{sourceFile} contains forbidden token {token}.");
            }

            var domTokens = new[]
            {
                "JsonElement",
                "JsonDocument",
                "JsonNode",
            };
            foreach (var token in domTokens)
            {
                Assert.AreEqual(
                    0,
                    source.Split(token, StringSplitOptions.None).Length - 1,
                    $"{sourceFile}: {token} is reserved for the approved Workbench DOM adapter.");
            }
        }
    }

    [TestMethod]
    public void BuiltInProfileReferencesBindExactCommittedSourceBytes()
    {
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var serializer = new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);
        AssertSerializationProfileSource(
            serializer,
            canonicalizer,
            "json-meta.profile.json",
            ProgramKitJsonProfiles.JsonMeta);
        AssertSerializationProfileSource(
            serializer,
            canonicalizer,
            "json-contracts.profile.json",
            ProgramKitJsonProfiles.JsonContracts);
        var canonicalSource = ReadProfileSource(
            serializer,
            canonicalizer,
            "canonical-json-rfc8785.profile.json",
            ProgramKitJsonProfiles.CanonicalJsonRfc8785.Digest);
        Assert.AreEqual(
            ProgramKitJsonProfiles.CanonicalJsonRfc8785.Identity,
            canonicalSource.Identity);
        Assert.AreEqual(
            ProgramKitJsonProfiles.CanonicalJsonRfc8785.Version,
            canonicalSource.Version);
        Assert.AreEqual(
            JsonProfileSourceKind.Canonicalization,
            canonicalSource.ProfileKind);
        Assert.IsNull(canonicalSource.CanonicalizationProfile);
        Assert.AreEqual(
            JsonProfileExtensibility.None,
            canonicalSource.Extensibility);
        Assert.AreSequenceEqual(
            Array.Empty<string>(),
            canonicalSource.BuiltInMetadataTargets.ToArray());
        Assert.AreSequenceEqual(
            Array.Empty<string>(),
            canonicalSource.BuiltInConverterTargets.ToArray());
        AssertOwnedMechanicsSources(
            canonicalSource,
            ExpectedCanonicalMechanicsSources);
    }

    [TestMethod]
    public void SerializationSchemaModuleHasCompleteValidSidecarsAndExactBytes()
    {
        SerializationJsonSchemaModule module = new();
        var validator = new ProgramKitSchemaModuleValidator();
        var validation = validator.Validate(module);

        Assert.IsTrue(
            validation.IsValid,
            string.Join(
                Environment.NewLine,
                validation.Diagnostics.Select(static diagnostic =>
                    $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}")));
        Assert.HasCount(5, module.Resources);
        foreach (var resource in module.Resources)
        {
            Assert.AreEqual(ArtifactStatus.Implemented, resource.Status);
            Assert.IsFalse(resource.Consumers.IsDefaultOrEmpty);
            Assert.IsFalse(resource.Provenance.SourceInputs.IsDefaultOrEmpty);
            Assert.IsFalse(resource.Compatibility.Dimensions.IsDefaultOrEmpty);
            using var stream = module.OpenRead(resource.SchemaReference);
            var digest = SHA256.HashData(stream);
            Assert.AreEqual(
                resource.SchemaReference.Digest.Value,
                string.Concat(
                    "sha256:",
                    Convert.ToHexString(digest).ToLowerInvariant()));
        }
    }

    [TestMethod]
    public void CanonicalValueExposesOnlyOpaqueDefensiveBytes()
    {
        Assert.IsTrue(typeof(CanonicalJsonValue).IsSealed);
        Assert.IsFalse(typeof(CanonicalJsonValue).IsValueType);
        Assert.DoesNotContain(
            static constructor => constructor.IsPublic,
            typeof(CanonicalJsonValue).GetConstructors());
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var value = canonicalizer.Canonicalize(
            """{"b":2,"a":1}"""u8,
            JsonSerializationLimits.Default);
        var first = value.ToArray();
        first[0] = (byte)'[';
        var second = value.ToArray();

        Assert.AreEqual((byte)'{', second[0]);
        Assert.AreEqual(
            """{"a":1,"b":2}""",
            Encoding.UTF8.GetString(second));
        Assert.AreEqual(71, value.Digest.Value.Length);
        Assert.DoesNotContain(
            static property =>
                property.PropertyType.Name.Contains(
                    "Json",
                    StringComparison.Ordinal) &&
                property.Name != nameof(CanonicalJsonValue.Digest),
            typeof(CanonicalJsonValue).GetProperties());
    }

    [TestMethod]
    public void JsonDiagnosticsAreCompleteUniqueAndStable()
    {
        var definitions = ProgramKitJsonDiagnosticCatalog.Definitions;

        Assert.HasCount(21, definitions);
        Assert.HasCount(
            definitions.Length,
            definitions.Select(static definition => definition.Id)
                .Distinct(StringComparer.Ordinal));
        Assert.AreSequenceEqual(
            Enumerable.Range(1, 21)
                .Select(static number => $"PKJSN{number:000}")
                .ToArray(),
            definitions.Select(static definition => definition.Id).ToArray());
    }

    private static void AssertSerializationProfileSource(
        IProgramKitJsonSerializer serializer,
        IProgramKitJsonCanonicalizer canonicalizer,
        string fileName,
        JsonSerializationProfile profile)
    {
        var source = ReadProfileSource(
            serializer,
            canonicalizer,
            fileName,
            profile.Reference.Digest);
        Assert.AreEqual(profile.Reference.Identity, source.Identity);
        Assert.AreEqual(profile.Reference.Version, source.Version);
        Assert.AreEqual(JsonProfileSourceKind.Serialization, source.ProfileKind);
        Assert.AreEqual(
            profile.CanonicalizationProfile,
            source.CanonicalizationProfile);
        Assert.AreEqual(profile.Extensibility, source.Extensibility);
        Assert.AreEqual(profile.MaximumLimits, source.MaximumLimits);
        Assert.AreSequenceEqual(
            ExpectedStrictRules,
            source.Rules,
            SequenceOrder.InAnyOrder);
        if (profile.Reference == ProgramKitJsonProfiles.JsonMeta.Reference)
        {
            Assert.AreSequenceEqual(
                ExpectedJsonMetaMetadataTargets,
                source.BuiltInMetadataTargets.ToArray());
            Assert.AreSequenceEqual(
                ExpectedJsonMetaConverterTargets,
                source.BuiltInConverterTargets.ToArray());
        }
        else
        {
            Assert.AreSequenceEqual(
                Array.Empty<string>(),
                source.BuiltInMetadataTargets.ToArray());
            Assert.AreSequenceEqual(
                ExpectedPrimitiveConverterTargets,
                source.BuiltInConverterTargets.ToArray());
        }

        AssertOwnedMechanicsSources(
            source,
            profile.Reference == ProgramKitJsonProfiles.JsonMeta.Reference
                ? ExpectedJsonMetaMechanicsSources
                : ExpectedJsonContractsMechanicsSources);
    }

    private static void AssertOwnedMechanicsSources(
        JsonProfileSourceDescriptor source,
        string[] expectedRelativePaths)
    {
        Assert.AreSequenceEqual(
            expectedRelativePaths,
            source.OwnedMechanicsSources
                .Select(static mechanics => mechanics.RelativePath)
                .ToArray());
        var sourceFiles = ConformanceInputs.Files("Source", "*.cs");
        foreach (var mechanics in source.OwnedMechanicsSources)
        {
            var normalizedSuffix = string.Concat(
                "/",
                mechanics.RelativePath);
            var sourcePath = sourceFiles.Single(path =>
                path.Replace('\\', '/').EndsWith(
                    normalizedSuffix,
                    StringComparison.Ordinal));
            var bytes = File.ReadAllBytes(sourcePath);
            Assert.IsFalse(
                bytes.Length >= 3 &&
                bytes[0] == 0xef &&
                bytes[1] == 0xbb &&
                bytes[2] == 0xbf,
                $"{mechanics.RelativePath} must not contain a UTF-8 BOM.");
            Assert.IsLessThan(
                0,
                bytes.AsSpan().IndexOf("\r\n"u8),
                $"{mechanics.RelativePath} must use LF line endings.");
            Assert.AreEqual(
                mechanics.Digest.Value,
                string.Concat(
                    "sha256:",
                    Convert.ToHexString(SHA256.HashData(bytes))
                        .ToLowerInvariant()),
                mechanics.RelativePath);
        }
    }

    private static JsonProfileSourceDescriptor ReadProfileSource(
        IProgramKitJsonSerializer serializer,
        IProgramKitJsonCanonicalizer canonicalizer,
        string fileName,
        Sha256Digest expected)
    {
        var path = ConformanceInputs
            .Files("Schemas/serialization/profiles", fileName)
            .Single();
        var bytes = File.ReadAllBytes(path);
        Assert.IsFalse(
            bytes.Length >= 3 &&
            bytes[0] == 0xef &&
            bytes[1] == 0xbb &&
            bytes[2] == 0xbf,
            $"{fileName} must not contain a UTF-8 BOM.");
        Assert.IsLessThan(
            0,
            bytes.AsSpan().IndexOf("\r\n"u8),
            $"{fileName} must use LF line endings.");
        Assert.AreSequenceEqual(
            canonicalizer.Canonicalize(
                bytes,
                JsonSerializationLimits.Default).ToArray(),
            bytes,
            $"{fileName} must contain exact canonical JSON bytes.");
        var digest = SHA256.HashData(bytes);
        Assert.AreEqual(
            expected.Value,
            string.Concat(
                "sha256:",
                Convert.ToHexString(digest).ToLowerInvariant()));
        var source = serializer.Read<JsonProfileSourceDescriptor>(
            bytes,
            ProgramKitJsonProfiles.JsonMeta.Reference,
            JsonSerializationLimits.Default);
        Assert.AreEqual(
            "https://schemas.orbyss.io/program-kit/serialization/1.0.0/profile-source.schema.json",
            source.Schema.AbsoluteUri,
            fileName);
        return source;
    }
}
