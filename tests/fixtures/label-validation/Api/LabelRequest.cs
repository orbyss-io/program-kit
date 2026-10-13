/// <summary>Raw fixture transport input; normalized UTF-16 bounds are established by Core.</summary>
/// <param name="Label">The raw label, including controls that normalization must not hide.</param>
public sealed record LabelRequest(string? Label);
