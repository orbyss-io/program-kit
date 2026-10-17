using System.Text;

namespace ProgramKit.Examples.PdfDecoding;

internal static class PdfFixture
{
    public static byte[] Build(byte[] content, bool compressedContent, byte[]? image = null, byte[]? unreachable = null)
    {
        using var result = new MemoryStream();
        var offsets = new List<long> { 0 };
        void Text(string text) => result.Write(Encoding.ASCII.GetBytes(text));
        void Object(string text)
        {
            offsets.Add(result.Position); Text($"{offsets.Count - 1} 0 obj\n{text}\nendobj\n");
        }
        void Stream(string properties, byte[] bytes)
        {
            offsets.Add(result.Position); Text($"{offsets.Count - 1} 0 obj\n<< /Length {bytes.Length} {properties} >>\nstream\n");
            result.Write(bytes); Text("\nendstream\nendobj\n");
        }
        Text("%PDF-1.7\n");
        Object("<< /Type /Catalog /Pages 2 0 R >>");
        Object("<< /Type /Pages /Kids [3 0 R] /Count 1 >>");
        var resources = image is null ? "<< >>" : "<< /XObject << /Im0 5 0 R >> >>";
        Object($"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Resources {resources} /Contents 4 0 R >>");
        Stream(compressedContent ? "/Filter /FlateDecode" : "", content);
        if (image is not null) Stream("/Type /XObject /Subtype /Image /Width 2 /Height 2 /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode", image);
        if (unreachable is not null) Stream("/Filter /FlateDecode", unreachable);
        var xref = result.Position;
        Text($"xref\n0 {offsets.Count}\n0000000000 65535 f \n");
        foreach (var offset in offsets.Skip(1)) Text($"{offset:D10} 00000 n \n");
        Text($"trailer\n<< /Size {offsets.Count} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n");
        return result.ToArray();
    }
}
