import unittest

from ppt_restore.platform.doctor import doctor


class DoctorTests(unittest.TestCase):
    def test_report_is_json_safe(self):
        report = doctor()
        payload = report.to_dict()
        self.assertIn("renderers", payload)
        self.assertIn("formal_pass", payload["capabilities"])
        self.assertIn("wps_installed", payload["renderers"])
        self.assertIn("wps_headless", payload["renderers"])
        self.assertIn("wps_pdf_import", payload["renderers"])
        self.assertIn("wps_preverify", payload["capabilities"])


if __name__ == "__main__":
    unittest.main()
