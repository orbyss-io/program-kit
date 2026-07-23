namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

/// <summary>The explicit runtime contribution forms supported by Serialization.JSON.</summary>
public enum JsonSerializationContributionKind
{
    /// <summary>One typed converter.</summary>
    TypedConverter,

    /// <summary>One converter factory with declared target families.</summary>
    ConverterFactory,

    /// <summary>One source-generated context.</summary>
    TypeInfoResolver,
}
