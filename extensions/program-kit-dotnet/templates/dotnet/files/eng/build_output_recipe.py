"""Closed copying of owned SDK-published outputs; no runtime worker or parser."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def require(condition, message):
    if not condition:
        raise ValueError('PKV003 ' + message)


def declarations(root, project, graph):
    rows = graph[project].get('buildOutputCopies', [])
    require(isinstance(rows, list) and len(rows) <= 16, 'buildOutputCopies must be a bounded list')
    folders, producers = [], set()
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'project', 'directory'}, 'build output copy fields differ from the supported recipe')
        producer, folder = row['project'], row['directory']
        require(isinstance(producer, str) and producer in graph[project].get('buildProjectReferences', [])
                and producer in graph and producer not in producers, 'build output producer must be a distinct declared build-only project')
        require(isinstance(folder, str) and re.fullmatch(r'tools/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', folder)
                and not any(part in ('.', '..') for part in folder.split('/')),
                'build output destination must be an owned tools subdirectory')
        require(not any(folder.casefold() == old or folder.casefold().startswith(old + '/')
                        or old.startswith(folder.casefold() + '/') for old in folders), 'overlapping build output destinations')
        producers.add(producer); folders.append(folder.casefold())
        for relative in (project, producer):
            target = (root / relative).resolve()
            require(target.is_relative_to(root.resolve()), 'build output owner escapes repository')
            paths = [target, *(parent / filename for parent in target.parents if parent.is_relative_to(root.resolve())
                              for filename in ('Directory.Build.props', 'Directory.Build.targets'))]
            for path in paths:
                if not path.is_file():
                    continue
                tree = ET.parse(path)
                require(not any(node.tag.rsplit('}', 1)[-1] in {'TargetDir', 'OutputPath', 'BaseOutputPath',
                    'AppendTargetFrameworkToOutputPath', 'AppendRuntimeIdentifierToOutputPath', 'RuntimeIdentifier', 'RuntimeIdentifiers'}
                    for group in tree.iter('PropertyGroup') for node in group),
                    'custom SDK output/RID layouts require an evaluated build-output adapter')
    return rows


def recipe(root, project, graph):
    """Emit reviewable XML; never writes consumer projects or modifies dependency pins."""
    rows = declarations(root, project, graph)
    result = ET.Element('Project')
    if not rows:
        return result
    names = ['ProgramKitPackBuildOutput' + str(index) for index in range(len(rows))]
    properties = ET.SubElement(result, 'PropertyGroup')
    ET.SubElement(properties, 'TargetsForTfmSpecificContentInPackage').text = '$(TargetsForTfmSpecificContentInPackage);' + ';'.join(names)
    for index, row in enumerate(rows):
        suffix, directory = str(index), row['directory']
        publish = '$(MSBuildProjectDirectory)/obj/ProgramKit.BuildOutputs/' + suffix + '/'
        source = publish + '**/*'
        destination = '$(TargetDir)' + directory
        copied, exposed, packed = 'ProgramKitBuildOutput' + suffix, 'ProgramKitCopiedOutput' + suffix, 'ProgramKitPackOutput' + suffix
        target = ET.SubElement(result, 'Target', Name='ProgramKitCopyBuildOutput' + suffix, BeforeTargets='GetCopyToOutputDirectoryItems')
        ET.SubElement(target, 'RemoveDir', Directories=publish)
        ET.SubElement(target, 'MSBuild', Projects='$(MSBuildThisFileDirectory)' +
                      os.path.relpath(root / row['project'], (root / project).parent).replace('\\', '/'),
                      Targets='Publish', BuildInParallel='false',
                      Properties='Configuration=$(Configuration);TargetFramework=$(TargetFramework);PublishDir=' + publish)
        ET.SubElement(ET.SubElement(target, 'ItemGroup'), copied, Include=source)
        ET.SubElement(target, 'Error', Condition="'@(" + copied + ")' == ''", Text='Declared build output is missing; rebuild the owned producer.')
        ET.SubElement(target, 'RemoveDir', Directories=destination)
        task = ET.SubElement(target, 'Copy', SourceFiles='@(' + copied + ')',
                             DestinationFiles="@(" + copied + "->'" + destination + "/%(RecursiveDir)%(Filename)%(Extension)')")
        ET.SubElement(task, 'Output', TaskParameter='CopiedFiles', ItemName='FileWrites')
        target = ET.SubElement(result, 'Target', Name='ProgramKitExposeBuildOutput' + suffix,
                               BeforeTargets='GetCopyToOutputDirectoryItems', DependsOnTargets='ProgramKitCopyBuildOutput' + suffix)
        group = ET.SubElement(target, 'ItemGroup')
        ET.SubElement(group, exposed, Include=destination + '/**/*')
        content = ET.SubElement(group, 'ContentWithTargetPath', Include='@(' + exposed + ')', CopyToOutputDirectory='PreserveNewest')
        ET.SubElement(content, 'TargetPath').text = directory + '/%(' + exposed + '.RecursiveDir)%(' + exposed + '.Filename)%(' + exposed + '.Extension)'
        target = ET.SubElement(result, 'Target', Name=names[index])
        group = ET.SubElement(target, 'ItemGroup')
        ET.SubElement(group, packed, Include=destination + '/**/*')
        content = ET.SubElement(group, 'TfmSpecificPackageFile', Include='@(' + packed + ')')
        ET.SubElement(content, 'PackagePath').text = directory + '/%(' + packed + '.RecursiveDir)%(' + packed + '.Filename)%(' + packed + '.Extension)'
    return result


def shape(node):
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(), tuple(shape(child) for child in node))


def derived_nodes(root, path, tree, graph):
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    if relative not in graph or not graph[relative].get('buildOutputCopies'):
        return set()
    expected = recipe(root, relative, graph)
    approved = set()
    for node in expected:
        if node.tag == 'Target':
            matches = [candidate for candidate in tree if candidate.tag == 'Target' and candidate.get('Name') == node.get('Name')]
        else:
            matches = [candidate for candidate in tree if candidate.tag == 'PropertyGroup'
                       and candidate.find('TargetsForTfmSpecificContentInPackage') is not None]
        require(len(matches) == 1 and shape(matches[0]) == shape(node),
                'declared build output target differs from its qualified recipe; preview eng/build_output_recipe.py')
        approved.update(id(item) for item in matches[0].iter())
    # No unknown task/property/item is waived by declaring the producer or recipe.
    return approved


def main():
    parser = argparse.ArgumentParser(description='Preview owner-declared build-output XML; reconcile through normal reviewed project editing.')
    parser.add_argument('--repository', default='.')
    parser.add_argument('--project', required=True)
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    from repository_architecture import validate_planned
    graph = validate_planned(root, json.loads((root / 'eng/architecture.json').read_text(encoding='utf-8')))
    require(args.project in graph, 'select a declared project owner')
    output = recipe(root, args.project, graph)
    ET.indent(output, space='  ')
    print(ET.tostring(output, encoding='unicode'))


if __name__ == '__main__':
    main()
