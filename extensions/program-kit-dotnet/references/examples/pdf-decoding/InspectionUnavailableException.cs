namespace ProgramKit.Examples.PdfDecoding;

// An exhausted/incomplete operation supplies no content admission result.
public sealed class InspectionUnavailableException(string message) : Exception(message);
