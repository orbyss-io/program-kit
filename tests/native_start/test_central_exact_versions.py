"""NuGet singleton brackets are exact pins; flexible ranges remain unsupported."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
from central_packages import central_package_versions


class CentralExactVersionTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[2] / 'artifacts/cache/central-pin-tests'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def pins(self, version):
        (self.root / 'Directory.Packages.props').write_text(
            f'<Project><ItemGroup><PackageVersion Include="Exact.Package" Version="{version}" /></ItemGroup></Project>', encoding='utf-8')
        return central_package_versions(self.root)

    def test_plain_literal_preserved(self):
        self.assertEqual({'exact.package': '10.0.12'}, self.pins('10.0.12'))

    def test_singleton_exact_version_preserved(self):
        self.assertEqual({'exact.package': '10.0.12'}, self.pins('[10.0.12]'))

    def test_singleton_prerelease_preserved(self):
        self.assertEqual({'exact.package': '2.9.0-beta.1'}, self.pins('[2.9.0-beta.1]'))

    def test_flexible_or_evaluated_versions_remain_rejected(self):
        for version in ('[10.0.12,)', '[10.0.12,11.0.0)', '(10.0.12)', '10.*', '$(SdkVersion)', '[10.*]', '[[10.0.12]]'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.pins(version)


if __name__ == '__main__':
    unittest.main()
