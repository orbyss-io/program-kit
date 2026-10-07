"""Read exact versioned publisher knowledge on demand, without installing dependencies."""
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET
import building_blocks as blocks


def bounded_pages(text, limit=12000):
    pages=[]; current=''; size=0
    for character in text:
        width=len(character.encode('utf-8'))
        if size+width>limit:
            pages.append(current); current=''; size=0
        current+=character; size+=width
    if current or not pages: pages.append(current)
    return pages


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile')
    parser.add_argument('--package')
    parser.add_argument('--fact',help='Exact schema, descriptor, README or XML fact path within the package')
    parser.add_argument('--symbol',help='Exact XML documentation member name, such as T:Namespace.Interface')
    parser.add_argument('--document',help='Exact publisher-relative source/document path')
    parser.add_argument('--page',type=int,default=1)
    args=parser.parse_args()
    if (args.fact or args.symbol) and not args.package: parser.error('--fact/--symbol require --package')
    if args.symbol and not args.fact: parser.error('--symbol requires the exact XML --fact')
    if args.package and args.document: parser.error('Select a package or a publisher document')
    registry=blocks.profile_registry(); index=blocks.load_json(registry/'index.json')
    identity=args.profile or index['default']; entry=index['profiles'][identity]
    blocks.qualified_dependency_profile(registry,identity,blocks.load_json(blocks.default_catalog(Path(blocks.__file__))))
    manifest=blocks.load_json(registry/entry['knowledge']['path'])
    if args.package:
        row=next((p for p in manifest['packages'] if p['id']==args.package),None)
        if row is None: parser.error('Select a package listed by this exact profile')
        package=blocks.load_json(registry/row['path'])
        if args.fact:
            if args.fact not in package['facts']: parser.error('Select an available package fact')
            text=package['facts'][args.fact]
            if args.symbol:
                members=[m for m in ET.fromstring(text).iter('member') if m.get('name')==args.symbol]
                if len(members)!=1: parser.error('Select one available XML member')
                text=ET.tostring(members[0],encoding='unicode')
        else:
            text=json.dumps({key:package[key] for key in ('id','version','license','repository')} | {'facts':sorted(package['facts'])},indent=2)
    elif args.document:
        row=next((p for p in manifest['documents'] if p['publisherPath']==args.document),None)
        if row is None: parser.error('Select an available publisher document')
        text=blocks.publisher_document_bytes(registry,row).decode('utf-8')
    else:
        text=json.dumps({'profile':identity,'releaseVersion':manifest['releaseVersion'],
            'packages':[p['id'] for p in manifest['packages']],
            'documents':[p['publisherPath'] for p in manifest['documents']]},indent=2)
    pages=bounded_pages(text)
    if args.page<1 or args.page>len(pages): parser.error('Select an available knowledge page')
    print(f'Publisher knowledge page {args.page}/{len(pages)}; exact selected profile {identity}')
    print(pages[args.page-1],end='')


if __name__=='__main__': main()
