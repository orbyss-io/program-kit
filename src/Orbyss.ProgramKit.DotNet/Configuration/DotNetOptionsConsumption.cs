namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Options interface selected for a consuming service.</summary>
public enum DotNetOptionsConsumption
{
    /// <summary>Fixed singleton IOptions value.</summary>
    Fixed,
    /// <summary>Scoped IOptionsSnapshot value.</summary>
    Snapshot,
    /// <summary>Singleton-capable IOptionsMonitor value with change notifications.</summary>
    Monitor,
}
