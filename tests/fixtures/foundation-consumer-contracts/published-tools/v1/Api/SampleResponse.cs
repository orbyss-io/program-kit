using Orbyss.Foundation.Collections.Core;

namespace PublishedTools.Contract.Api;

/// <summary>Operation-owned wire projection retaining the admitted array shape.</summary>
public sealed record SampleResponse(ValueSequence<string> Values);
