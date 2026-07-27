using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Authentication;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<GeneratedPublicBrowser.App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");
builder.Services.AddOidcAuthentication(options =>
{
    options.ProviderOptions.Authority = "https://identity.example.test/";
    options.ProviderOptions.ClientId = "sample-public-browser";
    options.ProviderOptions.ResponseType = "code";
    options.ProviderOptions.RedirectUri =
        "https://browser.example.test/authentication/login-callback";
    options.ProviderOptions.PostLogoutRedirectUri =
        "https://browser.example.test/authentication/logout-callback";
    options.ProviderOptions.DefaultScopes.Clear();
    options.ProviderOptions.DefaultScopes.Add("openid");
    options.ProviderOptions.DefaultScopes.Add("profile");
    options.ProviderOptions.DefaultScopes.Add("sample-api.read");
});
builder.Services.AddScoped(sp =>
{
    var authorization = new AuthorizationMessageHandler(
        sp.GetRequiredService<IAccessTokenProvider>(),
        sp.GetRequiredService<NavigationManager>())
        .ConfigureHandler(
            ["https://api.example.test"],
            ["sample-api.read"]);
    authorization.InnerHandler = new HttpClientHandler();
    return new HttpClient(authorization)
    {
        BaseAddress = new Uri("https://api.example.test/"),
    };
});
await builder.Build().RunAsync();
