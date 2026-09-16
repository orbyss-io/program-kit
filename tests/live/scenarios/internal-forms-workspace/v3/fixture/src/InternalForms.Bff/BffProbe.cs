using Orbyss.Foundation.Authentication;
using Orbyss.Foundation.Authentication.BffCookie;
using Orbyss.Foundation.WebDefaults;

namespace InternalForms.Bff;

public static class BffProbe
{
    public static readonly Type[] SelectedTypes =
    [
        typeof(FoundationAuthenticationFeature),
        typeof(FoundationBffCookieFeature),
        typeof(FoundationWebDefaultsFeature),
    ];
}
