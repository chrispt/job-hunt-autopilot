import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import userdata

FILES = ["context/candidate-profile.md", "data/screens.json", "data/notion.json"]


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


class Env(unittest.TestCase):
    """A fake Claude home: <home>/plugins/cache/<marketplace>/job-search-agent/<version>/ roots
    and <home>/plugins/data/job-search-agent-<marketplace>/ as the persistent folder."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = self._tmp.name
        self.old_env = {k: os.environ.pop(k, None) for k in ("CLAUDE_PLUGIN_DATA", "JOB_SEARCH_DATA_DIR")}
        self.data = os.path.join(self.home, "plugins", "data", "job-search-agent-mkt")

    def tearDown(self):
        for k, v in self.old_env.items():
            if v is not None:
                os.environ[k] = v
        self._tmp.cleanup()

    def root(self, version, templates=None, with_list=True):
        r = os.path.join(self.home, "plugins", "cache", "mkt", "job-search-agent", version)
        templates = templates or {}
        for rel in FILES:
            write(os.path.join(r, rel), templates.get(rel, f"template {rel}"))
        if with_list:
            write(os.path.join(r, "data", "userdata-files.json"), json.dumps({"files": FILES}))
        return r


class DataDir(Env):
    def test_derived_from_cache_path_matches_claude_plugin_data_convention(self):
        r = self.root("0.3.0")
        self.assertEqual(os.path.normpath(userdata.data_dir(r)), os.path.normpath(self.data))

    def test_env_overrides(self):
        r = self.root("0.3.0")
        os.environ["CLAUDE_PLUGIN_DATA"] = os.path.join(self.home, "elsewhere")
        self.assertEqual(os.path.normpath(userdata.data_dir(r)), os.path.normpath(os.path.join(self.home, "elsewhere")))
        os.environ["JOB_SEARCH_DATA_DIR"] = os.path.join(self.home, "explicit")
        self.assertEqual(os.path.normpath(userdata.data_dir(r)), os.path.normpath(os.path.join(self.home, "explicit")))

    def test_not_under_a_plugin_cache_means_inactive(self):
        d = os.path.join(self.home, "checkout")
        write(os.path.join(d, "data", "userdata-files.json"), json.dumps({"files": FILES}))
        self.assertIsNone(userdata.data_dir(d))


class Inactive(Env):
    def test_no_files_list_is_a_noop(self):
        """The personal edition ships no list, so nothing it holds is ever moved."""
        r = self.root("0.2.9", with_list=False)
        self.assertEqual(userdata.apply(r), [])
        self.assertEqual(userdata.save(r), [])
        self.assertFalse(os.path.exists(self.data))
        self.assertEqual(read(os.path.join(r, "data/screens.json")), "template data/screens.json")


class FirstRun(Env):
    def test_fresh_install_creates_manifest_and_keeps_templates(self):
        r = self.root("0.3.0")
        userdata.apply(r)
        self.assertTrue(os.path.exists(os.path.join(self.data, "manifest.json")))
        self.assertEqual(read(os.path.join(r, "data/screens.json")), "template data/screens.json")
        self.assertFalse(os.path.exists(os.path.join(self.data, "data", "screens.json")))

    def test_edit_is_saved_and_unchanged_files_are_not(self):
        r = self.root("0.3.0")
        userdata.apply(r)
        write(os.path.join(r, "context/candidate-profile.md"), "MY PROFILE")
        saved = userdata.save(r)
        self.assertEqual(saved, ["context/candidate-profile.md"])
        self.assertEqual(read(os.path.join(self.data, "context", "candidate-profile.md")), "MY PROFILE")
        self.assertEqual(userdata.save(r), [])  # idempotent


class Update(Env):
    def test_update_restores_personal_files_into_the_new_version_folder(self):
        old = self.root("0.3.0")
        userdata.apply(old)
        write(os.path.join(old, "data/notion.json"), '{"database_id": "abc"}')
        write(os.path.join(old, "context/candidate-profile.md"), "MY PROFILE")
        userdata.save(old)
        new = self.root("0.3.1")  # what `plugin update` produces: fresh templates, new folder
        notes = userdata.apply(new)
        self.assertEqual(read(os.path.join(new, "data/notion.json")), '{"database_id": "abc"}')
        self.assertEqual(read(os.path.join(new, "context/candidate-profile.md")), "MY PROFILE")
        self.assertEqual(read(os.path.join(new, "data/screens.json")), "template data/screens.json")
        self.assertEqual(notes, [])  # no template changed under a personal copy

    def test_warns_when_a_template_changed_under_a_personal_copy(self):
        old = self.root("0.3.0", {"data/screens.json": "screens v1"})
        userdata.apply(old)
        write(os.path.join(old, "data/screens.json"), "MY SCREENS")
        userdata.save(old)
        new = self.root("0.3.1", {"data/screens.json": "screens v2 (director flag)"})
        notes = userdata.apply(new)
        self.assertEqual(read(os.path.join(new, "data/screens.json")), "MY SCREENS")
        self.assertTrue(any("data/screens.json" in n and "changed" in n for n in notes), notes)

    def test_no_warning_when_the_template_is_unchanged(self):
        old = self.root("0.3.0", {"data/screens.json": "screens v1"})
        userdata.apply(old)
        write(os.path.join(old, "data/screens.json"), "MY SCREENS")
        userdata.save(old)
        new = self.root("0.3.1", {"data/screens.json": "screens v1"})
        self.assertEqual(userdata.apply(new), [])

    def test_save_never_overwrites_personal_files_with_a_fresh_template(self):
        """The failure this whole feature exists to prevent: an update lands, the restore step
        does not run (no Python on the hook's PATH, say), and the end-of-turn save then copies
        the fresh templates over the user's saved files."""
        old = self.root("0.3.0")
        userdata.apply(old)
        write(os.path.join(old, "context/candidate-profile.md"), "MY PROFILE")
        userdata.save(old)
        new = self.root("0.3.1")           # apply NOT called for the new folder
        self.assertEqual(userdata.save(new), [])
        self.assertEqual(read(os.path.join(self.data, "context", "candidate-profile.md")), "MY PROFILE")

    def test_unsaved_edit_survives_the_next_session_start(self):
        r = self.root("0.3.0")
        userdata.apply(r)
        write(os.path.join(r, "data/screens.json"), "EDITED, NOT YET SAVED")
        userdata.apply(r)  # a new session in the same folder must save first, then restore
        self.assertEqual(read(os.path.join(self.data, "data", "screens.json")), "EDITED, NOT YET SAVED")
        self.assertEqual(read(os.path.join(r, "data/screens.json")), "EDITED, NOT YET SAVED")

    def test_a_change_made_directly_in_the_data_folder_is_picked_up(self):
        r = self.root("0.3.0")
        userdata.apply(r)
        write(os.path.join(self.data, "data", "screens.json"), "EDITED IN DATA FOLDER")
        userdata.apply(r)
        self.assertEqual(read(os.path.join(r, "data/screens.json")), "EDITED IN DATA FOLDER")


class Import(Env):
    def test_import_from_an_earlier_install_folder(self):
        """Users on 0.2.x have their setup in the old version folder, not in the data folder."""
        old = self.root("0.2.9", {"data/screens.json": "template data/screens.json"}, with_list=False)
        write(os.path.join(old, "data/notion.json"), '{"database_id": "xyz"}')
        write(os.path.join(old, "context/candidate-profile.md"), "OLD PROFILE")
        new = self.root("0.3.0")
        userdata.apply(new)
        imported = userdata.import_from(new, old)
        self.assertEqual(sorted(imported), ["context/candidate-profile.md", "data/notion.json"])
        self.assertEqual(read(os.path.join(new, "data/notion.json")), '{"database_id": "xyz"}')
        self.assertEqual(read(os.path.join(self.data, "data", "notion.json")), '{"database_id": "xyz"}')

    def test_first_run_points_at_earlier_install_folders(self):
        self.root("0.2.9", with_list=False)
        new = self.root("0.3.0")
        notes = userdata.apply(new)
        self.assertTrue(any("import" in n and "0.2.9" in n for n in notes), notes)
        # said once, not every session
        self.assertFalse(any("import" in n for n in userdata.apply(new)))


class Cli(Env):
    def test_status_reports_without_changing_anything(self):
        r = self.root("0.3.0")
        userdata.apply(r)
        write(os.path.join(r, "data/screens.json"), "EDITED")
        text = userdata.status(r)
        self.assertIn("data/screens.json", text)
        self.assertIn("not yet saved", text)
        self.assertFalse(os.path.exists(os.path.join(self.data, "data", "screens.json")))

    def test_status_before_the_first_restore_does_not_call_templates_edits(self):
        """A fresh install has not been restored yet; its files are untouched templates."""
        r = self.root("0.3.0")
        text = userdata.status(r)
        self.assertIn("NO (run apply)", text)
        self.assertNotIn("edited here", text)
        self.assertIn("not restored yet", text)

    def test_status_before_restore_shows_a_saved_copy_will_come_back(self):
        old = self.root("0.3.0")
        userdata.apply(old)
        write(os.path.join(old, "data/notion.json"), "MINE")
        userdata.save(old)
        new = self.root("0.3.1")  # updated, session not started yet
        text = userdata.status(new)
        self.assertIn("data/notion.json: saved copy will be restored", text)


if __name__ == "__main__":
    unittest.main()
