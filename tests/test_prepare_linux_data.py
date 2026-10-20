import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare-linux-data.py"
SPEC = importlib.util.spec_from_file_location("prepare_linux_data", SCRIPT)
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class PrepareLinuxDataTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="media-data-plan-")
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name).resolve()
        self.repo = self.base / "source"
        self.data = self.base / "data"
        self.repo.mkdir()
        self.data.mkdir()

    def test_plan_lists_exact_eight_links_without_writes(self):
        plan = prepare.prepare_data(self.repo, self.data)
        self.assertEqual(plan["mode"], "plan")
        self.assertEqual(
            tuple(operation["name"] for operation in plan["operations"]),
            ("models", "cache", "temp", "input", "output", "projects", "user", "logs"),
        )
        self.assertEqual(list(self.repo.iterdir()), [])
        self.assertEqual(list(self.data.iterdir()), [])

    def test_existing_target_directories_are_preserved_in_plan(self):
        for name in prepare.DATA_NAMES:
            (self.data / name).mkdir()
        marker = self.data / "models" / "keep.txt"
        marker.write_text("preserve", encoding="utf-8")
        plan = prepare.build_plan(self.repo, self.data)
        self.assertTrue(all(
            operation["target_action"] == "use_existing_directory"
            for operation in plan["operations"]
        ))
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_data_directory_is_required_by_cli(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                prepare.main([])
        self.assertEqual(error.exception.code, 2)

    def test_relative_data_directory_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "absolute"):
            prepare.build_plan(self.repo, Path("relative-data"))

    def test_nonexistent_data_directory_is_rejected_without_creation(self):
        missing = self.base / "missing"
        with self.assertRaisesRegex(ValueError, "existing ordinary"):
            prepare.build_plan(self.repo, missing)
        self.assertFalse(missing.exists())

    def test_data_file_is_rejected(self):
        data_file = self.base / "file"
        data_file.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "existing ordinary"):
            prepare.build_plan(self.repo, data_file)
        self.assertEqual(data_file.read_text(encoding="utf-8"), "keep")

    def test_filesystem_root_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "filesystem root or system"):
            prepare.build_plan(self.repo, Path(self.base.anchor))

    def test_data_directory_cannot_equal_repository(self):
        with self.assertRaisesRegex(ValueError, "equal or be inside"):
            prepare.build_plan(self.repo, self.repo)

    def test_repository_cannot_be_inside_data_directory(self):
        with self.assertRaisesRegex(ValueError, "separate, non-nested"):
            prepare.build_plan(self.repo, self.base)

    def test_data_directory_cannot_be_inside_repository(self):
        child = self.repo / "data"
        child.mkdir()
        with self.assertRaisesRegex(ValueError, "equal or be inside"):
            prepare.build_plan(self.repo, child)
        self.assertEqual(list(child.iterdir()), [])

    def test_source_file_conflict_does_not_create_any_target(self):
        conflict = self.repo / "logs"  # Last pair ensures complete preflight.
        conflict.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "refusing to replace"):
            prepare.build_plan(self.repo, self.data)
        self.assertEqual(list(self.data.iterdir()), [])
        self.assertEqual(conflict.read_text(encoding="utf-8"), "keep")

    def test_even_empty_source_directory_is_a_conflict(self):
        (self.repo / "models").mkdir()
        with self.assertRaisesRegex(ValueError, "refusing to replace"):
            prepare.build_plan(self.repo, self.data)
        self.assertTrue((self.repo / "models").is_dir())
        self.assertEqual(list(self.data.iterdir()), [])

    def test_target_file_is_a_conflict(self):
        target = self.data / "logs"
        target.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ordinary directory"):
            prepare.build_plan(self.repo, self.data)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_data_target_cannot_contain_repository(self):
        parent = self.base / "shared"
        parent.mkdir()
        nested_repo = parent / "models"
        nested_repo.mkdir()
        with self.assertRaises(ValueError):
            prepare.build_plan(nested_repo, parent)
        self.assertEqual(list(nested_repo.iterdir()), [])

    def test_common_system_directory_is_rejected(self):
        system = Path("/etc") if os.name == "posix" else Path(os.environ["SystemRoot"])
        if not system.is_dir():
            self.skipTest("system directory is unavailable")
        with self.assertRaisesRegex(ValueError, "system path"):
            prepare.build_plan(self.repo, system)

    @unittest.skipUnless(os.name == "nt", "Windows-specific apply guard")
    def test_windows_apply_is_rejected_without_writes(self):
        with self.assertRaisesRegex(ValueError, "POSIX"):
            prepare.prepare_data(self.repo, self.data, apply=True)
        self.assertEqual(list(self.repo.iterdir()), [])
        self.assertEqual(list(self.data.iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "POSIX symlink behavior")
    def test_same_source_link_is_idempotent_in_plan(self):
        (self.repo / "models").symlink_to(self.data / "models", target_is_directory=True)
        plan = prepare.build_plan(self.repo, self.data)
        self.assertEqual(plan["operations"][0]["link_action"], "already_linked")
        self.assertFalse((self.data / "models").exists())

    @unittest.skipUnless(os.name == "posix", "POSIX symlink behavior")
    def test_source_link_to_other_target_is_rejected(self):
        (self.repo / "models").symlink_to(self.base / "elsewhere", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "points elsewhere"):
            prepare.build_plan(self.repo, self.data)
        self.assertEqual(list(self.data.iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "POSIX symlink behavior")
    def test_target_symlink_escape_is_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.data / "models").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "escapes"):
            prepare.build_plan(self.repo, self.data)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual(list(self.repo.iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "POSIX symlink behavior")
    def test_target_symlink_inside_data_directory_is_also_rejected(self):
        actual = self.data / "actual"
        actual.mkdir()
        (self.data / "models").symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "must not be a symbolic link"):
            prepare.build_plan(self.repo, self.data)

    @unittest.skipUnless(os.name == "posix", "POSIX apply cannot be verified on Windows")
    def test_apply_creates_links_and_is_idempotent(self):
        first = prepare.prepare_data(self.repo, self.data, apply=True)
        self.assertEqual(first["mode"], "applied")
        for name in prepare.DATA_NAMES:
            self.assertTrue((self.data / name).is_dir())
            self.assertTrue((self.repo / name).is_symlink())
            self.assertEqual((self.repo / name).resolve(), self.data / name)
        second = prepare.prepare_data(self.repo, self.data, apply=True)
        self.assertTrue(all(
            operation["link_action"] == "already_linked"
            and operation["target_action"] == "use_existing_directory"
            for operation in second["operations"]
        ))

    @unittest.skipUnless(os.name == "posix", "POSIX apply cannot be verified on Windows")
    def test_apply_preflights_all_conflicts_before_any_write(self):
        (self.repo / "logs").mkdir()
        with self.assertRaisesRegex(ValueError, "refusing to replace"):
            prepare.prepare_data(self.repo, self.data, apply=True)
        self.assertEqual(list(self.data.iterdir()), [])
        self.assertEqual([entry.name for entry in self.repo.iterdir()], ["logs"])


if __name__ == "__main__":
    unittest.main()
