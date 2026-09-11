using Microsoft.OpenApi;
using Orbyss.Foundation.Web.OpenApi;
using Orbyss.Foundation.Web.ProblemDetails;
using Orbyss.Foundation.WebDefaults;

namespace InternalForms.Api;

public static class ApiProbe
{
    public static readonly Type[] SelectedTypes =
    [
        typeof(FoundationWebDefaultsFeature),
        typeof(FoundationProblemDetailsFeature),
        typeof(FoundationOpenApiFeature),
        typeof(OpenApiSpecVersion),
    ];
}
