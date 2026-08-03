from datetime import date
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from report_mailer import report_text, write_pdf


class ReportPdfTest(unittest.TestCase):
    def test_generated_report_has_pdf_header_and_conclusion(self) -> None:
        text = report_text(date(2026, 7, 31))
        self.assertIn("Conclusion:", text)
        with TemporaryDirectory() as directory:
            report = write_pdf(text, Path(directory) / "report.pdf")
            self.assertTrue(report.read_bytes().startswith(b"%PDF-1.4"))


if __name__ == "__main__":
    unittest.main()
