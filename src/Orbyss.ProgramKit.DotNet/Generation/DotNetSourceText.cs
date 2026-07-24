using System.Text;

namespace Orbyss.ProgramKit.DotNet.Generation;

internal static class DotNetSourceText
{
    internal static ReadOnlyMemory<byte> Utf8(string value) =>
        Encoding.UTF8.GetBytes(value.Replace("\r\n", "\n", StringComparison.Ordinal));

    internal static string CSharpLiteral(string value) =>
        string.Concat(
            "\"",
            value
                .Replace("\\", "\\\\", StringComparison.Ordinal)
                .Replace("\"", "\\\"", StringComparison.Ordinal)
                .Replace("\r", "\\r", StringComparison.Ordinal)
                .Replace("\n", "\\n", StringComparison.Ordinal),
            "\"");

    internal static string Xml(string value) =>
        value
            .Replace("&", "&amp;", StringComparison.Ordinal)
            .Replace("<", "&lt;", StringComparison.Ordinal)
            .Replace(">", "&gt;", StringComparison.Ordinal)
            .Replace("\"", "&quot;", StringComparison.Ordinal);
}
