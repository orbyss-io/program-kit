"""Prepare source for a separate evidence repository; never provisions/publishes."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def prepare(output):
    output = Path(output)
    if output.exists():
        raise ValueError('PKRF evidence-repository-output-must-be-new')
    shutil.copytree(ROOT / 'evidence-repository', output)
    shutil.copyfile(ROOT / 'scripts/repair_evidence_guardian.py', output / 'guardian.py')
    shutil.copyfile(ROOT / 'extensions/program-kit-governance/scripts/repair_contract.py', output / 'repair_contract.py')
    shutil.copytree(ROOT / 'extensions/program-kit-governance/references/repair-feedback', output / 'contract')
    (output / '.gitignore').write_text('__pycache__/\n*.pyc\n', encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(prepare(parser.parse_args().output))
