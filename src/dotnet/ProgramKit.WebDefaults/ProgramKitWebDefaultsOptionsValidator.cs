using Microsoft.Extensions.Options;

namespace ProgramKit.WebDefaults;

/// <summary>Rejects an incomplete or invalid locale set.</summary>
internal sealed class ProgramKitWebDefaultsOptionsValidator : IValidateOptions<ProgramKitWebDefaultsOptions>
{
    /// <inheritdoc />
    public ValidateOptionsResult Validate(string? name, ProgramKitWebDefaultsOptions options)
    {
        var failures = new List<string>();
        if (options.SupportedLocales.Length == 0
            || !options.SupportedLocales.Contains(options.DefaultLocale, StringComparer.OrdinalIgnoreCase))
        {
            failures.Add("ProgramKit:Web:SupportedLocales must contain ProgramKit:Web:DefaultLocale.");
        }

        foreach (var locale in options.SupportedLocales)
        {
            try
            {
                _ = System.Globalization.CultureInfo.GetCultureInfo(locale);
            }
            catch (System.Globalization.CultureNotFoundException)
            {
                failures.Add($"ProgramKit:Web:SupportedLocales contains an unknown locale: {locale}");
            }
        }

        return failures.Count == 0 ? ValidateOptionsResult.Success : ValidateOptionsResult.Fail(failures);
    }
}
