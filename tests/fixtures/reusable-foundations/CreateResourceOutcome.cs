namespace Product.Core;

/// <summary>Application conflict protocol; provider exception details do not escape.</summary>
public enum CreateResourceOutcome
{
    /// <summary>The resource was committed.</summary>
    Created,
    /// <summary>The immutable resource identity already exists.</summary>
    Conflict
}
