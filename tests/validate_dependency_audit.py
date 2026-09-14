"""Dependency evidence stays immutable and cannot become a hidden application target."""
from __future__ import annotations
import contextlib
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import dependency_audit as audit
import bootstrap_lifecycle as lifecycle
import package_execution
import implementation_preflight as preflight
import sync_readiness
from validate_building_blocks import load_module, accepted_fixture, write_json, RESOLVER, CATALOG
from validate_governance_state import roadmap


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='program-kit-dependency-audit-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.blocks = load_module(RESOLVER)
        self.catalog = self.blocks.load_json(CATALOG)
        self.selection, _ = accepted_fixture(self.blocks, self.root, self.catalog)

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, str):
            path.write_text(value, encoding='utf-8')
        else:
            write_json(path, value)
        return path

    def proof(self):
        architecture_path = self.root / 'docs/architecture/architecture-map.json'
        architecture = audit.read(architecture_path)
        architecture['decisions'][0]['path'] = 'docs/architecture/decisions/use-building-blocks.md'
        self.write(architecture['decisions'][0]['path'], '# Use building blocks\nStatus: Accepted\n')
        write_json(architecture_path, architecture)
        source = self.write('docs/proof/Probe.csproj', '<Project><ItemGroup><PackageReference Include="Orbyss.Foundation.Tasks" /></ItemGroup></Project>')
        self.write('docs/architecture/bootstrap-decisions.json', {'unresolved': [], 'deferred': []})
        self.write('docs/architecture/specification-roadmap.md', roadmap())
        result = self.write('.specify/governance/proof/results.xml', '<testsuite><testcase name="ok" /></testsuite>')
        stdout = self.write('.specify/governance/proof/stdout', '')
        stderr = self.write('.specify/governance/proof/stderr', '')
        bound = lambda p: {'path': p.relative_to(self.root).as_posix(), 'sha256': audit.sha(p)}
        proof = self.write('.specify/governance/proof/proof.json', {
            'schema_version': '1.1', 'prerequisite': 'probe', 'exit_code': 0,
            'command': ['deterministic-unit-fixture'], 'checks': ['ok'], 'test_result': bound(result),
            'tooling_sources': lifecycle.proof_tooling(), 'inputs': [bound(source)],
            'streams': [bound(stdout), bound(stderr)],
            'design_sources': {p: lifecycle.design_digest(self.root / p) for p in
                ['docs/architecture/bootstrap-decisions.json', 'docs/architecture/building-block-selection.json']}})
        self.write('docs/architecture/bootstrap-prerequisites.json', {
            'schema_version': '1.0', 'sources': [{'path': p, 'sha256': lifecycle.source_digest(self.root / p), 'prerequisites': ['probe']}
                for p in lifecycle.source_paths(self.root)],
            'prerequisites': [{'id': 'probe', 'source_ids': ['probe'], 'affected_slices': ['SPEC-001'],
                'disposition': 'architecture', 'trigger': 'before-implementation', 'owner': 'test',
                'task': 'unit fixture', 'rationale': 'unit fixture', 'status': 'closed',
                'evidence': [bound(proof) | {'kind': 'compatibility'}]}]})
        return source

    def run_audit(self, lock=None):
        self.blocks.audit_unmanaged_dependencies(self.root, self.catalog, lock)

    def test_first_materialization_repeat_and_contextmanager_rollback(self):
        source = self.proof()
        protected = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file() and ('docs' in p.parts or '.specify' in p.parts)}
        plan = self.blocks.resolve(self.root, self.selection, CATALOG, '0.12.0')
        lockpath = self.root / '.program-kit/building-blocks.lock.json'
        with patch.dict('os.environ', {'PROGRAMKIT_TEST_BUILDING_BLOCK_FAIL_AFTER_ACTION': '1'}):
            with self.assertRaises(OSError):
                self.blocks.apply_materialization(self.root, lockpath, plan, self.catalog)
        self.assertFalse(lockpath.exists())
        self.blocks.apply_materialization(self.root, lockpath, plan, self.catalog)
        written = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.blocks.apply_materialization(self.root, lockpath, plan, self.catalog)
        self.assertEqual(written, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertTrue(all(p.read_bytes() == data for p, data in protected.items()))
        @contextlib.contextmanager
        def boundary():
            yield
        source.write_text(source.read_text() + ' ')
        with self.assertRaisesRegex(self.blocks.ResolverError, 'PKB405.*inputs/streams changed'):
            with boundary():
                self.run_audit(plan)

    def test_no_blanket_exemption_and_active_project_import_links_rejected(self):
        proof = self.proof()
        self.run_audit()
        extra = self.write('docs/Other.csproj', '<Project><PackageReference Include="Orbyss.Foundation.Tasks" /></Project>')
        with self.assertRaisesRegex(self.blocks.ResolverError, 'unmanaged NuGet'):
            self.run_audit()
        extra.unlink()
        for element in ['ProjectReference Include', 'Import Project']:
            path = self.write('consumer.csproj', f'<Project><{element}="docs/proof/Probe.csproj" /></Project>')
            with self.assertRaisesRegex(self.blocks.ResolverError, 'active MSBuild'):
                self.run_audit()
            path.unlink()
        with self.assertRaisesRegex(ValueError, 'active dependency target'):
            audit.reject_active_references(self.root, {proof.resolve()}, {'targets': [{'path': 'docs/proof/Probe.csproj'}]})
        for name, content in [('consumer.sln', 'Project("{ID}") = "Probe", "docs/proof/Probe.csproj", "{GUID}"'),
                              ('consumer.slnx', '<Solution><Project Path="docs/proof/Probe.csproj" /></Solution>')]:
            path = self.write(name, content)
            with self.assertRaisesRegex(self.blocks.ResolverError, 'active solution'):
                self.run_audit()
            path.unlink()
        self.write('specs/001-feature/artifact-ownership.json', {'runtimeComposition': {'projects': [{'path': 'docs/proof/Probe.csproj'}]}})
        with self.assertRaisesRegex(self.blocks.ResolverError, 'active runtime project'):
            self.run_audit()

    def test_engineering_ownership_requires_receipt_template_and_actual_hash(self):
        command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
            '--target', str(self.root), '--profile-selected', '--foundation-host-accepted',
            '--building-block-sources-approved', '--web-profile', 'none']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(2, len(audit.engineering_outputs(self.root)))
        for relative in ['.program-kit/eng/.config/dotnet-tools.json', '.program-kit/eng/ProgramKit.Packages.props']:
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.assertRaisesRegex(ValueError, 'ownership hash changed'):
                audit.engineering_outputs(self.root)
            path.write_bytes(original)
        state = self.root / '.program-kit/managed.json'
        state.unlink()
        with self.assertRaisesRegex(ValueError, 'no installed ownership'):
            audit.engineering_outputs(self.root)

    def test_strict_candidate_excluded_from_restore_but_not_linkable(self):
        candidate = self.write('specs/001-feature/dependencies/package.json', {'dependencies': {'@orbyss/forms-react': '0.2.0'}})
        self.write('.program-kit/evidence/toolchain.json', {'required': {}, 'resolved': {}, 'commands': {}, 'satisfied': True})
        context = package_execution.context_proof(self.root, self.root / '.program-kit/evidence/toolchain.json', ['@orbyss/forms-react'])
        lock = {'lockfileVersion': 3, 'packages': {'': {'dependencies': {'@orbyss/forms-react': '0.2.0'}}}}
        self.write('.program-kit/evidence/npm-graph.json', {'satisfied': True, 'packageJson': candidate.relative_to(self.root).as_posix(),
            'packageJsonSha256': audit.sha(candidate), 'lockfile': lock, 'lockfileSha256': package_execution.canonical_hash(lock), 'executionContext': context})
        self.write('specs/001-feature/artifact-ownership.json', {'artifacts': [{'pattern': 'specs/001-feature/**'}, {'path': 'web/package.json'}]})
        self.run_audit()
        self.assertEqual(['web/package.json'], sync_readiness.owned_targets(self.root, 'specs/001-feature', []))
        for manifest in [{'dependencies': {'candidate': 'file:specs/001-feature/dependencies'}}, {'workspaces': ['specs/*/dependencies']}]:
            path = self.write('package.json', manifest)
            with self.assertRaisesRegex(self.blocks.ResolverError, 'active npm'):
                self.run_audit()
            path.unlink()
        candidate.write_text('{}')
        with self.assertRaisesRegex(self.blocks.ResolverError, 'candidate manifest changed'):
            self.run_audit()

    def test_planned_catalog_references_need_exact_target_binding(self):
        self.assertEqual([], audit.planned_selection_errors(self.root, [{'path': 'src/Test.Feature/Test.Feature.csproj', 'packageReferences': ['Orbyss.Foundation.DomainEvents']}]))
        errors = audit.planned_selection_errors(self.root, [{'path': 'tests/Tests.csproj', 'packageReferences': ['Orbyss.Foundation.Tasks', 'Orbyss.Foundation.Analyzers']}])
        self.assertTrue(errors and 'PKA016' in errors[0])

    def test_setup_and_source_preflight_have_distinct_required_gates(self):
        feature = self.root / 'specs/001-feature'
        self.write('specs/001-feature/artifact-ownership.json', {})
        for stage in ['setup', 'source']:
            calls = []
            with patch.object(sys, 'argv', ['preflight', '--repository', str(self.root), '--feature-dir', str(feature), '--stage', stage]), patch.object(preflight, 'run', side_effect=lambda cmd, root: calls.append(cmd) or 0), patch.object(audit, 'planned_selection_errors', return_value=[]):
                self.assertEqual(0, preflight.main())
            ownership = next(c for c in calls if any('artifact_ownership.py' in arg for arg in c))
            self.assertEqual(stage == 'setup', '--design-only' in ownership)
            gates = [c for c in calls if '--phase' in c]
            self.assertEqual(['after-plan', 'after-plan'] if stage == 'setup' else ['implementation', 'implementation'], [c[c.index('--phase') + 1] for c in gates])


if __name__ == '__main__':
    unittest.main()
