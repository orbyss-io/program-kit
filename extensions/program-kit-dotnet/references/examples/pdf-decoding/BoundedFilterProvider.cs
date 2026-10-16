using UglyToad.PdfPig.Filters;
using UglyToad.PdfPig.Tokens;

namespace ProgramKit.Examples.PdfDecoding;

public sealed class BoundedFilterProvider(DecodeBudget budget) : IFilterProvider
{
    private readonly IFilter flate = new BoundedFlateFilter(budget);

    public IReadOnlyList<IFilter> GetFilters(DictionaryToken dictionary)
    {
        try
        {
            budget.Checkpoint();
            var hasFull = dictionary.TryGet(NameToken.Filter, out var full);
            var hasShort = dictionary.TryGet(NameToken.F, out var abbreviation);
            if (hasFull && hasShort) throw new NotSupportedException("Ambiguous full/abbreviated filter keys are outside this example.");
            var token = hasFull ? full : abbreviation;
            return token switch
            {
                null => Array.Empty<IFilter>(),
                NameToken name => GetNamedFilters([name]),
                ArrayToken array when array.Data.All(item => item is NameToken) => GetNamedFilters(array.Data.Cast<NameToken>().ToArray()),
                _ => throw new NotSupportedException("Indirect or unknown filter declaration is outside this example.")
            };
        }
        catch { budget.Fail(); throw; }
    }

    public IReadOnlyList<IFilter> GetNamedFilters(IReadOnlyList<NameToken> names)
    {
        try
        {
            budget.Checkpoint();
            if (names.Count != 1 || names[0].Data is not ("FlateDecode" or "Fl"))
                throw new NotSupportedException("This example qualifies a single FlateDecode/Fl stage; other codecs/chains are unsupported.");
            return [flate];
        }
        catch { budget.Fail(); throw; }
    }

    public IReadOnlyList<IFilter> GetAllFilters() => [flate];
}
