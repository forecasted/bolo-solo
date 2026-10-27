#!/usr/bin/env python3
"""Integration tests using real local H2 JARs; all databases are temporary."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


PROJECT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT / "scripts/migrate-h2.py"
SETTINGS = None


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MigrationTests(unittest.TestCase):
    def setUp(self):
        (PROJECT / "target").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="h2-migration-tests-", dir=str(PROJECT / "target"))
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.original = self.work / "旧库 with spaces"
        self.original.mkdir()
        self.database = self.original / "blog"
        self.output = self.work / "new migration's output"
        self.password = " 迁移密码 ' with spaces "

    def java_sql(self, jar, url, sql):
        script = self.work / "fixture.sql"
        script.write_text(sql, encoding="utf-8")
        result = subprocess.run([SETTINGS.java, "-Dfile.encoding=UTF-8", "-cp", str(jar),
                                 "org.h2.tools.RunScript", "-url", url, "-user", "root",
                                 "-password", self.password, "-script", str(script)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def fixture(self, page_store=False, empty=False):
        url = "jdbc:h2:{};MODE=MYSQL".format(self.database.as_posix())
        if page_store:
            url += ";MV_STORE=FALSE"
        if empty:
            sql = "SELECT 1;"
        else:
            sql = '''
CREATE TABLE "b3_solo_article" ("oId" VARCHAR(64) PRIMARY KEY, "title" VARCHAR(255), "content" CLOB, "payload" BLOB);
INSERT INTO "b3_solo_article" VALUES ('1', '中文标题 😀', REPEAT('大段正文', 50000), X'00ff80');
INSERT INTO "b3_solo_article" VALUES ('2', 'second', NULL, NULL);
CREATE TABLE "empty_table" ("id" INT);
CREATE TABLE "generated" ("id" BIGINT AUTO_INCREMENT PRIMARY KEY, "text" VARCHAR(32));
INSERT INTO "generated" ("text") VALUES ('first');
CREATE SEQUENCE "article_seq" START WITH 7;
CALL NEXT VALUE FOR "article_seq";
CREATE VIEW "article_titles" AS SELECT "title" FROM "b3_solo_article";
CREATE SCHEMA "schema's quote";
CREATE TABLE "schema's quote"."odd ' table" ("id" INT);
INSERT INTO "schema's quote"."odd ' table" VALUES (1), (2), (3);
'''
        self.java_sql(SETTINGS.old_jar, url, sql)
        self.primary = Path(str(self.database) + (".h2.db" if page_store else ".mv.db"))
        self.assertTrue(self.primary.is_file())
        self.source_hash = sha256(self.primary)

    def migrate(self, extra=(), expected=0, password=None, use_environment=True):
        env = os.environ.copy()
        env.pop("H2_PASSWORD", None)
        if use_environment:
            env["H2_PASSWORD"] = self.password if password is None else password
        result = subprocess.run([sys.executable, str(SCRIPT), "--database", str(self.database),
                                 "--old-jar", str(SETTINGS.old_jar), "--new-jar", str(SETTINGS.new_jar),
                                 "--java", SETTINGS.java, "--output-dir", str(self.output)] + list(extra),
                                env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def assert_source_preserved(self):
        self.assertEqual(sha256(self.primary), self.source_hash)

    def assert_success(self):
        manifest = json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "complete")
        self.assert_source_preserved()
        self.assertEqual(sha256(self.output / "backup" / self.primary.name), self.source_hash)
        self.assertNotIn(self.password, json.dumps(manifest, ensure_ascii=False))
        self.assertEqual(manifest["table_count"], 4)
        self.assertEqual(sorted(row["rows"] for row in manifest["row_counts"]), [0, 1, 2, 3])
        self.assertEqual(len(manifest["row_counts"]), 4)
        if os.name == "posix":
            self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        verification = self.output / "verify.csv"
        query = '''SELECT (SELECT COUNT(*) FROM "article_titles") AS TITLES,
                   (SELECT "title" FROM "b3_solo_article" WHERE "oId"='1') AS TITLE,
                   (SELECT LENGTH("content") FROM "b3_solo_article" WHERE "oId"='1') AS CONTENT_LENGTH,
                   (SELECT OCTET_LENGTH("payload") FROM "b3_solo_article" WHERE "oId"='1') AS BINARY_LENGTH,
                   NEXT VALUE FOR "article_seq" AS SEQUENCE_VALUE'''
        sql = '''INSERT INTO "generated" ("text") VALUES ('second');\n'''
        sql += "CALL CSVWRITE('{}', '{}', 'charset=UTF-8');".format(
            str(verification).replace("'", "''"), query.replace("'", "''"))
        self.java_sql(SETTINGS.new_jar, manifest["jdbc_url"] + ";IFEXISTS=TRUE", sql)
        with verification.open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row, {"TITLES": "2", "TITLE": "中文标题 😀", "CONTENT_LENGTH": "200000",
                               "BINARY_LENGTH": "3", "SEQUENCE_VALUE": "8"})

    def test_mvstore_migrates_data_lobs_views_sequences_and_identity(self):
        self.fixture()
        self.migrate()
        self.assert_success()

    def test_pagestore_and_password_file_preserve_data_and_whitespace(self):
        self.fixture(page_store=True)
        password_file = self.work / "password.txt"
        password_file.write_text(self.password + "\n", encoding="utf-8")
        self.migrate(["--database", str(self.primary), "--password-file", str(password_file)], use_environment=False)
        self.assert_success()

    def test_existing_output_directory_is_never_overwritten(self):
        self.fixture()
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_text("preserve")
        self.migrate(expected=1)
        self.assertEqual(list(self.output.iterdir()), [marker])
        self.assert_source_preserved()

    def test_wrong_password_retains_backup_and_marks_failure(self):
        self.fixture()
        self.migrate(password="incorrect", expected=1)
        manifest = json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "failed")
        self.assertFalse((self.output / "jdbc-url.txt").exists())
        self.assertEqual(sha256(self.output / "backup" / self.primary.name), self.source_hash)
        self.assert_source_preserved()

    def test_incompatible_custom_sql_retains_backup_and_marks_import_failure(self):
        self.fixture(empty=True)
        self.java_sql(SETTINGS.old_jar, "jdbc:h2:{};MODE=MYSQL".format(self.database.as_posix()), '''
CREATE ALIAS "legacy_only" FOR "org.h2.util.StringUtils.quoteRemarkSQL";
CREATE TABLE "legacy_data" ("id" INT, "value" VARCHAR DEFAULT "legacy_only"('old'));
INSERT INTO "legacy_data" ("id") VALUES (1);
''')
        self.source_hash = sha256(self.primary)
        self.migrate(expected=1)
        manifest = json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "failed")
        self.assertIn("import", manifest["error"])
        self.assertTrue((self.output / "export.sql").is_file())
        self.assertTrue((self.output / "database" / "blog.mv.db").is_file())
        self.assertFalse((self.output / "jdbc-url.txt").exists())
        self.assert_source_preserved()
        self.assertEqual(sha256(self.output / "backup" / self.primary.name), self.source_hash)

    def test_missing_source_does_not_create_a_database(self):
        self.migrate(expected=1)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.original.iterdir()))

    def test_wrong_jar_major_version_fails_before_backup(self):
        self.fixture()
        self.migrate(["--old-jar", str(SETTINGS.new_jar)], expected=1)
        self.assertFalse(self.output.exists())
        self.assert_source_preserved()

    def test_existing_lock_file_prevents_migration(self):
        self.fixture()
        lock = Path(str(self.database) + ".lock.db")
        lock.write_text("a live or stale H2 lock")
        self.migrate(expected=1)
        self.assertFalse(self.output.exists())
        self.assert_source_preserved()

    def test_output_inside_lob_directory_is_rejected(self):
        self.fixture()
        lob = Path(str(self.database) + ".lobs.db")
        lob.mkdir()
        self.migrate(["--output-dir", str(lob / "nested")], expected=1)
        self.assertFalse((lob / "nested").exists())

    def test_jdbc_options_in_output_path_are_rejected(self):
        self.fixture()
        self.migrate(["--output-dir", str(self.work / "bad;AUTO_SERVER=TRUE")], expected=1)
        self.assertFalse((self.work / "bad;AUTO_SERVER=TRUE").exists())

    def test_live_h2_connection_prevents_migration(self):
        self.fixture()
        output = self.work / "shell.log"
        with output.open("w") as log:
            process = subprocess.Popen([SETTINGS.java, "-cp", str(SETTINGS.old_jar), "org.h2.tools.Shell",
                                        "-url", "jdbc:h2:{};MODE=MYSQL".format(self.database.as_posix()),
                                        "-user", "root", "-password", self.password],
                                       stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 15
                while "sql>" not in output.read_text(encoding="utf-8"):
                    if process.poll() is not None or time.monotonic() > deadline:
                        self.fail("H2 did not keep its connection open: " + output.read_text())
                    time.sleep(0.1)
                self.migrate(expected=1)
                self.assertFalse(self.output.exists())
            finally:
                process.communicate(b"exit\n", timeout=10)

    def test_empty_database_and_explicit_empty_password(self):
        self.password = ""
        self.fixture(empty=True)
        self.migrate(["--empty-password"], use_environment=False)
        manifest = json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "complete")
        self.assertEqual(manifest["table_count"], 0)
        self.assertEqual(manifest["row_counts"], [])
        self.assert_source_preserved()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-jar", type=Path, required=True)
    parser.add_argument("--new-jar", type=Path, required=True)
    parser.add_argument("--java", default="java")
    SETTINGS, unittest_args = parser.parse_known_args()
    unittest.main(argv=[sys.argv[0]] + unittest_args)
