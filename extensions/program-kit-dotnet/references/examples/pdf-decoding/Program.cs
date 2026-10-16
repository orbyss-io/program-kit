using System.Text;
using System.Text.Json;
using UglyToad.PdfPig;
using UglyToad.PdfPig.Filters;
using UglyToad.PdfPig.Tokens;
using ProgramKit.Examples.PdfDecoding;

if (args.Length != 1) throw new ArgumentException("Pass the bounded synthetic fixture JSON path.");
using var vectors = JsonDocument.Parse(File.ReadAllBytes(args[0]));
var passed = new List<string>();
var limits = new DecodeLimits(131072, 65536, 262144, 8, TimeSpan.FromSeconds(5));
var dictionary = DictionaryToken.Empty.With(NameToken.Filter, NameToken.FlateDecode);
var malformed = new byte[] { 0x78, 0x01, 0x07, 0, 0, 0, 1 };
byte[] Bytes(string key) => Convert.FromBase64String(vectors.RootElement.GetProperty(key).GetString()!);
var valid = Bytes("dynamic");
var expected = Bytes("expected");
Memory<byte> Decode(byte[] bytes, DecodeBudget? budget = null, DictionaryToken? parameters = null)
{
    budget ??= new DecodeBudget(limits);
    var provider = new BoundedFilterProvider(budget);
    var source = parameters ?? dictionary;
    return provider.GetFilters(source).Single().Decode(bytes, source, provider, 0);
}
void Check(bool condition) { if (!condition) throw new InvalidOperationException("Required assertion failed."); }
void Reject<T>(Action action) where T : Exception
{
    try { action(); } catch (T) { return; }
    throw new InvalidOperationException("Expected " + typeof(T).Name);
}
void Case(string name, Action action) { action(); passed.Add(name); }

Case("public-default-returns-corrupt-input", () => Check(new FlateFilter().Decode(malformed, dictionary, DefaultFilterProvider.Instance, 0).Span.SequenceEqual(malformed)));
foreach (var kind in new[] { "stored", "fixed", "dynamic" })
    Case("valid-"+kind, () => Check(Decode(Bytes(kind)).Span.SequenceEqual(expected)));
