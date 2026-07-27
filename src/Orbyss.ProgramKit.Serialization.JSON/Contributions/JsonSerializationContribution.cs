using System.Collections.Immutable;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

/// <summary>Closed construction boundary for executable JSON contributions.</summary>
public abstract class JsonSerializationContribution :
    IJsonSerializationContribution
{
    internal JsonSerializationContribution()
    {
    }

    /// <inheritdoc />
    public abstract JsonSerializationContributionDescriptor Descriptor { get; }

    /// <inheritdoc />
    public abstract JsonConverter? Converter { get; }

    /// <inheritdoc />
    public abstract IJsonTypeInfoResolver? TypeInfoResolver { get; }

    /// <inheritdoc />
    public abstract ImmutableArray<Type> RuntimeTargetTypes { get; }
}
