using System.Diagnostics;
using System.Xml.Linq;

namespace ProgramKit.Foundation.TestSupport;

/// <summary>Executable runner adapter shared by disposable integration suites.
/// xUnit/MTP callers retain their own native discovery and reports.</summary>
public static class CaseSuite
{
    /// <summary>Execute selected real cases and retain named native JUnit evidence.
    /// Empty selections, duplicate names, missing cases and failures return nonzero.</summary>
    public static async Task<int> RunAsync(IEnumerable<IntegrationCase> cases, string reportPath,
        IReadOnlySet<string>? selected = null, CancellationToken cancellationToken = default)
    {
        var all = cases.ToArray();
        if (all.Length == 0 || all.Any(test => string.IsNullOrWhiteSpace(test.Name)) ||
            all.Select(test => test.Name).Distinct(StringComparer.Ordinal).Count() != all.Length ||
            selected is { Count: 0 } || selected is not null && selected.Except(all.Select(test => test.Name)).Any())
            throw new InvalidOperationException("Integration selection must contain actual unique case identities.");
        var suite = new XElement("testsuite", new XAttribute("name", "ProgramKitFoundationIntegration"));
        var failed = false;
        try
        {
            foreach (var test in all.Where(test => selected is null || selected.Contains(test.Name)))
            {
                cancellationToken.ThrowIfCancellationRequested();
                var clock = Stopwatch.StartNew();
                var result = new XElement("testcase", new XAttribute("name", test.Name));
                suite.Add(result);
                try { await test.Execute(cancellationToken); }
                catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
                {
                    result.Add(new XElement("error", new XAttribute("message", "Observed caller cancellation; acceptance remains unestablished.")));
                    throw;
                }
                catch (Exception)
                {
                    // Exceptions can contain credentials/provider data. Native test logs
                    // may carry owner-redacted details; this report retains only identity.
                    failed = true;
                    result.Add(new XElement("failure", new XAttribute("message", "Integration case failed; inspect redacted owner evidence.")));
                }
                finally { result.Add(new XAttribute("time", clock.Elapsed.TotalSeconds)); }
            }
        }
        finally
        {
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(reportPath))!);
            await File.WriteAllTextAsync(reportPath, new XDocument(suite).ToString(), CancellationToken.None);
        }
        return failed ? 1 : 0;
    }
}
