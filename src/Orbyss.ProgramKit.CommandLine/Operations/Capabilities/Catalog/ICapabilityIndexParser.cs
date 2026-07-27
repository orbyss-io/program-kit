namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

/// <summary>Parses the exact canonical capability index format.</summary>
public interface ICapabilityIndexParser
{
    /// <summary>Parses exact UTF-8 index bytes without filesystem discovery.</summary>
    CapabilityIndexDocument Parse(ReadOnlySpan<byte> content);
}
