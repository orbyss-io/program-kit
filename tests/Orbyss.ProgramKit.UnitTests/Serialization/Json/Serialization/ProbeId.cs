using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal readonly record struct ProbeId(string Value);
