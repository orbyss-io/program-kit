"""Infer scoped feature mechanisms from ordinary design and engineering inputs."""
from pathlib import Path
import re

CAPABILITIES = {
    'dotnet': r'(?<!\w)(?:c#|\.net|dotnet)(?!\w)',
    'web': r'\b(?:browser|frontend|react|vite|typescript)\b',
    'api': r'\b(?:http|openapi|endpoint|api)\b',
    'persistence': r'\b(?:persistence|database|dbcontext|postgresql|sqlserver|sqlite|entityframeworkcore|entity framework|npgsql)\b',
    'capabilities': r'\b(?:capability|building.block|shellfeature|composition|activation)\b',
}
MECHANISMS = {
    'async': r'\b(?:async|await|task|valuetask|cancellation|deadline)\b',
    'concurrency': r'\b(?:concurrency|concurrent|parallel|lock|semaphore|shared state|channel|queue|contention)\b',
    'lifetime': r'\b(?:disposal|dispose|idisposable|iasyncdisposable|lifetime|scope|lease|factory|dependency injection|di)\b',
    'queries': r'\b(?:linq|query|queries|pagination|paging|iqueryable|enumeration)\b',
    'io': r'\b(?:i/o|io|httpclient|file|stream|timeout|deadline|options|configuration)\b',
    'security': r'\b(?:authorization|authentication|identity|secret|untrusted|security|permission|process|url|path admission)\b',
}


def affirmative(text):
    """Exclude explicit non-goals from prose inference, never actual package evidence."""
    excluded_depth = None
    lines = []
    for line in text.splitlines():
        heading = re.match(r'^\s*(#+)\s', line)
        if heading:
            depth = len(heading[1])
            if excluded_depth is not None and depth <= excluded_depth:
                excluded_depth = None
            if re.search(r'non.?goals?|out of scope|excluded|future work', line, re.I):
                excluded_depth = depth
        if excluded_depth is None:
            lines.append(line)
    clauses = re.split(r'(?<=[.!?;])\s+|\n', '\n'.join(lines))
    result = []
    for clause in clauses:
        # Preserve an affirmative prefix in "API without database" while dropping
        # clauses such as "API and browser are out of scope" altogether.
        if re.search(r'\b(?:out of scope|not required|excluded|future|deferred)\b', clause, re.I):
            continue
        result.append(re.split(r'\b(?:no|without)\s', clause, maxsplit=1, flags=re.I)[0])
    return '\n'.join(result)


def context(root, feature, phase, affected_paths=()):
    prose = '\n'.join(affirmative(path.read_text(encoding='utf-8'))
                      for name in ('spec.md', 'plan.md', 'research.md', 'data-model.md', 'quickstart.md')
                      if (path := feature / name).is_file())
    projects = [p for p in (root / 'src').rglob('*.csproj') if not {'bin', 'obj'} & set(p.parts)]
    projects += [p for p in feature.rglob('*.csproj') if not {'bin', 'obj'} & set(p.parts)]
    selected = [p for p in set(projects) if p.relative_to(root).as_posix() in prose
                or p.parent.relative_to(root).as_posix() in prose]
    engineering, source = [], []
    for project in selected:
        engineering.append(project.read_text(encoding='utf-8'))
        if phase in ('implementation', 'delivery'):
            for path in project.parent.rglob('*.cs'):
                if {'bin', 'obj'} & set(path.parts):
                    continue
                if not affected_paths or any(path.relative_to(root).as_posix() == p or
                    path.relative_to(root).as_posix().startswith(p.rstrip('/') + '/') for p in affected_paths):
                    source.append(path.read_text(encoding='utf-8'))
    for directory in ('src', 'web'):
        for package in (root / directory).rglob('package.json'):
            if {'node_modules', 'dist'} & set(package.parts):
                continue
            if package.relative_to(root).as_posix() in prose or package.parent.relative_to(root).as_posix() in prose:
                engineering.append(package.read_text(encoding='utf-8'))
    content = '\n'.join([prose, *engineering, *source]).lower()
    tags = {'all'}
    tags.update(tag for tag, pattern in CAPABILITIES.items() if re.search(pattern, content))
    if selected or (root / 'global.json').is_file():
        tags.add('dotnet')
    packages = '\n'.join(engineering).lower()
    # Qualified identity is stronger evidence than wording in the plan.
    if any(name in packages for name in ('entityframeworkcore', 'npgsql', 'microsoft.data.sqlite', 'microsoft.data.sqlclient')):
        tags.add('persistence')
    if 'microsoft.aspnetcore' in packages or 'microsoft.net.sdk.web' in packages:
        tags.add('api')
    if any(name in packages for name in ('"vite"', '"react"', '"typescript"')):
        tags.add('web')
    if 'api' in tags:
        tags.add('http-api')
    mechanisms = {name for name, pattern in MECHANISMS.items() if re.search(pattern, content)}
    if tags & {'persistence', 'api'}:
        mechanisms.update(('async', 'lifetime', 'io', 'security'))
    if 'persistence' in tags:
        mechanisms.update(('queries', 'concurrency'))
    if 'capabilities' in tags:
        mechanisms.add('lifetime')
    tags.update('dotnet-' + name for name in mechanisms if 'dotnet' in tags)
    return tags
