"""Release eligibility tests; all reports and PDF hashes below are fixtures."""
import copy
import hashlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from release_gate import GATES, eligible_releases, release_fingerprint


BUILD = "2.9.31.29434"
NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
PDF_HASH = hashlib.sha256(b"fixture PDF").hexdigest()


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gate-test-", dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "evidence").mkdir()
        self.record = self.make_record()

    def sign(self, record):
        record["approval"]["release_fingerprint"] = release_fingerprint(record)
        return record

    def make_record(self, version="1.0.0", guide="fa18c-navigation"):
        report_path = f"evidence/{guide}-{version}.md"
        body = f"# Test fixture\nDCS {BUILD}\nPDF {PDF_HASH}\nApproved by Wattl\n"
        raw = body.encode("utf-8")
        (self.root / report_path).write_bytes(raw)
        return self.sign({
            "guide_id": guide, "title": "F/A-18C Navigation", "module": "F/A-18C",
            "version": version, "gates": {key: "passed" for key in GATES},
            "artifacts": [{"filename": "guide.pdf", "label": "Bildschirmfassung", "bytes": 123,
                           "sha256": PDF_HASH,
                           "url": f"https://github.com/Wattl/Project-X-Guides/releases/download/{guide}-v{version}/guide.pdf"}],
            "verification": {"status": "passed", "runtime_tested": True,
                             "dcs_build": BUILD, "tested_at": "2026-11-01T10:00:00Z",
                             "report": {"path": report_path, "sha256": hashlib.sha256(raw).hexdigest()}},
            "rights": {"status": "cleared", "reviewed_by": "Wattl", "reviewed_at": "2026-11-01"},
            "approval": {"status": "approved", "approved_by": "Wattl", "approved_at": "2026-11-02T09:00:00+01:00"},
        })

    def check(self, records=None, build=BUILD):
        return eligible_releases({"schema_version": 1, "releases": records if records is not None else [self.record]},
                                 build, self.root, NOW)

    def reject(self, term):
        eligible, exclusions = self.check()
        self.assertEqual(eligible, [])
        self.assertEqual(len(exclusions), 1)
        self.assertIn(term, exclusions[0]["reason"])

    def test_complete_release_is_eligible(self):
        self.assertEqual(self.check(), ([self.record], []))

    def test_empty_catalog_has_no_downloads(self):
        self.assertEqual(self.check([]), ([], []))

    def test_draft_is_not_released(self):
        self.record["approval"]["status"] = "draft"
        self.reject("not approved")

    def test_other_approver_cannot_release(self):
        self.record["approval"]["approved_by"] = "another-person"
        self.reject("not approved")

    def test_static_check_cannot_substitute_runtime_test(self):
        self.record["verification"]["runtime_tested"] = False
        self.sign(self.record)
        self.reject("practical DCS test")

    def test_runtime_flag_must_be_boolean(self):
        self.record["verification"]["runtime_tested"] = "true"
        self.sign(self.record)
        self.reject("practical DCS test")

    def test_new_dcs_build_withdraws_download(self):
        eligible, exclusions = self.check(build="2.9.32.10000")
        self.assertEqual(eligible, [])
        self.assertIn("current DCS build", exclusions[0]["reason"])

    def test_unknown_build_never_reuses_previous_release(self):
        for build in [None, "", "unknown", "2.9.31", "2.9.31.29434\n"]:
            with self.subTest(build=build):
                result, reasons = self.check(build=build)
                self.assertEqual(result, [])
                self.assertIn("unknown", reasons[0]["reason"])

    def test_changed_artifact_invalidates_approval(self):
        self.record["artifacts"][0]["bytes"] += 1
        self.reject("exact release")

    def test_changed_metadata_invalidates_approval(self):
        self.record["title"] = "Changed title"
        self.reject("exact release")

    def test_pdf_publication_size_limit(self):
        self.record["artifacts"][0]["bytes"] = 80_000_001
        self.sign(self.record)
        self.reject("80,000,000")

    def test_unknown_rights_block_release(self):
        self.record["rights"]["status"] = "unknown"
        self.sign(self.record)
        self.reject("rights")

    def test_open_gate_blocks_release(self):
        self.record["gates"]["red_team"] = "open"
        self.sign(self.record)
        self.reject("workflow gates")

    def test_future_test_date_blocks_release(self):
        self.record["verification"]["tested_at"] = "2027-01-01"
        self.sign(self.record)
        self.reject("future")

    def test_approval_cannot_predate_test(self):
        self.record["approval"]["approved_at"] = "2026-10-30"
        self.reject("predates")

    def test_naive_datetime_is_rejected(self):
        self.record["verification"]["tested_at"] = "2026-11-01T10:00:00"
        self.sign(self.record)
        self.reject("ISO date/timestamp")

    def test_missing_report_blocks_release(self):
        (self.root / self.record["verification"]["report"]["path"]).unlink()
        self.reject("missing")

    def test_report_modification_is_detected(self):
        (self.root / self.record["verification"]["report"]["path"]).write_text("Changed", encoding="utf-8")
        self.reject("hash does not match")

    def test_report_must_name_tested_artifacts(self):
        path = self.root / self.record["verification"]["report"]["path"]
        raw = f"DCS {BUILD}; approved by Wattl; no artifact identity".encode()
        path.write_bytes(raw)
        self.record["verification"]["report"]["sha256"] = hashlib.sha256(raw).hexdigest()
        self.sign(self.record)
        self.reject("every artifact SHA-256")

    def test_traversal_cannot_read_outside_evidence(self):
        for path in ["evidence/../secret.md", "../evidence/test.md", "C:/secret.md", "evidence\\test.md", "evidence//test.md"]:
            with self.subTest(path=path):
                self.record["verification"]["report"]["path"] = path
                self.sign(self.record)
                self.reject("under evidence")

    def test_symlink_cannot_escape_evidence(self):
        external = self.root / "outside.md"
        external.write_text("outside", encoding="utf-8")
        linked = self.root / "evidence/linked.md"
        try:
            linked.symlink_to(external)
        except OSError:
            self.skipTest("Platform does not permit symlinks for this user")
        self.record["verification"]["report"]["path"] = "evidence/linked.md"
        self.sign(self.record)
        self.reject("escapes evidence")

    def test_only_own_repository_release_urls_allowed(self):
        urls = [
            "https://github.com/other/repo/releases/download/v1/guide.pdf",
            "http://github.com/Wattl/Project-X-Guides/releases/download/v1/guide.pdf",
            "https://github.com.evil.example/Wattl/Project-X-Guides/releases/download/v1/guide.pdf",
            "https://github.com/Wattl/Project-X-Guides/releases/download/v1/guide.pdf?redirect=x",
            "https://github.com/Wattl/Project-X-Guides/releases/download/../guide.pdf",
            "https://github.com/Wattl/Project-X-Guides/releases/download/v1/%67uide.pdf",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.record["artifacts"][0]["url"] = url
                self.sign(self.record)
                eligible, reasons = self.check()
                self.assertEqual(eligible, [])
                self.assertTrue(reasons)

    def test_path_and_duplicate_artifact_names_rejected(self):
        self.record["artifacts"][0]["filename"] = "../guide.pdf"
        self.sign(self.record)
        self.reject("safe PDF basename")
        self.record["artifacts"][0]["filename"] = "guide.pdf"
        self.record["artifacts"].append(copy.deepcopy(self.record["artifacts"][0]))
        self.sign(self.record)
        self.reject("Duplicate artifact")

    def test_latest_eligible_version_is_numeric(self):
        older = self.make_record("1.9.0")
        latest = self.make_record("1.10.0")
        eligible, exclusions = self.check([latest, older, self.record])
        self.assertEqual(eligible, [latest])
        self.assertEqual(len(exclusions), 2)

    def test_unapproved_newer_version_does_not_replace_approved_one(self):
        newer = self.make_record("2.0.0")
        newer["approval"]["status"] = "pending"
        eligible, exclusions = self.check([self.record, newer])
        self.assertEqual(eligible, [self.record])
        self.assertIn("not approved", exclusions[0]["reason"])

    def test_duplicate_identity_excludes_both_copies(self):
        eligible, exclusions = self.check([self.record, copy.deepcopy(self.record)])
        self.assertEqual(eligible, [])
        self.assertEqual(len(exclusions), 2)
        self.assertTrue(all("Duplicate guide/version" in reason["reason"] for reason in exclusions))

    def test_separate_guides_keep_their_latest_eligible_release(self):
        other = self.make_record("1.0.0", "bfm-acm")
        eligible, exclusions = self.check([self.record, other])
        self.assertEqual([entry["guide_id"] for entry in eligible], ["bfm-acm", "fa18c-navigation"])
        self.assertEqual(exclusions, [])

    def test_malformed_records_fail_closed(self):
        eligible, exclusions = self.check([None, [], "record", {}, {"guide_id": []}])
        self.assertEqual(eligible, [])
        self.assertEqual(len(exclusions), 5)

    def test_malformed_catalogue_raises(self):
        for catalog in [None, {}, {"schema_version": True, "releases": []}, {"schema_version": 1, "releases": {}}]:
            with self.subTest(catalog=catalog), self.assertRaises(ValueError):
                eligible_releases(catalog, BUILD, self.root, NOW)

    def test_fingerprint_ignores_approval_but_binds_all_other_fields(self):
        before = release_fingerprint(self.record)
        self.record["approval"]["approved_at"] = "2026-11-02"
        self.assertEqual(before, release_fingerprint(self.record))
        self.record["module"] = "another module"
        self.assertNotEqual(before, release_fingerprint(self.record))


if __name__ == "__main__":
    unittest.main()
