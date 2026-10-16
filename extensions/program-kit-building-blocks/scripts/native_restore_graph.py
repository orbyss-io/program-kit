"""Evaluate current SDK projects and native NuGet output ownership in one context.

No restore/build/run target is requested. GenerateRestoreGraphFile is the native
NuGet metadata target; consumer overrides/hooks for restore targets are refused.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET

CONFIG = 'eng/restore-graph.json'
IGNORED = {'.git', '.specify', '.program-kit', 'artifacts', 'bin', 'obj', 'node_modules'}


def require(value, message):
    if not value:
        raise ValueError('PKB621 ' + message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def local(root, value, base=None, project=False):
    require(isinstance(value, str) and value and not any(c in value for c in '*?\x00'), 'native graph path is missing/dynamic')
    target = Path(value.replace('\\', '/'))
    target = (target if target.is_absolute() else (base or root)/target).resolve()
    require(target.is_relative_to(root), 'native restore graph/output escapes this repository: ' + str(target))
    if project:
        require(target.suffix.lower() in {'.csproj', '.fsproj', '.vbproj'} and target.is_file()
                and not IGNORED & set(target.relative_to(root).parts), 'native graph reaches missing/retired/scratch project: ' + str(target))
    # Refuse aliases in the original rooted spelling as well as final location.
    original = Path(value.replace('\\', '/'))
    original = original if original.is_absolute() else (base or root)/original
    for path in (original, *original.parents):
        if path.is_relative_to(root) and path.exists():
            require(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(), 'native restore ownership refuses linked paths')
    return target.relative_to(root).as_posix()


def evaluate(root, inventory, environment):
    root = root.resolve()
    config_path = root/CONFIG
    config = json.loads(config_path.read_text(encoding='utf-8'))
    require(set(config) == {'schemaVersion', 'adapter', 'configuration', 'sdkVersion'}
            and config['schemaVersion'] == 1 and config['adapter'] == 'native-msbuild'
            and isinstance(config['configuration'], str) and re.fullmatch('[A-Za-z0-9_.-]{1,64}', config['configuration'])
            and isinstance(config['sdkVersion'], str) and re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', config['sdkVersion']),
            'unsupported evaluated restore context; declare exact native-msbuild SDK and configuration')
    toolchain_path = root/'artifacts/program-kit/toolchain.json'
    toolchain = json.loads(toolchain_path.read_text()) if toolchain_path.is_file() else {}
    dotnet = toolchain.get('commands', {}).get('dotnet', ['dotnet'])
    require(isinstance(dotnet, list) and dotnet and all(isinstance(arg, str) for arg in dotnet), 'invalid recorded native SDK command')
    require(not toolchain or toolchain.get('required', {}).get('dotnet') == config['sdkVersion']
            == toolchain.get('resolved', {}).get('dotnet'), 'evaluated graph SDK must match current toolchain evidence')
    directory = root/'artifacts/program-kit/restore-graph-runs'/uuid.uuid4().hex
    directory.mkdir(parents=True)
    steps = []
    def run(arguments):
        command = [*dotnet, *arguments]
        index = len(steps); steps.append({'command': command, 'status': 'running'})
        stdout = directory/f'{index}.stdout.log'; stderr = directory/f'{index}.stderr.log'
        with stdout.open('w', encoding='utf-8') as out, stderr.open('w', encoding='utf-8') as err:
            result = subprocess.run(command, cwd=root, env=environment, stdout=out, stderr=err, timeout=120)
        steps[-1].update(exitCode=result.returncode, status='completed' if result.returncode == 0 else 'failed')
        require(result.returncode == 0, 'native graph evaluation failed; inspect ' + str(directory))
        require(stdout.stat().st_size <= 16_777_216, 'native graph response exceeds its bounded metadata budget')
        return stdout.read_text(encoding='utf-8-sig').strip()
    result = {'status': 'running', 'steps': steps, 'acceptanceEstablished': False}
    try:
        protected, historical_roots = set(), []
        if (root/'eng/retained-inputs.json').is_file():
            import dotnet_adapter
            dotnet_adapter.bootstrap()
            import retained_inputs
            retention = retained_inputs.snapshot(root)
            protected = {*retention['frozen'], *retention.get('retiredLocks', {})}
            historical_roots = [row['root'] for row in retention.get('archives', [])]
        require(run(['--version']) == config['sdkVersion'], 'actual native SDK differs from evaluated restore context')
        source_inputs = {}
        pending, observed, sources, evaluated_outputs = list(inventory), {}, {}, {}
        while pending:
            relative = local(root, pending.pop(), project=True)
            if relative in observed:
                continue
            require(len(observed) < 256, 'native project graph exceeds its finite owner budget')
            project = root/relative
            properties = 'TargetFramework,TargetFrameworks,ProjectAssetsFile,RestoreOutputPath,MSBuildProjectExtensionsPath,NuGetLockFilePath,MSBuildToolsPath'
            common = ['msbuild', str(project), '-nologo', '-v:quiet', '-p:Configuration='+config['configuration'], '-p:RestorePackagesWithLockFile=true']
            expanded = directory/f'project-{len(observed)}.xml'
            run([*common, '-preprocess:'+str(expanded)])
            require(expanded.stat().st_size <= 16_777_216, 'native expanded input exceeds its finite budget')
            sources[relative] = sha(expanded.read_bytes())
            value = json.loads(run([*common, '-getProperty:'+properties, '-getItem:ProjectReference']))
            # Preprocessing and item/property queries execute no MSBuild targets.
            # Inspect actual imported sources before the native metadata target;
            # inactive examples elsewhere in the repository grant no execution.
            imports = re.findall(r'\n([A-Za-z]:[\\/][^\r\n]+|/[^\r\n]+)\r?\n={20,}\r?\n-->', expanded.read_text(encoding='utf-8-sig'))
            require(imports and project.resolve() in {Path(path).resolve() for path in imports}, 'unsupported native preprocessor provenance format')
            sdk_root = Path(value['Properties']['MSBuildToolsPath']).resolve()
            sdk_inputs = [sdk_root, sdk_root.parents[1]/'sdk-manifests', sdk_root.parents[1]/'packs']
            package_root = Path(environment['NUGET_PACKAGES']).resolve()
            generated_root = Path(value['Properties']['MSBuildProjectExtensionsPath']).resolve()
            for imported in imports:
                path = Path(imported).resolve()
                require(path.is_file(), 'native imported source disappeared during inspection')
                if any(path.is_relative_to(directory) for directory in sdk_inputs) or path.is_relative_to(package_root):
                    continue  # Their complete expanded bytes remain bound below.
                require(path.is_relative_to(root), 'external imported source needs an admitted native adapter: ' + str(path))
                relative_import = path.relative_to(root)
                generated = path.parent == generated_root and path.name.endswith(('.nuget.g.props', '.nuget.g.targets'))
                require(generated or not IGNORED & set(relative_import.parts), 'native evaluation imports retired/scratch source: ' + str(path))
                local(root, imported)
                require(len(source_inputs) < 4096 and path.stat().st_size <= 16_777_216, 'native build input inventory exceeds its finite budget')
                raw = path.read_bytes(); source_inputs[path] = sha(raw)
                require(not re.search(rb'Restore(?:ForceEvaluate|LockedMode)', raw, re.I),
                        'mode-dependent native restore policy needs a separate admitted adapter: ' + str(path))
                for target in ET.fromstring(raw).iter():
                    if target.tag.rsplit('}', 1)[-1] == 'Target':
                        hooks = ' '.join(target.get(field, '') for field in ('Name', 'BeforeTargets', 'AfterTargets'))
                        require('restore' not in hooks.lower(), 'consumer restore-target override/hook needs a separate admitted adapter: ' + str(path))
            variants = [value]
            frameworks = value['Properties'].get('TargetFrameworks', '')
            if frameworks:
                for framework in frameworks.split(';'):
                    require(re.fullmatch('[A-Za-z0-9_.-]{1,128}', framework), 'unsupported evaluated framework identity')
                    variants.append(json.loads(run([*common, '-p:TargetFramework='+framework, '-getProperty:'+properties, '-getItem:ProjectReference'])))
            edges = set()
            output_variants = set()
            for variant in variants:
                props = variant['Properties']
                lock_path = local(root, props.get('NuGetLockFilePath') or 'packages.lock.json', project.parent)
                output_path = local(root, props.get('RestoreOutputPath') or props['MSBuildProjectExtensionsPath'], project.parent)
                assets_path = local(root, props['ProjectAssetsFile'], project.parent)
                output_variants.add((lock_path, output_path, assets_path))
                for item in variant['Items'].get('ProjectReference', []):
                    require(not any(item.get(key) for key in ('AdditionalProperties', 'SetConfiguration', 'SetPlatform', 'SetTargetFramework', 'GlobalPropertiesToRemove')),
                            'multiple reference evaluation contexts need a separate admitted adapter')
                    if item.get('ExcludeRestore', '').lower() == 'true':
                        continue
                    edges.add(local(root, item.get('FullPath', item['Identity']), project.parent, project=True))
            require(len(output_variants) == 1, 'framework-specific restore outputs need separate native owner identities')
            evaluated_outputs[relative] = output_variants.pop()
            observed[relative] = edges
            pending.extend(edges-set(observed))
        # All references are current, contained owners before any native graph
        # target can traverse them. Use project restores in the explicit context;
        # do not silently inherit solution-specific configuration remapping.
        solution = directory/'Inventory.slnx'
        document = ET.Element('Solution')
        for relative in sorted(observed):
            ET.SubElement(document, 'Project', Path=str(root/relative))
        ET.ElementTree(document).write(solution, encoding='utf-8', xml_declaration=True)
        graph_path = directory/'native.dg.json'
        run(['msbuild', str(solution), '-nologo', '-v:quiet', '-t:GenerateRestoreGraphFile',
             '-p:Configuration='+config['configuration'], '-p:RestoreGraphOutputPath='+str(graph_path),
             '-p:RestorePackagesWithLockFile=true',
             '-p:RestoreConfigFile='+str(root/'NuGet.config')])
        require(graph_path.stat().st_size <= 16_777_216, 'native restore graph exceeds its finite budget')
        raw = graph_path.read_bytes(); data = json.loads(raw)
        require(data.get('format') == 1 and isinstance(data.get('projects'), dict), 'unsupported native NuGet restore graph format')
        graph, outputs = {}, {}
        for key, row in data['projects'].items():
            relative = local(root, key, project=True)
            require(relative in observed, 'native graph introduced an owner after targetless admission')
            metadata = row['restore']
            require(local(root, metadata['projectPath'], project=True) == relative and metadata.get('projectStyle') == 'PackageReference',
                    'native graph project identity/style differs from admitted owner')
            edges = {local(root, reference, project=True) for framework in metadata.get('frameworks', {}).values()
                     for reference in framework.get('projectReferences', {})}
            require(edges == observed[relative], 'native restore graph differs from targetless reference admission')
            graph[relative] = edges
            lock = metadata.get('restoreLockProperties', {}).get('nuGetLockFilePath') or 'packages.lock.json'
            output = local(root, metadata['outputPath'])
            outputs[relative] = {'lock': local(root, lock, (root/relative).parent),
                                 'assets': local(root, str(root/output/'project.assets.json'))}
            for destination in outputs[relative].values():
                parts = Path(destination).parts
                require(not {'.git', '.specify', '.program-kit', 'node_modules'} & set(parts)
                        and parts[0] not in {'docs', 'specs'} and destination not in protected
                        and not any(destination.startswith(prefix+'/') for prefix in historical_roots),
                        'native restore output would overwrite retained/foreign ownership: ' + destination)
            require(Path(outputs[relative]['lock']).suffix.lower() == '.json', 'native lock output must remain a JSON lock file')
            existing_lock = root/outputs[relative]['lock']
            if existing_lock.is_file():
                require(existing_lock.stat().st_size <= 16_777_216, 'native lock input exceeds its finite budget')
                previous = json.loads(existing_lock.read_text(encoding='utf-8-sig'))
                require(isinstance(previous, dict) and previous.get('version') == 1 and isinstance(previous.get('dependencies'), dict),
                        'native lock destination is not an existing NuGet lock; preserve foreign bytes: ' + outputs[relative]['lock'])
            expected_lock, expected_output, expected_assets = evaluated_outputs[relative]
            require(outputs[relative] == {'lock': expected_lock, 'assets': expected_assets} and output == expected_output,
                    'evaluated build inputs and native NuGet output locations differ; repair custom output policy: ' + relative)
        require(set(graph) == set(observed), 'native restore graph omitted admitted project owners')
        for relative in sorted(observed):
            expanded = directory/'after.xml'
            run(['msbuild', str(root/relative), '-nologo', '-v:quiet', '-p:Configuration='+config['configuration'],
                 '-p:RestorePackagesWithLockFile=true', '-preprocess:'+str(expanded)])
            require(sha(expanded.read_bytes()) == sources[relative], 'evaluated imports changed during native restore ownership inspection')
        require(all(sha(path.read_bytes()) == expected for path, expected in source_inputs.items()),
                'native build inputs changed during graph inspection')
        identity = {'adapterSha256': sha(Path(__file__).read_bytes()), 'configurationSha256': sha(config_path.read_bytes()),
                    'sdkVersion': config['sdkVersion'], 'configuration': config['configuration'],
                    'evaluatedSources': sources, 'nativeGraphCanonicalSha256': sha(json.dumps(data, sort_keys=True, separators=(',', ':')).encode())}
        result.update(status='completed', identity=identity,
                      graph={key: sorted(value) for key, value in graph.items()}, outputs=outputs)
        return graph, outputs, identity
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error))
        raise
    finally:
        (directory/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
