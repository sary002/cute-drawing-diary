"""Exercise a diary lifecycle in disposable copies; never mark the real diary complete."""
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts/drawing_diary.py"


class DiaryLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "diary"
        shutil.copytree(PROJECT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.first = self.root / "entries/beginner/001-chick"

    def run_cli(self, *args, ok=True):
        run = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args], text=True, capture_output=True)
        self.assertEqual(run.returncode == 0, ok, run.stdout + run.stderr)
        return run

    def complete(self, *extra):
        return self.run_cli("record", "001-chick", "--date", datetime.date.today().isoformat(), *extra)

    def test_resume_does_not_create_duplicate(self):
        before = (self.first / "entry.json").read_bytes()
        resumed = self.run_cli("next")
        self.assertIn(str(self.root / "lessons/beginner/001-chick.md"), resumed.stdout)
        self.run_cli("next")
        self.assertEqual((self.first / "entry.json").read_bytes(), before)
        self.assertEqual(len(list((self.root / "entries").glob("*/*/entry.json"))), 1)

    def test_completion_needs_no_photo_date_time_or_reflection(self):
        self.run_cli("record", "001-chick")
        p = json.loads((self.first / "entry.json").read_text())["practice"]
        self.assertEqual(p["status"], "completed")
        self.assertIsNone(p["completed_on"])
        self.assertIsNone(p["actual_minutes"])
        self.assertEqual(p["photos"], [])
        self.assertIsNone(p["liked"])
        self.assertIsNone(p["improve"])
        self.run_cli("validate")
        self.run_cli("next")
        self.assertTrue((self.root / "entries/beginner/002-seal/entry.json").is_file())
        second = json.loads((self.root / "entries/beginner/002-seal/entry.json").read_text())
        self.assertEqual(second["lesson_status"], "draft")
        self.assertEqual(second["lesson_path"], "lessons/beginner/002-seal.md")
        self.assertTrue((self.root / second["lesson_path"]).is_file())
        self.assertFalse((self.root / "entries/beginner/002-seal/lesson.md").exists())
        self.run_cli("validate")

    def test_can_add_photo_later_without_rewriting_progress(self):
        self.complete("--minutes", "18", "--liked", "完成了")
        before = json.loads((self.first / "entry.json").read_text())["practice"]
        photo = self.first / "reference/finished.png"  # Test fixture only.
        self.run_cli("add-photo", "001-chick", "--photo", str(photo))
        after = json.loads((self.first / "entry.json").read_text())["practice"]
        for key in ("status", "completed_on", "actual_minutes", "liked", "improve"):
            self.assertEqual(before[key], after[key])
        self.assertEqual(len(after["photos"]), 1)
        self.run_cli("validate")
        self.run_cli("add-photo", "001-chick", "--photo", str(photo), ok=False)

    def test_complete_then_new_entry_and_immutable_history(self):
        old_snapshot = (self.first / "tools.snapshot.json").read_bytes()
        self.complete("--minutes", "23", "--improve", "平涂连续")
        current_path = self.root / "config/tools/touchmark-student-36-v1.json"
        # Simulate a NEW profile; history must retain the original snapshot.
        current = json.loads(current_path.read_text())
        current["id"] = "touchmark-student-36-v2"
        current["markers"]["tip_type"] = "测试笔头"
        (current_path.parent / (current["id"] + ".json")).write_text(json.dumps(current))
        project_path = self.root / "config/project.json"
        project = json.loads(project_path.read_text())
        project["current_tools"] = current["id"]
        project_path.write_text(json.dumps(project))
        self.run_cli("next")
        second = self.root / "entries/beginner/002-seal"
        e = json.loads((second / "entry.json").read_text())
        self.assertEqual(e["tools_profile"], current["id"])
        self.assertEqual(e["practice"]["status"], "pending")
        self.assertEqual(e["references"], [])
        self.assertEqual((self.first / "tools.snapshot.json").read_bytes(), old_snapshot)
        self.run_cli("index")
        self.run_cli("validate")
        self.assertIn("23分钟", (self.root / "entries/INDEX.md").read_text())
        self.assertIn("(../lessons/beginner/001-chick.md)", (self.root / "entries/INDEX.md").read_text())
        self.assertIn("(../lessons/beginner/002-seal.md)", (self.root / "entries/INDEX.md").read_text())

    def test_lesson_path_and_file_are_validated(self):
        path = self.first / "entry.json"
        entry = json.loads(path.read_text())
        original = entry["lesson_path"]
        for invalid in ("../outside.md", "entries/beginner/001-chick/lesson.md",
                        "/tmp/001-chick.md", "lessons/beginner/999-chick.md"):
            with self.subTest(path=invalid):
                entry["lesson_path"] = invalid
                path.write_text(json.dumps(entry))
                self.run_cli("validate", ok=False)
        entry["lesson_path"] = original
        path.write_text(json.dumps(entry))
        (self.root / original).unlink()
        self.run_cli("validate", ok=False)

    def test_next_does_not_overwrite_existing_lesson(self):
        self.complete()
        target = self.root / "lessons/beginner/002-seal.md"
        target.write_text("已有教案，不应被覆盖。")
        self.run_cli("next", ok=False)
        self.assertEqual(target.read_text(), "已有教案，不应被覆盖。")
        self.assertFalse((self.root / "entries/beginner/002-seal").exists())

    def test_photo_original_is_private_and_not_overwritten(self):
        photo = self.root / "entries/beginner/001-chick/reference/finished.png"
        self.complete("--photo", str(photo))  # Fixture only, not a real user practice.
        target = self.first / "practice/private/finished.png"
        self.assertEqual(target.read_bytes(), photo.read_bytes())
        target.unlink()  # Public clone excludes private originals; metadata should still validate.
        self.run_cli("validate")
        self.run_cli("record", "001-chick", "--date", datetime.date.today().isoformat(), ok=False)

    def test_reject_invalid_color_and_future_date(self):
        e_path = self.first / "entry.json"
        original = e_path.read_bytes()
        e = json.loads(original)
        e["marker_colors"] = ["999"]
        e_path.write_text(json.dumps(e))
        self.run_cli("validate", ok=False)
        e_path.write_bytes(original)
        future = datetime.date.today() + datetime.timedelta(days=1)
        self.run_cli("record", "001-chick", "--date", future.isoformat(), ok=False)
        self.assertEqual(e_path.read_bytes(), original)

    def test_photo_path_cannot_escape_entry(self):
        e_path = self.first / "entry.json"
        e = json.loads(e_path.read_text())
        e["practice"]["photos"] = [{"path": "../../../config/project.json", "visibility": "public", "origin": "user_practice"}]
        e_path.write_text(json.dumps(e))
        self.run_cli("validate", ok=False)


if __name__ == "__main__":
    unittest.main()
