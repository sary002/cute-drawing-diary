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
        shutil.copytree(PROJECT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", ".local", "previews", "entries"))
        self.first = self.root / "entries/beginner/001-headphone-mushroom"
        # Copy only the fixture artwork; the growing image library is unrelated to lifecycle tests.
        shutil.copytree(PROJECT / "entries/beginner/001-headphone-mushroom", self.first)
        catalog_path = self.root / "config/styles.json"
        catalog = json.loads(catalog_path.read_text())
        catalog["styles"][0]["curriculum_paths"] = {"beginner": "curriculum/beginner.json"}
        catalog_path.write_text(json.dumps(catalog))
        curriculum_path = self.root / "curriculum/beginner.json"
        curriculum = json.loads(curriculum_path.read_text())
        curriculum_path.write_text(json.dumps([curriculum[0], next(x for x in curriculum if x["slug"] == "seal")]))

    def run_cli(self, *args, ok=True):
        run = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args], text=True, capture_output=True)
        self.assertEqual(run.returncode == 0, ok, run.stdout + run.stderr)
        return run

    def complete(self, *extra):
        return self.run_cli("record", "001-headphone-mushroom", "--date", datetime.date.today().isoformat(), *extra)

    def test_resume_does_not_create_duplicate(self):
        before = (self.first / "entry.json").read_bytes()
        resumed = self.run_cli("next")
        self.assertIn(str(self.root / "lessons/beginner/001-headphone-mushroom.md"), resumed.stdout)
        self.run_cli("next")
        self.assertEqual((self.first / "entry.json").read_bytes(), before)
        self.assertEqual(len(list((self.root / "entries").glob("*/*/entry.json"))), 1)

    def test_unresolved_physical_color_review_cannot_be_ready(self):
        path = self.first / "entry.json"
        entry = json.loads(path.read_text())
        entry["color_review"] = {"status": "requires_revision"}
        entry["lesson_status"] = "ready"
        path.write_text(json.dumps(entry))
        self.assertIn("配色待校正", self.run_cli("validate", ok=False).stderr)
        entry["lesson_status"] = "draft"
        path.write_text(json.dumps(entry))
        before = path.read_bytes()
        self.run_cli("validate")
        self.run_cli("index")
        self.assertIn("配色待校正", (self.root / "entries/INDEX.md").read_text())
        self.assertEqual(path.read_bytes(), before)

    def test_completion_needs_no_photo_date_time_or_reflection(self):
        self.run_cli("record", "001-headphone-mushroom")
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
        self.run_cli("add-photo", "001-headphone-mushroom", "--photo", str(photo))
        after = json.loads((self.first / "entry.json").read_text())["practice"]
        for key in ("status", "completed_on", "actual_minutes", "liked", "improve"):
            self.assertEqual(before[key], after[key])
        self.assertEqual(len(after["photos"]), 1)
        self.run_cli("validate")
        self.run_cli("add-photo", "001-headphone-mushroom", "--photo", str(photo), ok=False)

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
        self.assertIn("(../lessons/beginner/001-headphone-mushroom.md)", (self.root / "entries/INDEX.md").read_text())
        self.assertIn("(../lessons/beginner/002-seal.md)", (self.root / "entries/INDEX.md").read_text())

    def test_lesson_path_and_file_are_validated(self):
        path = self.first / "entry.json"
        entry = json.loads(path.read_text())
        original = entry["lesson_path"]
        for invalid in ("../outside.md", "entries/beginner/001-headphone-mushroom/lesson.md",
                        "/tmp/001-headphone-mushroom.md", "lessons/beginner/999-chick.md"):
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
        photo = self.root / "entries/beginner/001-headphone-mushroom/reference/finished.png"
        self.complete("--photo", str(photo))  # Fixture only, not a real user practice.
        target = self.first / "practice/private/finished.png"
        self.assertEqual(target.read_bytes(), photo.read_bytes())
        target.unlink()  # Public clone excludes private originals; metadata should still validate.
        self.run_cli("validate")
        self.run_cli("record", "001-headphone-mushroom", "--date", datetime.date.today().isoformat(), ok=False)

    def test_reject_invalid_color_and_future_date(self):
        e_path = self.first / "entry.json"
        original = e_path.read_bytes()
        e = json.loads(original)
        e["marker_colors"] = ["999"]
        e_path.write_text(json.dumps(e))
        self.run_cli("validate", ok=False)
        e_path.write_bytes(original)
        future = datetime.date.today() + datetime.timedelta(days=1)
        self.run_cli("record", "001-headphone-mushroom", "--date", future.isoformat(), ok=False)
        self.assertEqual(e_path.read_bytes(), original)

    def test_photo_path_cannot_escape_entry(self):
        e_path = self.first / "entry.json"
        e = json.loads(e_path.read_text())
        e["practice"]["photos"] = [{"path": "../../../config/project.json", "visibility": "public", "origin": "user_practice"}]
        e_path.write_text(json.dumps(e))
        self.run_cli("validate", ok=False)


    def add_style_fixture(self):
        """A synthetic second style exists ONLY inside disposable test copies."""
        path = self.root / "config/styles.json"
        catalog = json.loads(path.read_text())
        catalog["styles"].append({"id": "S999", "slug": "test-landscape", "name": "测试风格",
                                  "profile_path": "styles/test-landscape.md",
                                  "curriculum_paths": {"beginner": "curriculum/S999/beginner.json"}})
        path.write_text(json.dumps(catalog))
        (self.root / "styles/test-landscape.md").write_text("测试档案")
        curriculum = self.root / "curriculum/S999/beginner.json"
        curriculum.parent.mkdir(parents=True)
        # Same slug as S001 intentionally exercises per-style selection.
        curriculum.write_text(json.dumps([{"slug": "headphone-mushroom", "title": "独立测试题",
                                           "goal": "测试远近", "colors": ["44", "67"]}]))
        progress_path = self.root / "config/learning-progress.json"
        progress = json.loads(progress_path.read_text())
        progress["styles"]["S999"] = {"current_stage": "beginner", "teaching_mode": "supported", "reviews": []}
        progress_path.write_text(json.dumps(progress))

    def test_styles_resume_and_select_topics_independently(self):
        self.add_style_fixture()
        old_entry = (self.first / "entry.json").read_bytes()
        self.run_cli("next", "--style", "S999")
        new_folder = self.root / "entries/beginner/002-headphone-mushroom"
        created = json.loads((new_folder / "entry.json").read_text())
        self.assertEqual(created["style_id"], "S999")
        self.assertEqual(created["teaching_mode"], "supported")
        self.assertEqual(created["marker_colors"], ["44", "67"])
        self.assertIn("002-headphone-mushroom.md", self.run_cli("next", "--style", "S999").stdout)
        self.assertIn("001-headphone-mushroom.md", self.run_cli("next", "--style", "S001").stdout)
        self.assertEqual((self.first / "entry.json").read_bytes(), old_entry)
        self.run_cli("validate")

    def test_explicit_new_keeps_pending_history_and_mode_override(self):
        old_entry = (self.first / "entry.json").read_bytes()
        self.run_cli("next", "--style", "S001", "--new", "--teaching-mode", "supported")
        second = json.loads((self.root / "entries/beginner/002-seal/entry.json").read_text())
        self.assertEqual(second["style_id"], "S001")
        self.assertEqual(second["teaching_mode"], "supported")
        self.assertEqual((self.first / "entry.json").read_bytes(), old_entry)
        self.assertEqual(json.loads((self.root / "config/learning-progress.json").read_text())["styles"]["S001"]["teaching_mode"], "guided")
        self.run_cli("validate")

    def test_missing_style_course_never_falls_back_to_s001(self):
        self.add_style_fixture()
        path = self.root / "config/styles.json"
        catalog = json.loads(path.read_text())
        catalog["styles"][1]["curriculum_paths"] = {}
        path.write_text(json.dumps(catalog))
        result = self.run_cli("next", "--style", "S999", ok=False)
        self.assertIn("尚无题库", result.stderr)
        self.assertEqual(len(list((self.root / "entries").glob("*/*/entry.json"))), 1)

    def test_unknown_style_does_not_create_or_register_it(self):
        before = (self.root / "config/styles.json").read_bytes()
        self.run_cli("next", "--style", "S002", ok=False)
        self.assertEqual((self.root / "config/styles.json").read_bytes(), before)
        self.assertEqual(len(list((self.root / "entries").glob("*/*/entry.json"))), 1)

    def test_review_advances_only_selected_style_and_preserves_old_work(self):
        self.add_style_fixture()
        self.run_cli("next", "--style", "S999")
        self.run_cli("record", "002-headphone-mushroom")
        before = (self.root / "entries/beginner/002-headphone-mushroom/entry.json").read_bytes()
        self.run_cli("review", "--style", "S999", "--decision", "advance", "--evidence", "大形和色块已可独立完成")
        progress = json.loads((self.root / "config/learning-progress.json").read_text())["styles"]
        self.assertEqual(progress["S999"]["current_stage"], "intermediate")
        self.assertEqual(progress["S001"]["current_stage"], "beginner")
        self.assertEqual((self.root / "entries/beginner/002-headphone-mushroom/entry.json").read_bytes(), before)
        # An old-stage pending piece must not hijack the selected next stage.
        entry = json.loads(before)
        entry["number"] = 3
        entry["lesson_path"] = "lessons/beginner/003-headphone-mushroom.md"
        entry["practice"]["status"] = "pending"
        pending = self.root / "entries/beginner/003-headphone-mushroom"
        shutil.copytree(self.root / "entries/beginner/002-headphone-mushroom", pending)
        (pending / "entry.json").write_text(json.dumps(entry))
        (self.root / entry["lesson_path"]).write_text("测试未完成旧作")
        self.assertIn("尚无题库", self.run_cli("next", "--style", "S999", ok=False).stderr)
        self.run_cli("validate")

    def test_review_rejects_uncompleted_or_blank_evidence(self):
        path = self.root / "config/learning-progress.json"
        before = path.read_bytes()
        self.run_cli("review", "--decision", "advance", "--evidence", "只有AI示意", ok=False)
        self.complete()
        self.run_cli("review", "--decision", "advance", "--evidence", "  ", ok=False)
        self.assertEqual(path.read_bytes(), before)

    def test_seven_completed_prompt_review_without_auto_promotion(self):
        self.complete()
        first_entry = json.loads((self.first / "entry.json").read_text())
        for number in range(2, 8):
            folder = self.root / f"entries/beginner/{number:03d}-headphone-mushroom"
            shutil.copytree(self.first, folder)
            entry = dict(first_entry, number=number, lesson_path=f"lessons/beginner/{number:03d}-headphone-mushroom.md")
            (folder / "entry.json").write_text(json.dumps(entry))
            (self.root / entry["lesson_path"]).write_text("测试完成记录")
        path = self.root / "config/learning-progress.json"
        before = path.read_bytes()
        self.assertIn("已到复盘点", self.run_cli("status", "--style", "S001").stdout)
        self.run_cli("next")
        self.assertEqual(path.read_bytes(), before)
        self.run_cli("review", "--decision", "practice", "--evidence", "需要补两幅边界控制练习")
        state = json.loads(path.read_text())["styles"]["S001"]
        self.assertEqual(state["current_stage"], "beginner")
        self.assertEqual(state["reviews"][-1]["next_review_at"], 9)
        self.assertNotIn("已到复盘点", self.run_cli("status", "--style", "S001").stdout)
        self.run_cli("validate")

    def test_unclassified_history_is_visible_without_inheriting_default_style(self):
        path = self.first / "entry.json"
        entry = json.loads(path.read_text())
        entry.pop("style_id")
        entry["practice"]["status"] = "completed"
        path.write_text(json.dumps(entry))
        before = path.read_bytes()
        self.assertIn("历史风格未分类", self.run_cli("status").stdout)
        self.assertIn("当前阶段真实完成0幅", self.run_cli("status", "--style", "S001").stdout)
        self.assertNotIn("001-headphone-mushroom", self.run_cli("status", "--style", "S001").stdout)
        self.run_cli("validate")
        self.assertEqual(path.read_bytes(), before)

    def test_validator_rejects_shared_curriculum_and_unknown_style_record(self):
        self.add_style_fixture()
        path = self.root / "config/styles.json"
        before = path.read_bytes()
        catalog = json.loads(before)
        catalog["styles"][1]["curriculum_paths"]["beginner"] = "curriculum/beginner.json"
        path.write_text(json.dumps(catalog))
        self.assertIn("不得共享", self.run_cli("validate", ok=False).stderr)
        path.write_bytes(before)
        entry_path = self.first / "entry.json"
        entry = json.loads(entry_path.read_text())
        entry["style_id"] = "S888"
        entry_path.write_text(json.dumps(entry))
        self.assertIn("作品风格不存在", self.run_cli("validate", ok=False).stderr)


if __name__ == "__main__":
    unittest.main()
