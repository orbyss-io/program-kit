using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed record FactoryBoundaryModel([property: JsonPropertyName("declared")] DeclaredFactoryValue Declared, [property: JsonPropertyName("foreign")] ForeignFactoryValue Foreign);
