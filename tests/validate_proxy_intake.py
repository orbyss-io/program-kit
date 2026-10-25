"""Explicit fictional rehearsal scope and readable draft preservation."""
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
import proxy_intake as proxy

class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'.intake-session-owner').write_text('synthetic disposable fixture')
        (self.root/'INTAKE-SESSION.md').write_text('Synthetic fixture')
        (self.root/'product-idea.md').write_text('A requester records a request.')
    def transcript(self):
        path=self.root/proxy.TRANSCRIPT;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(proxy.NOTICE+'\nQuestion: visible outcome?\nSimulated answer: stable request identity.\n')
    def full_draft(self):
        proxy.begin(self.root,'full-intake');self.transcript()
        (self.root/'docs/architecture/project-intent.md').write_text('# Request service\n'+proxy.NOTICE+'\nA requester records a request; retention is deferred to its selected feature.')
    def test_one_round_no_authority_and_scope_preserved(self):
        first=proxy.begin(self.root,'one-round');self.assertEqual(first,proxy.begin(self.root,'one-round'))
        self.transcript();self.assertEqual('none',proxy.verify(self.root)['authority'])
        with self.assertRaisesRegex(ValueError,'differs'):proxy.begin(self.root,'full-intake')
    def test_full_readable_draft_needs_no_intake_json_or_map(self):
        self.full_draft();result=proxy.verify(self.root)
        self.assertEqual('rehearsal-checked',result['status'])
        self.assertFalse((self.root/proxy.INTAKE).exists())
    def test_real_ratification_and_adr_acceptance_are_refused(self):
        self.full_draft()
        path=self.root/'.specify/memory/constitution.md';path.parent.mkdir(parents=True)
        path.write_text('# Constitution\n**Status**: Ratified\n')
        with self.assertRaisesRegex(ValueError,'ratification'):proxy.verify(self.root)
        path.unlink();adr=self.root/'docs/architecture/decisions/choice.md';adr.parent.mkdir()
        adr.write_text('# Choice\n- **Status**: Accepted\n')
        with self.assertRaisesRegex(ValueError,'ADR decisions'):proxy.verify(self.root)
    def test_disclosure_and_scenario_drift_remain_failures(self):
        proxy.begin(self.root,'one-round')
        with self.assertRaisesRegex(ValueError,'disclose'):proxy.verify(self.root)
        self.transcript();(self.root/'product-idea.md').write_text('Changed scenario')
        with self.assertRaisesRegex(ValueError,'scenario changed'):proxy.verify(self.root)
    def test_existing_real_intent_cannot_be_relabelled(self):
        path=self.root/'docs/architecture/project-intent.md';path.parent.mkdir(parents=True)
        path.write_text('# Existing product')
        with self.assertRaisesRegex(ValueError,'relabel'):proxy.begin(self.root,'full-intake')
if __name__=='__main__':unittest.main()
