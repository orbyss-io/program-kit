using System.Collections.Immutable;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

/// <summary>
/// Supplies one explicitly selected converter or source-generated metadata
/// context together with its immutable descriptor.
/// </summary>
public interface IJsonSerializationContribution
{
    /// <summary>Gets the independently versioned contribution descriptor.</summary>
    JsonSerializationContributionDescriptor Descriptor { get; }

    /// <summary>Gets the converter, when this is a converter contribution.</summary>
    JsonConverter? Converter { get; }

    /// <summary>Gets the source-generated context, when this is metadata.</summary>
    IJsonTypeInfoResolver? TypeInfoResolver { get; }

    /// <summary>Gets exact closed runtime types or open generic factory definitions.</summary>
    ImmutableArray<Type> RuntimeTargetTypes { get; }
}
