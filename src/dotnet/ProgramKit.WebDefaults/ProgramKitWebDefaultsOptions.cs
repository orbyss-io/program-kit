namespace ProgramKit.WebDefaults;

/// <summary>Defines the localizations enabled by the default Program Kit web middleware.</summary>
internal sealed class ProgramKitWebDefaultsOptions
{
    /// <summary>Gets or sets the deterministic application fallback locale.</summary>
    public string DefaultLocale { get; set; } = "en";

    /// <summary>Gets or sets the application locales accepted by request localization.</summary>
    public string[] SupportedLocales { get; set; } = ["en"];
}
