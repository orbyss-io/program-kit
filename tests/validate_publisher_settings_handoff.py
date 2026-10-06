"""Optional local upstream-source acceptance; supplies no public-package qualification."""
import argparse,json,shutil,subprocess,sys,zipfile
from pathlib import Path
from validate_application_handoff import HandoffTests, handoff, verify_handoff
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path,required=True);parser.add_argument('--build-package',type=Path);args=parser.parse_args();package=args.package.resolve()
 test=HandoffTests();test.setUp()
 try:
  with zipfile.ZipFile(package) as archive:envelope=json.loads(archive.read('orbyss-foundation/settings.json'))
  if args.build_package:
   sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'extensions/program-kit-governance/scripts'))
   import json_schema
   with zipfile.ZipFile(args.build_package) as archive:schema=json.loads(archive.read('schemas/settings.schema.json'))
   validator,_=json_schema.engine(schema,Path(args.build_package).resolve())
   assert not list(validator.iter_errors(envelope))
  package_id=envelope['packageId'];scope=envelope['contracts'][0]['scope']
  shutil.copyfile(package,test.packages/package.name)
  reference=dict(schemaVersion=1,kind='foundation-package',packageId=package_id,packageVersion=envelope['packageVersion'],packageSha256=handoff.digest(package),scope=scope)
  test.write('contracts/framework-settings.json',reference)
  test.selected['categories']['settings']['files'].append('contracts/framework-settings.json')
  test.selected['components'][0]['packages'].append(package_id)
  test.selected['requiredSettingsScopes'][package_id]=[scope]
  test.write('eng/application-handoff.json',test.selected);test.produce()
  index=handoff.assemble(test.root);assert index['status']=='ready'
  output=test.root/'artifacts/handoff/application-handoff.zip'
  receiver=Path(test.temp.name)/'independent-receiver';receiver.mkdir();shutil.copyfile(output,receiver/output.name)
  assert verify_handoff.verify(receiver/output.name)['status']=='ready'
  with zipfile.ZipFile(receiver/output.name) as archive:
   assert json.loads(archive.read('metadata/settings/'+package_id+'.json'))==envelope
   (receiver/'verify_handoff.py').write_bytes(archive.read('verify_handoff.py'))
  result=subprocess.run([sys.executable,'-I','verify_handoff.py',output.name],cwd=receiver,capture_output=True,text=True)
  assert result.returncode==0,result.stdout+result.stderr
  evidence=Path(__file__).resolve().parents[1]/'artifacts/handoff-validation/publisher-settings-integration.json'
  evidence.parent.mkdir(parents=True,exist_ok=True);evidence.write_text(json.dumps(dict(package=str(package),packageSha256=handoff.digest(package),owner=package_id,scope=scope,assemblyBound=True,independentReceiver=True,publicAvailabilityQualified=False,frameworkWideCoverage=False),indent=2)+'\n')
  print('Real locally built publisher companion consumed through native selected closure and independent receiver. Evidence: '+str(evidence))
 finally:test.doCleanups()
if __name__=='__main__':main()
