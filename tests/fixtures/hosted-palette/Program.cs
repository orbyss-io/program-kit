using Orbyss.Foundation.Web.HostedPages;

var output = args[0];
Directory.CreateDirectory(output);
foreach (var theme in new[] { "blue", "green", "slate" })
{
    var definition = new HostedPageRevision {
        Id = "palette-1", FormReleaseId = "fixture-1", DefaultLocale = "en", Theme = theme,
        Entry = "src/app.ts", Assets = [],
        Locales = new() { ["en"] = new() {
            Title = "Palette fixture", Purpose = "Selected Foundation hosted envelope",
            LogoAlt = "", LoadingText = "Loading application", FailureText = "Application unavailable",
            NoScriptText = "Enable JavaScript to use this application." } },
        Vite = new() { ["src/app.ts"] = new() { File = "runtime.js", IsEntry = true, Css = ["runtime.css"] } }
    };
    var revision = new AdmittedHostedRevision(definition, theme, new Dictionary<string, (HostedAssetDescriptor, byte[])>(), ["runtime.css"], null);
    var admission = new HostedPageAdmission(false, null, null);
    var route = new AdmittedHostedPageRoute(null, "/", definition.Id, admission, admission);
    File.WriteAllText(Path.Combine(output, theme + ".html"), HostedPageRendering.Page(revision, "en", path => path, route));
    File.WriteAllBytes(Path.Combine(output, theme + ".json"), HostedPageRendering.Bootstrap(revision, "en", path => path));
}
File.WriteAllText(Path.Combine(output, "foundation.css"), HostedPageRendering.Styles);
File.WriteAllText(Path.Combine(output, "loader.js"), HostedPageRendering.Loader);
