using System.Buffers;
using System.Globalization;
using System.Numerics;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Canonicalization;

/// <summary>
/// Strict RFC 8785-subset canonicalization with no mutable JSON document model.
/// </summary>
/// <remarks>
/// Inputs whose canonical rendering would be a bare integer outside the
/// interoperable safe-integer range are rejected. Canonical exponent forms retain
/// RFC 8785 binary64 behavior (including <c>1E30</c>); stronger exact-integer
/// meaning belongs to the selected schema and typed model validator because it
/// cannot be inferred from JSON syntax.
/// </remarks>
public sealed class ProgramKitJsonCanonicalizer : IProgramKitJsonCanonicalizer
{
    private const long MaximumSafeInteger = 9_007_199_254_740_991L;
    private static readonly UTF8Encoding StrictUtf8 = new(
        encoderShouldEmitUTF8Identifier: false,
        throwOnInvalidBytes: true);

    /// <summary>Validates and canonicalizes one complete UTF-8 JSON value.</summary>
    /// <param name="utf8Json">UTF-8 JSON without a byte-order mark.</param>
    /// <param name="limits">Explicit operation and member-buffer limits.</param>
    public CanonicalJsonValue Canonicalize(
        ReadOnlySpan<byte> utf8Json,
        JsonSerializationLimits limits)
    {
        ArgumentNullException.ThrowIfNull(limits);
        limits.EnsureValid();
        if (utf8Json.Length > limits.MaxUtf8Bytes)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.ByteLimitExceeded,
                "The JSON input exceeds the configured UTF-8 byte limit.");
        }

        if (utf8Json.Length >= 3 &&
            utf8Json[0] == 0xef &&
            utf8Json[1] == 0xbb &&
            utf8Json[2] == 0xbf)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidUnicode,
                "UTF-8 JSON must not contain a byte-order mark.");
        }

        try
        {
            _ = StrictUtf8.GetCharCount(utf8Json);
        }
        catch (DecoderFallbackException exception)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidUnicode,
                "The JSON input contains invalid UTF-8.",
                exception);
        }

        try
        {
            var reader = new Utf8JsonReader(
                utf8Json,
                new JsonReaderOptions
                {
                    AllowTrailingCommas = false,
                    CommentHandling = JsonCommentHandling.Disallow,
                    MaxDepth = limits.MaxDepth + 1,
                });
            var state = new CanonicalizationState(limits);
            if (!ReadNext(ref reader, ref state))
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.InvalidJson,
                    "The JSON input is empty.");
            }

            var canonical = ReadCurrentValue(ref reader, ref state, depth: 0);
            if (ReadNext(ref reader, ref state))
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.InvalidJson,
                    "The input contains more than one JSON value.");
            }

            if (canonical.Length > limits.MaxUtf8Bytes)
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.ByteLimitExceeded,
                    "The canonical JSON exceeds the configured UTF-8 byte limit.");
            }

            return new CanonicalJsonValue(canonical);
        }
        catch (ProgramKitJsonException)
        {
            throw;
        }
        catch (JsonException exception)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidJson,
                "The input is not valid strict JSON.",
                exception);
        }
        catch (OverflowException exception)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.MemberBufferLimitExceeded,
                "A JSON object exceeded the bounded member buffer.",
                exception);
        }
    }

    /// <summary>Canonicalizes one finite binary64 value under the strict profile.</summary>
    public CanonicalJsonValue CanonicalizeNumber(double value)
    {
        EnsureFiniteAndNotNegativeZero(value);
        return new CanonicalJsonValue(
            Encoding.UTF8.GetBytes(FormatStrictNumber(value)));
    }

    private static byte[] ReadCurrentValue(
        ref Utf8JsonReader reader,
        ref CanonicalizationState state,
        int depth)
    {
        return reader.TokenType switch
        {
            JsonTokenType.StartObject => ReadObject(ref reader, ref state, depth + 1),
            JsonTokenType.StartArray => ReadArray(ref reader, ref state, depth + 1),
            JsonTokenType.String => EncodeString(ReadValidatedString(ref reader)),
            JsonTokenType.Number => CanonicalizeNumberToken(ref reader),
            JsonTokenType.True => "true"u8.ToArray(),
            JsonTokenType.False => "false"u8.ToArray(),
            JsonTokenType.Null => "null"u8.ToArray(),
            _ => throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidJson,
                $"Unexpected JSON token '{reader.TokenType}'."),
        };
    }

    private static byte[] ReadObject(
        ref Utf8JsonReader reader,
        ref CanonicalizationState state,
        int depth)
    {
        EnsureDepth(depth, state.Limits);
        var names = new HashSet<string>(StringComparer.Ordinal);
        var members = new List<CanonicalJsonMember>();
        long bufferedBytes = 2;
        if (bufferedBytes > state.Limits.MaxBufferedObjectBytes)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.MemberBufferLimitExceeded,
                "An object exceeds the configured complete-object buffer limit.");
        }

        while (ReadNext(ref reader, ref state))
        {
            if (reader.TokenType == JsonTokenType.EndObject)
            {
                break;
            }

            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.InvalidJson,
                    "An object member name was expected.");
            }

            var name = ReadValidatedString(ref reader);
            if (!names.Add(name))
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.DuplicateMemberName,
                    $"Object member '{name}' occurs more than once.");
            }

            if (names.Count > state.Limits.MaxObjectMembers)
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.MemberLimitExceeded,
                    "An object exceeds the configured member limit.");
            }

            if (!ReadNext(ref reader, ref state))
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.InvalidJson,
                    "An object member has no value.");
            }

            var encodedName = EncodeString(name);
            var encodedValue = ReadCurrentValue(ref reader, ref state, depth);
            bufferedBytes = checked(
                bufferedBytes +
                encodedName.Length +
                encodedValue.Length +
                1 +
                (members.Count == 0 ? 0 : 1));
            if (bufferedBytes > state.Limits.MaxBufferedObjectBytes)
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.MemberBufferLimitExceeded,
                    "An object exceeds the configured bounded member-buffer limit.");
            }

            members.Add(new CanonicalJsonMember(name, encodedName, encodedValue));
        }

        if (reader.TokenType != JsonTokenType.EndObject)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidJson,
                "An object is not terminated.");
        }

        members.Sort(static (left, right) =>
            string.CompareOrdinal(left.Name, right.Name));
        var output = new ArrayBufferWriter<byte>();
        WriteByte(output, (byte)'{');
        for (var index = 0; index < members.Count; index++)
        {
            if (index > 0)
            {
                WriteByte(output, (byte)',');
            }

            output.Write(members[index].EncodedName);
            WriteByte(output, (byte)':');
            output.Write(members[index].EncodedValue);
        }

        WriteByte(output, (byte)'}');
        return output.WrittenSpan.ToArray();
    }

    private static byte[] ReadArray(
        ref Utf8JsonReader reader,
        ref CanonicalizationState state,
        int depth)
    {
        EnsureDepth(depth, state.Limits);
        var output = new ArrayBufferWriter<byte>();
        WriteByte(output, (byte)'[');
        var first = true;
        while (ReadNext(ref reader, ref state))
        {
            if (reader.TokenType == JsonTokenType.EndArray)
            {
                WriteByte(output, (byte)']');
                return output.WrittenSpan.ToArray();
            }

            if (!first)
            {
                WriteByte(output, (byte)',');
            }

            output.Write(ReadCurrentValue(ref reader, ref state, depth));
            if (output.WrittenCount > state.Limits.MaxUtf8Bytes)
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.ByteLimitExceeded,
                    "A canonical JSON array exceeds the configured byte limit.");
            }

            first = false;
        }

        throw Failure(
            ProgramKitJsonDiagnosticIds.InvalidJson,
            "An array is not terminated.");
    }

    private static string ReadValidatedString(ref Utf8JsonReader reader)
    {
        string value;
        try
        {
            value = reader.GetString()
                ?? throw new JsonException("A JSON string cannot be null.");
        }
        catch (Exception exception)
            when (exception is JsonException or ArgumentException or InvalidOperationException)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidUnicode,
                "A JSON string contains an invalid Unicode scalar sequence.",
                exception);
        }

        var remaining = value.AsSpan();
        while (!remaining.IsEmpty)
        {
            if (Rune.DecodeFromUtf16(
                    remaining,
                    out _,
                    out var consumed) != OperationStatus.Done)
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.InvalidUnicode,
                    "A JSON string contains an invalid Unicode scalar sequence.");
            }

            remaining = remaining[consumed..];
        }

        if (!value.IsNormalized(NormalizationForm.FormC))
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.NonCanonicalUnicode,
                "JSON strings must already use Unicode Normalization Form C.");
        }

        return value;
    }

    private static byte[] CanonicalizeNumberToken(ref Utf8JsonReader reader)
    {
        var raw = reader.HasValueSequence
            ? reader.ValueSequence.ToArray()
            : reader.ValueSpan.ToArray();
        var text = Encoding.UTF8.GetString(raw);
        if (!reader.TryGetDouble(out var value))
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidNumber,
                "A JSON number must be representable as finite IEEE 754 binary64.");
        }

        EnsureFiniteAndNotNegativeZero(value);
        if (CountSignificantDigits(text) > 17)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidNumber,
                "JSON numbers requiring more than binary64 decimal precision must be modeled as schema-constrained strings.");
        }

        return Encoding.UTF8.GetBytes(FormatStrictNumber(value));
    }

    private static void EnsureFiniteAndNotNegativeZero(double value)
    {
        if (!double.IsFinite(value))
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidNumber,
                "Non-finite JSON numbers are forbidden.");
        }

        if (value == 0d && BitConverter.DoubleToInt64Bits(value) < 0)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidNumber,
                "Negative zero is forbidden by the Program Kit strict JCS profile.");
        }
    }

    private static int CountSignificantDigits(string text)
    {
        var exponentIndex = text.IndexOfAny(['e', 'E']);
        var mantissa = exponentIndex < 0 ? text : text[..exponentIndex];
        var digits = mantissa
            .Where(static character => character is >= '0' and <= '9')
            .SkipWhile(static character => character == '0')
            .ToArray();
        var length = digits.Length;
        while (length > 0 && digits[length - 1] == '0')
        {
            length--;
        }

        return Math.Max(length, 1);
    }

    private static string FormatEcmaNumber(double value)
    {
        if (value == 0d)
        {
            return "0";
        }

        var roundTrip = value.ToString("R", CultureInfo.InvariantCulture);
        var negative = roundTrip[0] == '-';
        var unsigned = negative ? roundTrip[1..] : roundTrip;
        var exponentIndex = unsigned.IndexOfAny(['E', 'e']);
        var mantissa = exponentIndex < 0 ? unsigned : unsigned[..exponentIndex];
        var exponent = exponentIndex < 0
            ? 0
            : int.Parse(
                unsigned[(exponentIndex + 1)..],
                NumberStyles.AllowLeadingSign,
                CultureInfo.InvariantCulture);
        var decimalPoint = mantissa.IndexOf('.');
        if (decimalPoint < 0)
        {
            decimalPoint = mantissa.Length;
        }

        var rawDigits = mantissa.Replace(".", string.Empty, StringComparison.Ordinal);
        var leadingZeros = rawDigits.TakeWhile(static character => character == '0').Count();
        var digits = rawDigits[leadingZeros..].TrimEnd('0');
        var n = decimalPoint + exponent - leadingZeros;
        var k = digits.Length;

        string formatted;
        if (k <= n && n <= 21)
        {
            formatted = string.Concat(digits, new string('0', n - k));
        }
        else if (0 < n && n <= 21)
        {
            formatted = string.Concat(digits.AsSpan(0, n), ".", digits.AsSpan(n));
        }
        else if (-6 < n && n <= 0)
        {
            formatted = string.Concat("0.", new string('0', -n), digits);
        }
        else
        {
            var exponentValue = n - 1;
            var significand = k == 1
                ? digits
                : string.Concat(digits.AsSpan(0, 1), ".", digits.AsSpan(1));
            formatted = string.Concat(
                significand,
                "e",
                exponentValue >= 0 ? "+" : string.Empty,
                exponentValue.ToString(CultureInfo.InvariantCulture));
        }

        return negative ? string.Concat("-", formatted) : formatted;
    }

    private static string FormatStrictNumber(double value)
    {
        var formatted = FormatEcmaNumber(value);
        if (!formatted.Contains('.', StringComparison.Ordinal) &&
            !formatted.Contains('e', StringComparison.Ordinal) &&
            BigInteger.TryParse(
                formatted,
                NumberStyles.AllowLeadingSign,
                CultureInfo.InvariantCulture,
                out var integer) &&
            BigInteger.Abs(integer) > MaximumSafeInteger)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.InvalidNumber,
                "A canonical bare integer must remain inside the interoperable safe-integer range; use a schema-constrained string for larger exact integers.");
        }

        return formatted;
    }

    private static byte[] EncodeString(string value)
    {
        var output = new ArrayBufferWriter<byte>();
        using (var writer = new Utf8JsonWriter(
                   output,
                   new JsonWriterOptions
                   {
                       Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
                       Indented = false,
                       SkipValidation = false,
                   }))
        {
            writer.WriteStringValue(value);
            writer.Flush();
        }

        var writerBytes = output.WrittenSpan;
        var canonical = new ArrayBufferWriter<byte>(writerBytes.Length);
        Span<byte> encodedRune = stackalloc byte[4];
        for (var index = 0; index < writerBytes.Length; index++)
        {
            if (index + 1 < writerBytes.Length &&
                writerBytes[index] == (byte)'\\' &&
                writerBytes[index + 1] == (byte)'\\')
            {
                canonical.Write(writerBytes.Slice(index, 2));
                index++;
                continue;
            }

            if (!TryReadUnicodeEscape(
                    writerBytes,
                    index,
                    out var codeUnit))
            {
                WriteByte(canonical, writerBytes[index]);
                continue;
            }

            if (codeUnit <= 0x1f)
            {
                canonical.Write("\\u"u8);
                for (var hexIndex = index + 2; hexIndex < index + 6; hexIndex++)
                {
                    var hexByte = writerBytes[hexIndex];
                    WriteByte(
                        canonical,
                        hexByte is >= (byte)'A' and <= (byte)'F'
                            ? (byte)(hexByte + 32)
                            : hexByte);
                }

                index += 5;
                continue;
            }

            Rune rune;
            if (char.IsHighSurrogate((char)codeUnit) &&
                TryReadUnicodeEscape(
                    writerBytes,
                    index + 6,
                    out var lowSurrogate) &&
                char.IsLowSurrogate((char)lowSurrogate))
            {
                rune = new Rune((char)codeUnit, (char)lowSurrogate);
                index += 11;
            }
            else if (Rune.TryCreate((char)codeUnit, out rune))
            {
                index += 5;
            }
            else
            {
                throw Failure(
                    ProgramKitJsonDiagnosticIds.InvalidUnicode,
                    "The JSON writer produced an invalid Unicode escape.");
            }

            var encodedLength = rune.EncodeToUtf8(encodedRune);
            canonical.Write(encodedRune[..encodedLength]);
        }

        return canonical.WrittenSpan.ToArray();
    }

    private static bool TryReadUnicodeEscape(
        ReadOnlySpan<byte> bytes,
        int index,
        out ushort codeUnit)
    {
        codeUnit = 0;
        if (index < 0 ||
            index + 5 >= bytes.Length ||
            bytes[index] != (byte)'\\' ||
            bytes[index + 1] != (byte)'u')
        {
            return false;
        }

        for (var offset = 2; offset < 6; offset++)
        {
            var value = HexValue(bytes[index + offset]);
            if (value < 0)
            {
                return false;
            }

            codeUnit = (ushort)((codeUnit << 4) | value);
        }

        return true;
    }

    private static int HexValue(byte value) =>
        value switch
        {
            >= (byte)'0' and <= (byte)'9' => value - (byte)'0',
            >= (byte)'a' and <= (byte)'f' => value - (byte)'a' + 10,
            >= (byte)'A' and <= (byte)'F' => value - (byte)'A' + 10,
            _ => -1,
        };

    private static bool ReadNext(
        ref Utf8JsonReader reader,
        ref CanonicalizationState state)
    {
        var result = reader.Read();
        if (!result)
        {
            return false;
        }

        state.TokenCount++;
        if (state.TokenCount > state.Limits.MaxTokens)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.TokenLimitExceeded,
                "The JSON input exceeds the configured token limit.");
        }

        return true;
    }

    private static void EnsureDepth(int depth, JsonSerializationLimits limits)
    {
        if (depth > limits.MaxDepth)
        {
            throw Failure(
                ProgramKitJsonDiagnosticIds.DepthLimitExceeded,
                "The JSON input exceeds the configured nesting-depth limit.");
        }
    }

    private static void WriteByte(ArrayBufferWriter<byte> output, byte value)
    {
        var span = output.GetSpan(1);
        span[0] = value;
        output.Advance(1);
    }

    private static ProgramKitJsonException Failure(
        string id,
        string message,
        Exception? innerException = null) =>
        ProgramKitJsonException.Create(id, message, innerException: innerException);

}
