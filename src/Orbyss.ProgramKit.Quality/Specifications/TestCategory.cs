namespace Orbyss.ProgramKit.Quality.Specifications;

/// <summary>Identifies the durable purpose of a test specification.</summary>
public enum TestCategory
{
    /// <summary>Tests one isolated source unit.</summary>
    Unit,
    /// <summary>Tests one assembled component boundary.</summary>
    Component,
    /// <summary>Tests a published contract or conformance rule.</summary>
    ContractConformance,
    /// <summary>Tests registration and composition behavior.</summary>
    RegistrationComposition,
    /// <summary>Tests collaborating implementation boundaries.</summary>
    Integration,
    /// <summary>Tests an externally observable flow from end to end.</summary>
    EndToEnd,
    /// <summary>Preserves behavior implicated by a prior defect.</summary>
    Regression,
    /// <summary>Tests mechanical architecture constraints.</summary>
    Architecture,
    /// <summary>Tests an explicit security property.</summary>
    Security,
    /// <summary>Tests a bounded performance expectation.</summary>
    Performance,
    /// <summary>Tests repeatability from exact inputs.</summary>
    Reproducibility,
    /// <summary>Tests an explicit compatibility expectation.</summary>
    Compatibility,
    /// <summary>Records a selected human validation activity.</summary>
    HumanValidation,
}
