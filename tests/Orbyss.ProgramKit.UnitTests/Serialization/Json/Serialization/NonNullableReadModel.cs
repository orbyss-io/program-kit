using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed record NonNullableReadModel(string Value);
