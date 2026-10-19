namespace ProgramKit.Examples.Evidence;

/// <summary>Valid construction is pure. This fictional example supplies no account, grant or paid authority.</summary>
public sealed class ReviewDeployment
{
    /// <summary>Validates pure nonsecret construction without I/O.</summary>
    public ReviewDeployment(string desk)
    {
        if (desk.Length is < 1 or > 40 || desk.Any(char.IsControl))
            throw new ArgumentException("Select a valid desk.");
        Desk = desk;
    }

    /// <summary>The admitted nonsecret desk name.</summary>
    public string Desk { get; }
}
