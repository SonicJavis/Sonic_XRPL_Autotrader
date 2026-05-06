import unittest
from security.secret_scanner import scan_for_secrets


class SecurityScanTest(unittest.TestCase):
    def test_secret_scanner_runs(self):
        # Smoke test: the scanner should run without raising.
        findings = scan_for_secrets(".")
        self.assertIsInstance(findings, list)


if __name__ == "__main__":
    unittest.main()
