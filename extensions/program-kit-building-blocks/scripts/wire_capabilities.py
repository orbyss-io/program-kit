"""Project validation constraints from verified selected publisher bytes, never a wire schema."""
import re
from pathlib import Path


def project(blocks, effective):
    capture = effective.get('publisherKnowledge')
    result = {'profile': effective['profile'], 'sourceCommit': capture.get('sourceCommit') if capture else None,
              'packages': {}, 'problem': None, 'json': None, 'unresolved': []}
    if not capture:
        result['unresolved'].append('selected profile lacks immutable publisher knowledge')
        return result
    registry = Path(effective['registryPath'])

    def source(package, path):
        selected = effective['catalog']['packages'].get('nuget:' + package, {}).get('version')
        row = next((p for p in capture['packages'] if p['id'] == package and p['version'] == selected), None)
        document = next((d for d in capture['documents'] if d['publisherPath'] == path), None)
        if row is None or document is None:
            result['unresolved'].append(package + '@' + str(selected) + ': missing exact package/source binding ' + path)
            return ''
        result['packages'][package] = selected
        return blocks.publisher_document_bytes(registry, document).decode('utf-8')

    envelope = source('Orbyss.Foundation.Web.ProblemDetails',
                      'src/Orbyss.Foundation.Web.ProblemDetails/FoundationProblemEnvelope.cs')
    match = re.search(r'FoundationProblemEnvelope\((.*?)\);', envelope, re.S)
    if match:
        members = re.findall(r'(string\??|int|IReadOnlyList<ProblemFieldError>)\s+(\w+)', match[1])
        fields = [name for _, name in members]
        if fields and 'closed bounded wire shape' in envelope:
            result['problem'] = {'fields': [f[0].lower() + f[1:] for f in fields],
                                 'fieldTypes': {name[0].lower() + name[1:]: ('integer' if kind == 'int' else 'array' if kind.startswith('IReadOnlyList') else 'string') for kind, name in members},
                                 'optional': ['detail'], 'additionalProperties': False}
    if not result['problem']:
        result['unresolved'].append('problem writer closed envelope could not be established from selected source')
    else:
        fields = source('Orbyss.Foundation.Web.ProblemDetails.Core', 'src/Orbyss.Foundation.Web.ProblemDetails.Core/ProblemFieldError.cs')
        names = re.findall(r'public string (\w+) \{ get; \}', fields)
        result['problem']['fieldErrorFields'] = [name[0].lower() + name[1:] for name in names]
        if not names: result['unresolved'].append('selected bounded field-error structure could not be established')
    parser = source('Orbyss.Foundation.Json', 'src/Orbyss.Foundation.Json/JsonProfile.cs')
    if 'NumberHandling = JsonNumberHandling.Strict' in parser and 'AllowDuplicateProperties = false' in parser:
        result['json'] = {'numberHandling': 'Strict', 'duplicateMembers': False,
                          'strictUnknownMembers': False, 'extensionsRequireProof': True,
                          'presets': ['strict-request', 'tolerant-response']}
        keys = source('Orbyss.Foundation.Json', 'src/Orbyss.Foundation.Json/JsonProfileKeys.cs')
        names = dict(re.findall(r'public const string (\w+) = "([^"]+)"', keys))
        settings = source('Orbyss.Foundation.Json', 'src/Orbyss.Foundation.Json/JsonProfileSettings.cs')
        options = source('Orbyss.Foundation.Json.AspNetCore', 'src/Orbyss.Foundation.Json.AspNetCore/FoundationJsonOptions.cs')
        default = re.search(r'Preset \{ get; set; \} = JsonProfileKeys\.(\w+)', settings)
        profiles = {}
        for key, fields in re.findall(r'\[JsonProfileKeys\.(\w+)\] = new\(\) \{([^}]*)\}', options):
            preset = re.search(r'Preset = JsonProfileKeys\.(\w+)', fields)
            symbol = preset[1] if preset else default[1] if default else None
            if key in names and symbol in names:
                profiles[names[key]] = {'Preset': names[symbol], 'Extensions': []}
        result['json']['defaultProfiles'] = profiles
        if not profiles: result['unresolved'].append('selected native JSON profile defaults could not be established')
    else:
        result['unresolved'].append('selected JSON parser numeric/duplicate constraints could not be established')
    return result
