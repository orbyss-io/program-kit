using ICSharpCode.SharpZipLib;
using ICSharpCode.SharpZipLib.Zip.Compression;
using UglyToad.PdfPig.Filters;
using UglyToad.PdfPig.Tokens;

namespace ProgramKit.Examples.PdfDecoding;

public sealed class BoundedFlateFilter(DecodeBudget budget) : IFilter
{
    public bool IsSupported => true;

    public Memory<byte> Decode(Memory<byte> input, DictionaryToken dictionary, IFilterProvider provider, int filterIndex)
    {
        try
        {
            budget.Begin(input.Length);
            if (filterIndex != 0) throw new NotSupportedException("This example admits one Flate stage only.");
            var hasFull = dictionary.TryGet(NameToken.DecodeParms, out var fullParameters);
            var hasShort = dictionary.TryGet(NameToken.Dp, out var shortParameters);
            if (hasFull && hasShort) throw new NotSupportedException("Ambiguous decode parameter keys are outside this example.");
            var parameterToken = hasFull ? fullParameters : shortParameters;
            var fullFilter = dictionary.TryGet(NameToken.Filter, out var filterToken);
            var shortFilter = dictionary.TryGet(NameToken.F, out var shortFilterToken);
            if (fullFilter && shortFilter) throw new NotSupportedException("Ambiguous filter keys are outside this example.");
            filterToken = fullFilter ? filterToken : shortFilterToken;
            var named = filterToken is NameToken name ? name :
                filterToken is ArrayToken { Data.Count: 1 } array ? array.Data[0] as NameToken : null;
            if (named?.Data is not ("FlateDecode" or "Fl"))
                throw new NotSupportedException("Unqualified filter declaration or indirect filter lookup.");
            if (parameterToken is not null and not NullToken &&
                (filterToken is NameToken && parameterToken is not DictionaryToken ||
                 filterToken is ArrayToken && parameterToken is not ArrayToken))
                throw new NotSupportedException("Unqualified decode parameter declaration.");
            if (parameterToken is ArrayToken parameterArray &&
                (parameterArray.Data.Count != 1 || parameterArray.Data[0] is not (DictionaryToken or NullToken)))
                throw new NotSupportedException("Unqualified decode parameter array.");
            var parameters = DecodeParameterResolver.GetFilterParameters(dictionary, filterIndex);
            foreach (var pair in parameters.Data)
                if (pair.Key != "Predictor" || pair.Value is not NumericToken number || number.Data != 1)
                    throw new NotSupportedException("This example does not qualify predictors or other decode parameters.");
            var bytes = input.Span;
            if (bytes.Length < 6 || (bytes[0] & 15) != 8 || (bytes[0] >> 4) > 7 || ((bytes[0] << 8) | bytes[1]) % 31 != 0)
                throw new InvalidDataException("Invalid RFC1950 header/envelope.");
            if ((bytes[1] & 32) != 0) throw new NotSupportedException("Preset dictionaries are outside this example.");
            if (bytes[0] != 0x78) throw new NotSupportedException("This example qualifies the declared 32 KiB zlib window only.");

            // A decoder exposing completion and remaining input avoids treating
            // stream EOF or a manually checked trailer as proof of completion.
            var inflater = new Inflater(noHeader: false);
            inflater.SetInput(input.ToArray());
            using var output = new MemoryStream();
            var buffer = new byte[Math.Min(4096, budget.Limits.MaximumDecodedBytesPerStream)];
            while (!inflater.IsFinished)
            {
                budget.Checkpoint();
                var count = inflater.Inflate(buffer);
                budget.Checkpoint();
                if (count > 0)
                {
                    budget.Charge(output.Length + count, count);
                    output.Write(buffer, 0, count);
                }
                else if (!inflater.IsFinished)
                {
                    if (inflater.IsNeedingDictionary) throw new NotSupportedException("Preset dictionary is unavailable.");
                    throw new InvalidDataException("Truncated or stalled Flate stream.");
                }
            }
            if (inflater.RemainingInput != 0 || inflater.TotalIn != input.Length)
                throw new InvalidDataException("Trailing or concatenated compressed envelope is outside this example.");
            budget.Checkpoint();
            return output.ToArray();
        }
        catch (SharpZipBaseException error)
        {
            budget.Fail();
            throw new InvalidDataException("Malformed Flate data or checksum.", error);
        }
        catch (FormatException error)
        {
            budget.Fail();
            throw new InvalidDataException("Malformed Flate data.", error);
        }
        catch
        {
            budget.Fail();
            throw;
        }
    }
}
