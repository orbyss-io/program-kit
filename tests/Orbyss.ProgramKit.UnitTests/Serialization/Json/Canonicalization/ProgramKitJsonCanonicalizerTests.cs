using System.Text;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Canonicalization;

[TestClass]
public sealed class ProgramKitJsonCanonicalizerTests
{
    [TestMethod]
    public void CanonicalizerMatchesTheOfficialRfc8785Sample()
    {
        var input = """
            {
              "numbers": [333333333.33333329, 1E30, 4.50, 2e-3, 0.000000000000000000000000001],
              "string": "\u20ac$\u000F\u000aA'\u0042\u0022\u005c\\\"\/",
              "literals": [null, true, false]
            }
            """;
        Assert.AreEqual(
            """{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],"string":"€$\u000f\nA'B\"\\\\\"/"}""",
            Canonical(input));
    }

    [TestMethod]
    public void OfficialExponentNumberRemainsValidUnderTheStrictLexicalGuard()
    {
        Assert.AreEqual("1e+30", Canonical("1E30"));
    }

    [TestMethod]
    [DataRow("9007199254740992")]
    [DataRow("9007199254740992.0")]
    [DataRow("9.007199254740992e15")]
    public void UnsafeCanonicalIntegerResultsAreRejectedIdempotently(
        string input)
    {
        var exception =
            Assert.ThrowsExactly<ProgramKitJsonException>(
                () => Canonical(input));
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidNumber,
            exception.Diagnostic.Id);
    }

    [TestMethod]
    public void CanonicalizerUsesRfc8785Utf16PropertyOrdering()
    {
        const string input =
            "{\"€\":\"Euro Sign\",\"\\r\":\"Carriage Return\",\"1\":\"One\",\"😀\":\"Emoji\",\"\":\"Control\",\"ö\":\"Diaeresis\"}";
        Assert.AreEqual(
            "{\"\\r\":\"Carriage Return\",\"1\":\"One\",\"\":\"Control\",\"ö\":\"Diaeresis\",\"€\":\"Euro Sign\",\"😀\":\"Emoji\"}",
            Canonical(input));
    }

    [TestMethod]
    [DataRow("0000000000000000", "0")]
    [DataRow("0000000000000001", "5e-324")]
    [DataRow("8000000000000001", "-5e-324")]
    [DataRow("7fefffffffffffff", "1.7976931348623157e+308")]
    [DataRow("ffefffffffffffff", "-1.7976931348623157e+308")]
    [DataRow("44b52d02c7e14af5", "9.999999999999997e+22")]
    [DataRow("44b52d02c7e14af6", "1e+23")]
    [DataRow("44b52d02c7e14af7", "1.0000000000000001e+23")]
    [DataRow("444b1ae4d6e2ef50", "1e+21")]
    [DataRow("3eb0c6f7a0b5ed8c", "9.999999999999997e-7")]
    [DataRow("3eb0c6f7a0b5ed8d", "0.000001")]
    [DataRow("41b3de4355555553", "333333333.3333332")]
    [DataRow("41b3de4355555554", "333333333.33333325")]
    [DataRow("41b3de4355555555", "333333333.3333333")]
    [DataRow("41b3de4355555556", "333333333.3333334")]
    [DataRow("41b3de4355555557", "333333333.33333343")]
    [DataRow("becbf647612f3696", "-0.0000033333333333333333")]
    [DataRow("43143ff3c1cb0959", "1424953923781206.2")]
    public void CanonicalizerMatchesOfficialFiniteBinary64Vectors(
        string binary64Hex,
        string expected)
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var value = BitConverter.Int64BitsToDouble(
            Convert.ToInt64(binary64Hex, 16));
        Assert.AreEqual(
            expected,
            Encoding.UTF8.GetString(
                canonicalizer.CanonicalizeNumber(value).ToArray()));
    }

    [TestMethod]
    [DataRow(
        "{\"value\":1,\"value\":2}",
        ProgramKitJsonDiagnosticIds.DuplicateMemberName)]
    [DataRow(
        "{\"a\":1,\"\\u0061\":2}",
        ProgramKitJsonDiagnosticIds.DuplicateMemberName)]
    [DataRow(
        "{\"value\":\"\\udead\"}",
        ProgramKitJsonDiagnosticIds.InvalidUnicode)]
    [DataRow(
        "{\"value\":\"é\"}",
        ProgramKitJsonDiagnosticIds.NonCanonicalUnicode)]
    [DataRow(
        "{\"value\":-0}",
        ProgramKitJsonDiagnosticIds.InvalidNumber)]
    [DataRow(
        "{\"value\":9007199254740992}",
        ProgramKitJsonDiagnosticIds.InvalidNumber)]
    [DataRow(
        "{\"value\":0.123456789012345678901234567890}",
        ProgramKitJsonDiagnosticIds.InvalidNumber)]
    public void StrictCanonicalizerRejectsNonCanonicalInput(
        string input,
        string expectedDiagnostic)
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            canonicalizer.Canonicalize(
                Encoding.UTF8.GetBytes(input),
                JsonSerializationLimits.Default));
        Assert.AreEqual(expectedDiagnostic, exception.Diagnostic.Id);
    }

    [TestMethod]
    public void CanonicalizationIsByteIdempotent()
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var first = canonicalizer.Canonicalize(
            """{"😀":"emoji","\u0080":"control","number":1E30}"""u8,
            JsonSerializationLimits.Default);
        var second = canonicalizer.Canonicalize(
            first.ToArray(),
            JsonSerializationLimits.Default);
        Assert.AreSequenceEqual(first.ToArray(), second.ToArray());
    }

    [TestMethod]
    public void CanonicalizationPreservesLiteralUnicodeEscapeText()
    {
        const string json = "\"\\\\u0041\"";

        Assert.AreEqual(json, Canonical(json));
    }

    [TestMethod]
    public void StrictCanonicalizerRejectsBomInvalidUtf8AndNonFiniteNumbers()
    {
        AssertDiagnostic(
            [0xef, 0xbb, 0xbf, (byte)'{', (byte)'}'],
            ProgramKitJsonDiagnosticIds.InvalidUnicode);
        AssertDiagnostic(
            [0xff],
            ProgramKitJsonDiagnosticIds.InvalidUnicode);
        AssertNumberDiagnostic(double.NaN);
        AssertNumberDiagnostic(double.PositiveInfinity);
        AssertNumberDiagnostic(
            BitConverter.Int64BitsToDouble(
                unchecked((long)0x8000000000000000)));
    }

    [TestMethod]
    public void ExplicitLimitsProduceStableBoundaryDiagnostics()
    {
        AssertDiagnostic(
            "{}"u8.ToArray(),
            ProgramKitJsonDiagnosticIds.ByteLimitExceeded,
            new JsonSerializationLimits(1, 1, 10, 1, 1));
        Assert.AreEqual(
            "{\"a\":1}",
            Canonical(
                "{\"a\":1}",
                new JsonSerializationLimits(64, 1, 10, 1, 16)));
        AssertDiagnostic(
            "{\"a\":[]}"u8.ToArray(),
            ProgramKitJsonDiagnosticIds.DepthLimitExceeded,
            new JsonSerializationLimits(64, 1, 10, 1, 16));
        AssertDiagnostic(
            "[1]"u8.ToArray(),
            ProgramKitJsonDiagnosticIds.TokenLimitExceeded,
            new JsonSerializationLimits(64, 2, 2, 1, 16));
        AssertDiagnostic(
            "{\"a\":1,\"b\":2}"u8.ToArray(),
            ProgramKitJsonDiagnosticIds.MemberLimitExceeded,
            new JsonSerializationLimits(64, 2, 10, 1, 16));
        AssertDiagnostic(
            "{\"a\":\"long\"}"u8.ToArray(),
            ProgramKitJsonDiagnosticIds.MemberBufferLimitExceeded,
            new JsonSerializationLimits(64, 2, 10, 2, 4));
    }

    [TestMethod]
    public void CompleteObjectBufferLimitIncludesEveryCanonicalObjectByte()
    {
        const string json = """{"a":1}""";
        var exactBoundary = new JsonSerializationLimits(
            MaxUtf8Bytes: 64,
            MaxDepth: 2,
            MaxTokens: 10,
            MaxObjectMembers: 1,
            MaxBufferedObjectBytes: 7);
        Assert.AreEqual(json, Canonical(json, exactBoundary));

        var belowBoundary = exactBoundary with
        {
            MaxBufferedObjectBytes = 6,
        };
        AssertDiagnostic(
            Encoding.UTF8.GetBytes(json),
            ProgramKitJsonDiagnosticIds.MemberBufferLimitExceeded,
            belowBoundary);
    }

    private static string Canonical(
        string json,
        JsonSerializationLimits? limits = null)
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        return Encoding.UTF8.GetString(
            canonicalizer.Canonicalize(
                Encoding.UTF8.GetBytes(json),
                limits ?? JsonSerializationLimits.Default).ToArray());
    }

    private static void AssertDiagnostic(
        byte[] utf8,
        string expectedDiagnostic,
        JsonSerializationLimits? limits = null)
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            canonicalizer.Canonicalize(
                utf8,
                limits ?? JsonSerializationLimits.Default));
        Assert.AreEqual(expectedDiagnostic, exception.Diagnostic.Id);
    }

    private static void AssertNumberDiagnostic(double value)
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            canonicalizer.CanonicalizeNumber(value));
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidNumber,
            exception.Diagnostic.Id);
    }
}
