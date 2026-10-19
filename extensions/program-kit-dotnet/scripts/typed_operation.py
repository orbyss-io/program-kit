"""Finite typed-label source adapter. No selection, execution, package installation or policy copies."""
from pathlib import Path, PurePosixPath
import posixpath
import re

RECIPE = 'extensions/program-kit-dotnet/references/examples/typed-operation/README.md'
ADAPTER = 'typed-label-v1'
FILES = {
    'core': ('ILabelStore.cs', 'ILabelOperations.cs'),
    'runtime': ('LabelOperations.cs', 'LabelServices.cs'),
    'api': ('LabelEndpoint.cs', 'LabelEndpoints.cs', 'LabelRequest.cs', 'LabelResponse.cs', 'LabelApiOptions.cs'),
    'provider': ('PostgreSqlLabelStore.cs',),
}


def require(condition, message):
    if not condition:
        raise ValueError('PKS300 ' + message)


def relative(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', value)
            and not {'.', '..'} & set(value.split('/')), 'use confined native owner paths')
    return value


def render(owners, extensions):
    """Render exact installed example sources; consumer ownership begins on creation.

    Native projects, feature registration, options metadata and client type generation
    retain their normal owners. The governance caller validates evaluated context.
    """
    require(isinstance(owners, dict) and set(owners) == {'core', 'runtime', 'api', 'provider', 'test',
            'frontend', 'generatedTypes'}, 'declare core/runtime/api/provider/test/frontend/generatedTypes owners')
    for value in owners.values():
        relative(value)
    require(all(owners[key].endswith('.csproj') for key in FILES.keys() | {'test'}), 'select native project owners')
    require(len({owners[key].casefold() for key in FILES.keys() | {'test'}}) == 5, 'source and test owners must be distinct')
    require(owners['generatedTypes'].endswith('.ts'), 'select the native generated TypeScript output')
    # Shared source access supports loose and packaged logical assets without extraction.
    from asset_sources import tree
    sources = tree(Path(extensions) / 'program-kit-dotnet/references/examples/typed-operation')
    outputs = {}
    for owner, names in FILES.items():
        for name in names:
            require(name in sources, 'restore the complete installed typed-operation recipe')
            outputs[str(PurePosixPath(owners[owner]).parent / name)] = sources[name]
    client = sources['client.ts']
    seam = b"../../../tools/openapi/policies/generated/types"
    require(client.count(seam) == 1, 'generated-client import seam changed; qualify the adapter')
    import_path = posixpath.relpath(owners['generatedTypes'][:-3], owners['frontend'] + '/src')
    if not import_path.startswith('.'):
        import_path = './' + import_path
    outputs[owners['frontend'] + '/src/client.ts'] = client.replace(seam, import_path.encode())
    require(len({p.casefold() for p in outputs}) == len(outputs), 'colliding source destinations')
    return outputs
