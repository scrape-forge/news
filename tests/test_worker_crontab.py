import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import install_worker_crontab


class WorkerCrontabTests(TestCase):
    def test_build_is_idempotent_and_preserves_unmanaged_entries(self):
        kwargs = {
            "project_dir": Path("/app"),
            "python_bin": Path("/usr/local/bin/python"),
            "log_dir": Path("/var/log/news-workers"),
            "remove": False,
        }
        initial = "0 3 * * * /usr/local/bin/backup\n"

        first = install_worker_crontab.build_crontab(
            initial,
            ["enrich"],
            {},
            **kwargs,
        )
        second = install_worker_crontab.build_crontab(
            first,
            ["enrich"],
            {},
            **kwargs,
        )

        self.assertEqual(first, second)
        self.assertIn("0 3 * * * /usr/local/bin/backup", second)
        self.assertEqual(second.count("# BEGIN news-worker:enrich"), 1)
        self.assertIn("-m news.workers enrich", second)

    def test_remove_only_deletes_selected_managed_block(self):
        current = install_worker_crontab.build_crontab(
            "MAILTO=ops@example.com\n",
            ["enrich"],
            {},
            project_dir=Path("/app"),
            python_bin=Path("/usr/local/bin/python"),
            log_dir=Path("/var/log/news-workers"),
            remove=False,
        )

        updated = install_worker_crontab.build_crontab(
            current,
            ["enrich"],
            {},
            project_dir=Path("/app"),
            python_bin=Path("/usr/local/bin/python"),
            log_dir=Path("/var/log/news-workers"),
            remove=True,
        )

        self.assertEqual(updated, "MAILTO=ops@example.com\n")

    def test_install_removes_retired_worker_blocks(self):
        current = """# BEGIN news-worker:tags
* * * * * old-command
# END news-worker:tags
"""

        updated = install_worker_crontab.build_crontab(
            current,
            ["enrich"],
            {},
            project_dir=Path("/app"),
            python_bin=Path("/usr/local/bin/python"),
            log_dir=Path("/var/log/news-workers"),
            remove=False,
        )

        self.assertNotIn("news-worker:tags", updated)
        self.assertIn("news-worker:enrich", updated)

    def test_install_removes_unmarked_retired_worker_entry(self):
        current = """# do daily maintenance
0 2 * * * run-parts /etc/periodic/daily
*/1 * * * * cd /app && /usr/local/bin/python -u -m news.workers tags >> /app/logs/workers/tags.log 2>&1
*/1 * * * * cd /app && /usr/local/bin/python -u -m news.workers enrich >> /app/logs/workers/enrich.log 2>&1
*/5 * * * * /usr/local/bin/unrelated-job
"""

        updated = install_worker_crontab.build_crontab(
            current,
            ["enrich"],
            {},
            project_dir=Path("/app"),
            python_bin=Path("/usr/local/bin/python"),
            log_dir=Path("/var/log/news-workers"),
            remove=False,
        )

        self.assertNotIn("news.workers tags", updated)
        self.assertIn("run-parts /etc/periodic/daily", updated)
        self.assertIn("/usr/local/bin/unrelated-job", updated)
        self.assertIn("news.workers enrich", updated)
        self.assertEqual(updated.count("news.workers enrich"), 1)
        self.assertEqual(updated.count("# BEGIN news-worker:enrich"), 1)

    @patch.dict(
        os.environ,
        {
            "CRON_WORKERS": "enrich",
            "WORKER_CRON_ENRICH": "*/5 * * * *",
        },
        clear=True,
    )
    def test_reads_workers_and_schedules_from_environment(self):
        workers = install_worker_crontab.selected_workers([])
        values = install_worker_crontab.environment_schedule_overrides(workers)
        schedules = install_worker_crontab.parse_schedule_overrides(values)

        self.assertEqual(workers, ["enrich"])
        self.assertEqual(schedules, {"enrich": "*/5 * * * *"})

    def test_rejects_schedule_with_wrong_number_of_fields(self):
        with self.assertRaises(ValueError):
            install_worker_crontab.parse_schedule_overrides(["enrich=* * *"])

    def test_rejects_unknown_positional_worker(self):
        with self.assertRaises(ValueError):
            install_worker_crontab.selected_workers(["unknown"])

    def test_direct_file_write_atomically_replaces_content(self):
        with TemporaryDirectory() as directory:
            crontab_file = Path(directory) / "root"
            crontab_file.write_text("old\n", encoding="utf-8")
            old_inode = crontab_file.stat().st_ino

            install_worker_crontab.write_crontab("new\n", crontab_file)

            self.assertEqual(crontab_file.read_text(encoding="utf-8"), "new\n")
            self.assertNotEqual(crontab_file.stat().st_ino, old_inode)
