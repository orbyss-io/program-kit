namespace ProgramKit.Examples.Evidence;

/// <summary>Provider-private persistence record; never an aggregate or wire DTO.</summary>
internal sealed class EvidenceRow
{
    /// <summary>The owned id value.</summary>
    public string Id { get; set; } = "";
    /// <summary>The owned owner value.</summary>
    public string Owner { get; set; } = "";
    /// <summary>The owned packet value.</summary>
    public string Packet { get; set; } = "";
    /// <summary>The owned accepted value.</summary>
    public bool Accepted { get; set; }
    /// <summary>The owned revision value.</summary>
    public int Revision { get; set; }
}
