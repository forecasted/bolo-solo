#!/usr/bin/env python3
"""Offline H2 1.x -> 2.x migration using local H2 command-line tools only."""

import argparse
import contextlib
import csv
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


class MigrationError(Exception):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def digest(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(block)
    return result.hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return digest(stream)


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def identifier(value):
    return '"' + value.replace('"', '""') + '"'


def properties_url(url):
    # Java Properties readers accept these escapes regardless of file encoding.
    parts = []
    for char in url:
        if char == "\\":
            parts.append("\\\\")
        elif ord(char) > 127:
            units = char.encode("utf-16-be")
            parts.extend("\\u" + units[i:i + 2].hex() for i in range(0, len(units), 2))
        else:
            parts.append(char)
    return "jdbc.URL=" + "".join(parts) + "\n"


def jar_version(path, major):
    try:
        with zipfile.ZipFile(path) as archive:
            archive.getinfo("org/h2/Driver.class")
            archive.getinfo("org/h2/tools/Script.class")
            archive.getinfo("org/h2/tools/RunScript.class")
            manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8")
    except (OSError, KeyError, zipfile.BadZipFile) as error:
        raise MigrationError("无效的本地 H2 JAR：{}".format(path)) from error
    manifest = manifest.replace("\r\n ", "").replace("\n ", "")
    match = re.search(r"^Implementation-Version: (\S+)", manifest, re.MULTILINE)
    if not match or not match.group(1).startswith(str(major) + "."):
        raise MigrationError("{} 必须是 H2 {}.x 的原版 JAR".format(path, major))
    return match.group(1)


def database_path(value):
    path = Path(value).expanduser().absolute()
    for suffix in (".mv.db", ".h2.db"):
        if path.name.endswith(suffix):
            path = path.with_name(path.name[:-len(suffix)])
            break
    path = path.resolve()
    if not path.name or any(c in str(path) for c in ";\r\n\x00"):
        raise MigrationError("数据库路径不能包含分号、换行或空字符；请提供文件路径而非 JDBC URL")
    candidates = [Path(str(path) + suffix) for suffix in (".mv.db", ".h2.db")]
    existing = [p for p in candidates if p.is_file()]
    if len(existing) != 1:
        raise MigrationError("需要唯一的旧数据库文件：{}.mv.db 或 {}.h2.db".format(path, path))
    return path, existing[0]


def source_files(database):
    paths = sorted(database.parent.glob(database.name + ".*"))
    lock = Path(str(database) + ".lock.db")
    if lock.exists() or lock.is_symlink():
        raise MigrationError("发现旧数据库锁文件，请先停止博客并确认数据库已关闭：{}".format(lock))
    files = []
    for path in paths:
        entries = [path]
        if path.is_dir() and not path.is_symlink():
            entries.extend(sorted(path.rglob("*")))
        for entry in entries:
            if entry.is_symlink():
                raise MigrationError("数据库伴随文件不能是符号链接：{}".format(entry))
            if entry.is_file():
                files.append(entry)
            elif not entry.is_dir():
                raise MigrationError("数据库目录中包含非普通文件：{}".format(entry))
    return files


@contextlib.contextmanager
def locked_database(primary):
    """Use the OS byte-range locks used by Java FileChannel, including MVStore."""
    with primary.open("rb") as stream:
        try:
            if os.name == "posix":
                import fcntl
                fcntl.lockf(stream.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            elif os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBRLCK, 1)
            else:
                raise MigrationError("当前系统不支持数据库文件锁检查")
        except OSError as error:
            raise MigrationError("旧数据库正在使用或无法锁定，请先停止博客：{}".format(primary)) from error
        if not os.path.samestat(os.fstat(stream.fileno()), primary.stat()):
            raise MigrationError("锁定期间旧数据库文件被替换，请停止博客后重试")
        # Keep this descriptor open throughout the migration. On POSIX, opening
        # and closing another descriptor for the same inode releases its locks.
        yield stream


def backup_files(files, primary, source_stream, destination):
    records = []
    for source in files:
        relative = source.relative_to(primary.parent)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        before = source.stat()
        same_primary = os.path.samefile(source, primary)
        if same_primary:
            source_stream.seek(0)
        with contextlib.ExitStack() as stack:
            stream = source_stream if same_primary else stack.enter_context(source.open("rb"))
            output = stack.enter_context(target.open("xb"))
            checksum = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                checksum.update(block)
                output.write(block)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise MigrationError("备份期间旧数据库发生变化，请完全停止博客后重试：{}".format(source))
        if file_digest(target) != checksum.hexdigest():
            raise MigrationError("备份校验失败：{}".format(target))
        records.append({"file": str(relative), "size": after.st_size, "sha256": checksum.hexdigest()})
    return records


def csv_statement(path, query):
    return "CALL CSVWRITE({}, {}, 'charset=UTF-8');\n".format(literal(path), literal(query))


class H2Tools:
    def __init__(self, java, user, password, work):
        self.java, self.user, self.password, self.work = java, user, password, work
        self.step = 0

    def run(self, jar, tool, url, label, arguments):
        self.step += 1
        log = self.work / "logs" / "{:02d}-{}.log".format(self.step, label)
        command = [self.java, "-Dfile.encoding=UTF-8", "-cp", str(jar), "org.h2.tools." + tool,
                   "-url", url, "-user", self.user, "-password", self.password] + arguments
        print("  {} …".format(label), flush=True)
        # No shell, dependency download or external service is involved. Never
        # print the command: the H2 CLI requires its password as a process argument.
        with log.open("xb") as output:
            try:
                result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
            except OSError as error:
                raise MigrationError("无法运行 Java；详情目录：{}".format(log.parent)) from error
        if result.returncode:
            raise MigrationError("{} 失败，详情：{}".format(label, log))

    def sql(self, jar, url, label, sql):
        script = self.work / "checks" / (label + ".sql")
        script.write_text(sql, encoding="utf-8")
        self.run(jar, "RunScript", url, label, ["-script", str(script)])

    def counts(self, jar, url, label):
        tables_file = self.work / "checks" / (label + "-tables.csv")
        query = ("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA <> 'INFORMATION_SCHEMA' "
                 "AND TABLE_TYPE IN ('TABLE', 'BASE TABLE') ORDER BY TABLE_SCHEMA, TABLE_NAME")
        self.sql(jar, url, label + "-tables", csv_statement(tables_file, query))
        with tables_file.open(encoding="utf-8", newline="") as stream:
            tables = list(csv.DictReader(stream))
        if not tables:
            return {}
        queries = []
        for table in tables:
            schema, name = table["TABLE_SCHEMA"], table["TABLE_NAME"]
            queries.append("SELECT {} AS TABLE_SCHEMA, {} AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM {}.{}"
                           .format(literal(schema), literal(name), identifier(schema), identifier(name)))
        counts_file = self.work / "checks" / (label + "-counts.csv")
        self.sql(jar, url, label + "-counts", csv_statement(counts_file, " UNION ALL ".join(queries)))
        with counts_file.open(encoding="utf-8", newline="") as stream:
            return {(row["TABLE_SCHEMA"], row["TABLE_NAME"]): int(row["ROW_COUNT"])
                    for row in csv.DictReader(stream)}


def arguments():
    parser = argparse.ArgumentParser(description="离线迁移 Bolo 的 H2 1.x 文件数据库到 2.x；先停止博客。仅依赖 Python 3.8+、Java 21+ 和本地新旧 JAR。")
    parser.add_argument("--database", required=True, help="旧库文件路径或不含 .mv.db/.h2.db 扩展名的路径")
    parser.add_argument("--old-jar", required=True, help="旧实例实际使用的 H2 1.x JAR；必须与旧数据库匹配")
    parser.add_argument("--new-jar", help="H2 2.x JAR；默认查找项目 target/bolo/WEB-INF/lib/h2-*.jar")
    parser.add_argument("--user", default="root", help="数据库管理员用户名（默认 root）")
    secret = parser.add_mutually_exclusive_group()
    secret.add_argument("--password-file", help="UTF-8 密码文件；只移除结尾的一个换行")
    secret.add_argument("--empty-password", action="store_true", help="显式使用空密码")
    parser.add_argument("--output-dir", help="新的迁移目录（必须不存在）；默认在旧库旁创建独立目录")
    parser.add_argument("--java", default=os.environ.get("JAVA_HOME", "") and str(Path(os.environ["JAVA_HOME"]) / "bin/java") or "java", help="Java 21+ 可执行文件路径")
    return parser.parse_args()


def save_manifest(work, manifest):
    temporary = work / "manifest.json.tmp"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(work / "manifest.json")


def migrate(args):
    os.umask(0o077)
    database, primary = database_path(args.database)
    files = source_files(database)
    old_jar = Path(args.old_jar).expanduser().resolve()
    if args.new_jar:
        new_jar = Path(args.new_jar).expanduser().resolve()
    else:
        candidates = sorted((Path(__file__).resolve().parent.parent / "target/bolo/WEB-INF/lib").glob("h2-*.jar"))
        if len(candidates) != 1:
            raise MigrationError("未找到唯一的新 H2 JAR，请使用 --new-jar 指定本地文件")
        new_jar = candidates[0]
    old_version, new_version = jar_version(old_jar, 1), jar_version(new_jar, 2)
    java = shutil.which(args.java)
    if not java:
        raise MigrationError("找不到 Java，请使用 --java 指定 Java 21+ 可执行文件")
    java_check = subprocess.run([java, "-XshowSettings:properties", "-version"], capture_output=True, text=True)
    version = re.search(r"java.specification.version\s*=\s*(\d+)", java_check.stderr + java_check.stdout)
    if java_check.returncode or not version or int(version.group(1)) < 21:
        raise MigrationError("需要 Java 21 或更新版本")
    if args.output_dir:
        output = Path(args.output_dir).expanduser().resolve()
        if output.exists():
            raise MigrationError("输出目录已存在，请使用全新路径：{}".format(output))
        if any(c in str(output) for c in ";\r\n\x00"):
            raise MigrationError("输出目录不能包含分号、换行或空字符")
        if output.parent == database.parent and output.name.startswith(database.name + "."):
            raise MigrationError("输出目录不能使用旧数据库的文件前缀")
        for companion in database.parent.glob(database.name + ".*"):
            if companion in output.parents:
                raise MigrationError("输出目录不能位于旧数据库伴随文件内")
    else:
        output = None
    if args.empty_password:
        password = ""
    elif args.password_file:
        password = Path(args.password_file).expanduser().read_bytes().decode("utf-8")
        password = password[:-2] if password.endswith("\r\n") else password[:-1] if password.endswith("\n") else password
    elif "H2_PASSWORD" in os.environ:
        password = os.environ["H2_PASSWORD"]
    elif sys.stdin.isatty():
        password = getpass.getpass("旧数据库密码：")
    else:
        raise MigrationError("非交互运行请使用 --password-file、--empty-password 或 H2_PASSWORD 环境变量")

    with locked_database(primary) as source_stream:
        if output:
            output.mkdir(mode=0o700)
            work = output
        else:
            work = Path(tempfile.mkdtemp(prefix=database.name + "-h2-migration-", dir=str(database.parent)))
        manifest = {"status": "running", "started_at": timestamp(), "source_database": str(database),
                    "old_h2_version": old_version, "new_h2_version": new_version,
                    "old_jar_sha256": file_digest(old_jar), "new_jar_sha256": file_digest(new_jar)}
        print("迁移目录：{}".format(work), flush=True)
        try:
            for name in ("backup", "database", "checks", "logs"):
                (work / name).mkdir(mode=0o700)
            save_manifest(work, manifest)
            print("[1/5] 复制并校验旧库备份", flush=True)
            manifest["backup_files"] = backup_files(files, primary, source_stream, work / "backup")
            save_manifest(work, manifest)
            tools = H2Tools(java, args.user, password, work)
            # All H2 1.x access is to this read-only backup, never to the original.
            old_url = "jdbc:h2:{};MODE=MYSQL;IFEXISTS=TRUE;ACCESS_MODE_DATA=r;FILE_LOCK=NO".format((work / "backup" / database.name).as_posix())
            print("[2/5] 读取旧库表行数并导出 SQL（H2 {}）".format(old_version), flush=True)
            old_counts = tools.counts(old_jar, old_url, "old")
            export = work / "export.sql"
            # Quote SQL paths ourselves: older Script tools interpolate their
            # -script path without escaping apostrophes.
            tools.sql(old_jar, old_url, "export", "SCRIPT TO {} CHARSET 'UTF-8';\n".format(literal(export)))
            if not export.is_file() or not export.stat().st_size:
                raise MigrationError("SQL 导出为空，迁移已停止")
            manifest["export_sha256"] = file_digest(export)
            new_database = work / "database" / database.name
            new_url = "jdbc:h2:{};MODE=MYSQL".format(new_database.as_posix())
            print("[3/5] 导入全新数据库（H2 {}）".format(new_version), flush=True)
            tools.sql(new_jar, new_url, "import",
                      "RUNSCRIPT FROM {} CHARSET 'UTF-8' FROM_1X;\n".format(literal(export)))
            print("[4/5] 逐表核对行数，校验原库和备份", flush=True)
            new_counts = tools.counts(new_jar, new_url + ";IFEXISTS=TRUE", "new")
            if old_counts != new_counts:
                raise MigrationError("迁移前后表集合或行数不一致；请查看 checks/ 下的 CSV，勿切换数据库")
            if source_files(database) != files:
                raise MigrationError("迁移期间旧库伴随文件发生变化，请完全停止博客后重试")
            if not os.path.samestat(os.fstat(source_stream.fileno()), primary.stat()):
                raise MigrationError("迁移期间原数据库文件被替换，请完全停止博客后重试")
            for record in manifest["backup_files"]:
                source, backup = database.parent / record["file"], work / "backup" / record["file"]
                if os.path.samefile(source, primary):
                    source_stream.seek(0)
                    source_hash = digest(source_stream)
                else:
                    source_hash = file_digest(source)
                if source_hash != record["sha256"] or file_digest(backup) != record["sha256"]:
                    raise MigrationError("原库或备份校验值发生变化：{}".format(source))
            manifest.update({"status": "complete", "finished_at": timestamp(), "new_database": str(new_database),
                             "jdbc_url": new_url, "table_count": len(new_counts),
                             "row_counts": [{"schema": schema, "table": table, "rows": count}
                                            for (schema, table), count in sorted(new_counts.items())]})
            # A suggestion, rather than an automatically overwritten live config.
            (work / "jdbc-url.txt").write_text(properties_url(new_url), encoding="ascii")
            save_manifest(work, manifest)
            print("[5/5] 迁移成功：{} 张表，{} 行，全部核对一致".format(len(new_counts), sum(new_counts.values())), flush=True)
            print("备份、SQL、校验报告：{}".format(work))
            print("请将 local.properties 的 jdbc.URL 设置为：\n" + new_url)
            print("然后启动新版博客验证；原库与旧部署包可用于回退。")
            return work
        except (Exception, KeyboardInterrupt) as error:
            manifest.update({"status": "failed", "finished_at": timestamp(),
                             "error": "用户中断" if isinstance(error, KeyboardInterrupt) else str(error)})
            try:
                save_manifest(work, manifest)
            except OSError:
                pass
            print("迁移未完成，保留现场供检查：{}；重试请使用新的输出目录。".format(work), file=sys.stderr)
            raise


def main():
    try:
        migrate(arguments())
    except KeyboardInterrupt:
        print("迁移已中断。", file=sys.stderr)
        return 130
    except (MigrationError, OSError, ValueError) as error:
        print("错误：{}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
