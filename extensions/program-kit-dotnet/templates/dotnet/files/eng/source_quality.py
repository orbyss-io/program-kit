"""Project declared source conventions into task context without evaluating MSBuild."""
from pathlib import Path
import re
from central_packages import central_package_versions


def guidance(root: Path):
    """Use the actual selected pin; never substitute the current default for a consumer."""
    root = root.resolve()
    version = None
    diagnostic = None
    if (root / 'Directory.Packages.props').is_file():
        try:
            version = central_package_versions(root).get('orbyss.foundation.analyzers')
        except (ValueError, OSError) as error:
            diagnostic = str(error)
    config = root / '.editorconfig'
    declarations = []
    if config.is_file():
        section = None
        for line in config.read_text(encoding='utf-8-sig').splitlines():
            stripped = line.strip()
            if stripped.startswith('[') and stripped.endswith(']'):
                section = stripped
            match = re.fullmatch(r'dotnet_diagnostic\.ORB1003\.severity\s*=\s*(\w+)', stripped, re.I)
            if match:
                declarations.append({'section': section, 'severity': match[1].lower()})
    return {'analyzerPackage': 'Orbyss.Foundation.Analyzers', 'selectedVersion': version,
            'rule': 'ORB1003', 'rootDeclarations': declarations, 'diagnostic': diagnostic,
            'effectiveProjectConfigurationQualified': False,
            'guidance': [
                'Write one named type per C# file, including enums, records, interfaces, nested and test helper types. Keep generated output separate; do not hand-edit it.',
                'For a label contract use ILabelRule.cs, LabelRequest.cs, LabelDecision.cs and LabelFailure.cs. See program-kit-dotnet/references/examples/contract-layout; pass the actual selected analyzer pin to its qualification command.',
                'The root declarations shown here are task context. Project configuration, nested editorconfig, generated-code classification and scoped suppression remain subject to the actual selected native compiler/analyzer build. Missing or unsupported pins are unresolved, not an analyzer pass.'
            ]}