Case("malformed-deflate-refused", () => Reject<InvalidDataException>(() => Decode(malformed)));
Case("every-truncated-prefix-refused", () =>
{
    for (var index = 0; index < valid.Length; index++) Reject<InvalidDataException>(() => Decode(valid[..index]));
});
Case("checksum-refused", () => { var corrupt = valid.ToArray(); corrupt[^1] ^= 1; Reject<InvalidDataException>(() => Decode(corrupt)); });
Case("final-block-required-even-with-original-checksum", () =>
{
    var corrupt = Bytes("stored"); corrupt[2] &= 0xfe;
    Reject<InvalidDataException>(() => Decode(corrupt));
});
Case("trailing-and-concatenated-envelope-refused", () =>
{
    foreach (var suffix in new[] { new byte[] { 0 }, new byte[] { 32, 10 }, valid })
        Reject<InvalidDataException>(() => Decode([..valid, ..suffix]));
});
Case("invalid-zlib-header-refused", () =>
{
    var corrupt = valid.ToArray(); corrupt[0] = 0x88; corrupt[1] = 0;
    Reject<InvalidDataException>(() => Decode(corrupt));
});
Case("preset-dictionary-unsupported", () => Reject<NotSupportedException>(() => Decode([0x78, 0x20, 0, 0, 0, 0])));
Case("unqualified-window-unsupported", () => Reject<NotSupportedException>(() => Decode([0x08, 0x1d, 3, 0, 0, 0, 0, 1])));
Case("filter-alias-and-single-array", () =>
{
    foreach (var token in new IToken[] { NameToken.Create("Fl"), new ArrayToken([NameToken.FlateDecode]) })
        Check(Decode(valid, parameters: DictionaryToken.Empty.With(NameToken.Filter, token)).Span.SequenceEqual(expected));
});
Case("codecs-and-chains-unsupported", () =>
{
    foreach (var token in new IToken[] { NameToken.Create("LZWDecode"), NameToken.Create("DCTDecode"), NameToken.Create("ASCIIHexDecode"),
        new ArrayToken([NameToken.FlateDecode, NameToken.FlateDecode]) })
        Reject<NotSupportedException>(() => Decode(valid, parameters: DictionaryToken.Empty.With(NameToken.Filter, token)));
});
Case("predictors-and-parameters-unsupported", () =>
{
    foreach (var parameter in new IToken[] { new NumericToken(2), DictionaryToken.Empty.With(NameToken.Predictor, new NumericToken(12)),
        DictionaryToken.Empty.With(NameToken.Columns, new NumericToken(100)) })
        Reject<NotSupportedException>(() => Decode(valid, parameters: dictionary.With(NameToken.DecodeParms, parameter)));
    Reject<NotSupportedException>(() => Decode(valid, parameters: dictionary.With(NameToken.Filter, new ArrayToken([NameToken.FlateDecode])).With(NameToken.DecodeParms, new ArrayToken([]))));
});
Case("abbreviated-parameter-admission", () =>
{
    var source = DictionaryToken.Empty.With(NameToken.F, NameToken.Create("Fl")).With(NameToken.Dp, DictionaryToken.Empty.With(NameToken.Predictor, new NumericToken(1)));
    Check(Decode(valid, parameters: source).Span.SequenceEqual(expected));
    Reject<NotSupportedException>(() => Decode(valid, parameters: source.With(NameToken.Dp, new NumericToken(3))));
});
Case("encoded-byte-budget", () => Reject<InspectionUnavailableException>(() => Decode(valid, new DecodeBudget(limits with { MaximumEncodedBytes = 1 }))));
Case("decoded-expansion-budget", () => Reject<InspectionUnavailableException>(() => Decode(valid, new DecodeBudget(limits with { MaximumDecodedBytesPerStream = 16 }))));
Case("cumulative-byte-budget", () =>
{
    var budget = new DecodeBudget(limits with { MaximumTotalDecodedBytes = expected.Length });
    Decode(valid, budget); Reject<InspectionUnavailableException>(() => Decode(valid, budget));
});
Case("repeated-decodes-count", () =>
{
    var budget = new DecodeBudget(limits with { MaximumDecodeCalls = 1 });
    Decode(valid, budget); Reject<InspectionUnavailableException>(() => Decode(valid, budget));
});
Case("concurrent-shared-budget-no-overspend", () =>
{
    var budget = new DecodeBudget(limits with { MaximumDecodeCalls = 1 });
    var successes = 0;
    Parallel.For(0, 2, _ => { try { Decode(valid, budget); Interlocked.Increment(ref successes); } catch (InspectionUnavailableException) { } });
    Check(successes <= 1 && budget.Calls == 1 && budget.DecodedBytes <= expected.Length);
    Reject<InspectionUnavailableException>(budget.Checkpoint);
});
Case("failed-operation-stays-incomplete", () =>
{
    var budget = new DecodeBudget(limits);
    Reject<InvalidDataException>(() => Decode(malformed, budget));
    Reject<InspectionUnavailableException>(() => Decode(valid, budget));
});
Case("cooperative-cancellation", () => Reject<OperationCanceledException>(() => Decode(valid, new DecodeBudget(limits, new CancellationToken(true)))));
Case("cooperative-deadline", () =>
{
    var budget = new DecodeBudget(limits with { Timeout = TimeSpan.FromMilliseconds(1) });
    Thread.Sleep(20); Reject<InspectionUnavailableException>(() => Decode(valid, budget));
});
Case("native-pdf-content-filter-seam", () =>
{
    var budget = new DecodeBudget(limits);
    using var document = PdfDocument.Open(PdfFixture.Build(Bytes("content"), true), new ParsingOptions { UseLenientParsing = false, FilterProvider = new BoundedFilterProvider(budget) });
    Check(document.GetPage(1).Operations.Count > 0 && budget.Calls >= 1);
});
Case("native-pdf-malformed-content-refused", () => Reject<InvalidDataException>(() =>
{
    using var document = PdfDocument.Open(PdfFixture.Build(malformed, true), new ParsingOptions { UseLenientParsing = false, FilterProvider = new BoundedFilterProvider(new DecodeBudget(limits)) });
    document.GetPage(1);
}));
Case("deferred-image-needs-explicit-work", () =>
{
    var budget = new DecodeBudget(limits);
    using var document = PdfDocument.Open(PdfFixture.Build(Encoding.ASCII.GetBytes("q 2 0 0 2 0 0 cm /Im0 Do Q"), false, Bytes("image")), new ParsingOptions { UseLenientParsing = false, FilterProvider = new BoundedFilterProvider(budget) });
    var image = document.GetPage(1).GetImages().Single();
    Check(budget.Calls == 0);
    Check(image.TryGetBytesAsMemory(out var decoded) && decoded.Span.SequenceEqual(new byte[] { 0, 1, 2, 3 }) && budget.Calls == 1);
});
Case("deferred-malformed-image-refused", () =>
{
    var budget = new DecodeBudget(limits);
    using var document = PdfDocument.Open(PdfFixture.Build(Encoding.ASCII.GetBytes("/Im0 Do"), false, malformed), new ParsingOptions { UseLenientParsing = false, FilterProvider = new BoundedFilterProvider(budget) });
    var image = document.GetPage(1).GetImages().Single();
    Check(budget.Calls == 0);
    Reject<InvalidDataException>(() => image.TryGetBytesAsMemory(out _));
});
Case("unreachable-stream-is-outside-traversal", () =>
{
    var budget = new DecodeBudget(limits);
    using var document = PdfDocument.Open(PdfFixture.Build(Encoding.ASCII.GetBytes("0 0 m 1 1 l S"), false, unreachable: malformed), new ParsingOptions { UseLenientParsing = false, FilterProvider = new BoundedFilterProvider(budget) });
    Check(document.GetPage(1).Operations.Count > 0 && budget.Calls == 0);
});
Console.WriteLine(JsonSerializer.Serialize(new { status = "passed", cases = passed, executedCases = passed.Count,
    scope = "Synthetic Flate provider and explicit content/image work only; no general PDF, process isolation or product acceptance", processMemoryLimitQualified = false, paidDispatch = false }));
