using Microsoft.Extensions.Options;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Validates the API owner's configured prefix through the native Options contract.</summary>
internal sealed class LabelApiOptionsValidator : IValidateOptions<LabelApiOptions>
{
    /// <inheritdoc />
    public ValidateOptionsResult Validate(string? name, LabelApiOptions options)
    {
        if (options.Prefix is { Length: > 0 and <= 32 })
            return ValidateOptionsResult.Success;

        return ValidateOptionsResult.Fail("Sample:Api:Prefix is required and must contain at most 32 characters.");
    }
}
