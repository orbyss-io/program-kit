using Orbyss.Foundation.Collections.Core;

namespace PublishedTools.Contract.Core;

/// <summary>Contract-only collection value; this assembly is never an activated feature.</summary>
public sealed record SampleSnapshot(ValueSequence<string> Values);
