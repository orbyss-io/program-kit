namespace ProgramKit.Tasks;

/// <summary>Identifies work owned by one CShells shell generation.</summary>
public interface IProgramKitTask
{
    /// <summary>A stable identity used in diagnostics.</summary>
    string Id => GetType().FullName ?? GetType().Name;
}
