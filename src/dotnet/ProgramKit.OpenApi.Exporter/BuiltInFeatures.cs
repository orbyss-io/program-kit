namespace ProgramKit.OpenApiExport;

/// <summary>Defines the platform feature identities supplied by Program Kit runtime packages.</summary>
internal static class BuiltInFeatures
{
    /// <summary>Maps exact feature identities to their package and composition metadata.</summary>
    public static readonly IReadOnlyDictionary<string, BuiltInFeatureDefinition> Definitions =
        new Dictionary<string, BuiltInFeatureDefinition>(StringComparer.Ordinal)
        {
            ["ProgramKit.Authentication"] =
                new("ProgramKit.Authentication", [], [], false),
            ["ProgramKit.Authentication.BffCookie"] =
                new(
                    "ProgramKit.Authentication.BffCookie",
                    ["ProgramKit.Authentication", "ProgramKit.WebDefaults"],
                    ["/bff/login", "/bff/user", "/bff/antiforgery", "/bff/logout", "/bff/signed-out"],
                    false),
            ["ProgramKit.Authentication.SpaPkce"] =
                new(
                    "ProgramKit.Authentication.SpaPkce",
                    ["ProgramKit.Authentication", "ProgramKit.WebDefaults"],
                    [],
                    false),
            ["ProgramKit.DomainEvents"] =
                new("ProgramKit.DomainEvents", [], [], false),
            ["ProgramKitTasks"] =
                new("ProgramKit.Tasks", [], [], false),
            ["ProgramKit.WebDefaults"] =
                new("ProgramKit.WebDefaults", [], [], false),
            ["ProgramKit.Web.OpenApi"] =
                new("ProgramKit.Web.OpenApi", [], ["/_program-kit/openapi/{documentName}.json"], true),
            ["ProgramKit.Web.ProblemDetails"] =
                new("ProgramKit.Web.ProblemDetails", [], [], false),
        };
}
