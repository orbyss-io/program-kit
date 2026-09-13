"""Read-only native check of explicit completion selection in the installed consumer."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
roots = json.loads((ROOT / 'artifacts/delivery-phase4/consumers/repositories.json').read_text(encoding='utf-8'))
root = Path(roots['25592c38-0750-4cd4-8c7d-552d47ec9aa1'])
sys.path.insert(0, str(root / '.specify/extensions/program-kit-delivery/scripts'))
from delivery_contract import admit_execution, authority
import azure_execution as execution

receipt = authority.read(root / execution.RECEIPT)
if receipt['workId'] != 'P4-INTEGRATION':
    raise ValueError('Expected the completed receiving Task to occupy the local session receipt')
results = [admit_execution(root, activity, 'SPC-001') for activity in ('delivery', 'acceptance')]
if any(result['workId'] != 'P4-CLIENT' or result['completionRecorded'] for result in results):
    raise ValueError('Explicit completion selected unrelated work or recorded a new completion')
output = {'installedRuntime': str(Path(sys.modules['delivery_contract'].__file__).resolve()),
          'localReceiptWorkId': receipt['workId'], 'results': results}
(ROOT / 'artifacts/delivery-phase4/installed-completion.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
print(json.dumps(output))
