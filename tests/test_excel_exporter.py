from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from quality_agent.excel_exporter import export_test_cases_to_excel


class ExcelExporterTest(unittest.TestCase):
    def test_exports_xlsx_file(self):
        result = {
            "summary": "Login",
            "test_cases": [
                {
                    "title": "Successful login",
                    "category": "positive",
                    "priority": "P1",
                    "preconditions": ["User exists"],
                    "steps": ["Open login page", "Submit credentials"],
                    "expected_result": "User reaches dashboard",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cases.xlsx"
            export_test_cases_to_excel(result, output_path)

            self.assertTrue(output_path.exists())
            with ZipFile(output_path) as workbook:
                names = workbook.namelist()
                self.assertIn("xl/worksheets/sheet1.xml", names)
                sheet = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
                self.assertIn("Successful login", sheet)


if __name__ == "__main__":
    unittest.main()
