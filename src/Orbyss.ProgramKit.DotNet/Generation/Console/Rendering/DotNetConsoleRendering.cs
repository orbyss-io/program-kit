using System.Globalization;
using System.Text;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Rendering;

internal static class DotNetConsoleRendering
{
    internal static string Type(DotNetConsoleClrTypeDescriptor type)
    {
        var metadataName = type.MetadataName.Replace('+', '.');
        var arityMarker = metadataName.LastIndexOf('`');
        if (arityMarker >= 0)
        {
            metadataName = metadataName[..arityMarker];
        }

        var rendered = string.Concat("global::", metadataName);
        if (!type.GenericArguments.IsDefaultOrEmpty)
        {
            rendered = string.Concat(
                rendered,
                "<",
                string.Join(", ", type.GenericArguments.Select(Type)),
                ">");
        }

        return type.ReferenceNullability ==
            DotNetConsoleReferenceNullability.Nullable
            ? string.Concat(rendered, "?")
            : rendered;
    }

    internal static string DefaultValue(
        DotNetConsoleValueProjection value)
    {
        var canonical = value.DefaultDisposition.CanonicalValue ??
            throw new InvalidOperationException(
                "A canonical default value is required.");
        return value.ElementType switch
        {
            "global::System.String" =>
                DotNetSourceText.CSharpLiteral(canonical),
            "global::System.Boolean" =>
                canonical == "true" ? "true" : "false",
            "global::System.Int32" => canonical,
            "global::System.Int64" => string.Concat(canonical, "L"),
            "global::System.Decimal" => string.Concat(canonical, "M"),
            "global::System.Guid" => string.Concat(
                "global::System.Guid.ParseExact(",
                DotNetSourceText.CSharpLiteral(canonical),
                ", \"D\")"),
            "global::System.DateTimeOffset" => string.Concat(
                "global::System.DateTimeOffset.ParseExact(",
                DotNetSourceText.CSharpLiteral(canonical),
                ", \"O\", global::System.Globalization.CultureInfo.InvariantCulture, ",
                "global::System.Globalization.DateTimeStyles.None)"),
            _ => throw new InvalidOperationException(
                string.Format(
                    CultureInfo.InvariantCulture,
                    "Unsupported generated default element type '{0}'.",
                    value.ElementType)),
        };
    }

    internal static void Line(
        StringBuilder builder,
        int indentation,
        string value = "")
    {
        builder.Append(' ', indentation * 4);
        builder.Append(value);
        builder.Append('\n');
    }
}
