#!/usr/bin/env python3
"""Regression tests for autocommit.py, the ~/.claude checkpoint hook (secret scan, one commit per area).

Every test builds a throwaway git repository in the temp folder (TMP/TEMP choose where) and points the
hook at it with CLAUDE_AUTOCOMMIT_ROOT; CLAUDE_CONFIG_DIR, HOME and USERPROFILE point into the throwaway
folder too, so the real ~/.claude repository is never read or written by these tests.
Fake credentials are put together at run time, so this file holds none itself (the hook scans it too).
Run:  python -B test_autocommit.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import random
import shutil
import stat
import string
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().with_name("autocommit.py")
REAL = (Path.home() / ".claude").resolve()
PY = sys.executable
for _k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_CEILING_DIRECTORIES"):
    os.environ.pop(_k, None)

# the module itself, loaded with its root on a folder that is never a repository (pure functions only)
_SAFE = Path(tempfile.mkdtemp(prefix="autocommit-safe-"))
os.environ["CLAUDE_AUTOCOMMIT_ROOT"] = str(_SAFE / "not-a-repo")
_spec = importlib.util.spec_from_file_location("autocommit_under_test", HOOK)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)
assert ac.ROOT == _SAFE / "not-a-repo", ac.ROOT

GITIGNORE = """/*
!/.gitignore
!/CLAUDE.md
!/settings.json
!/commands/
!/hooks/
!/skills/
!/create-clips/
!/static-studio/
!/projects/
/projects/*/*
!/projects/*/memory/
"""


def rand(n: int, alphabet: str, seed: int) -> str:
    r = random.Random(seed)
    return "".join(r.choice(alphabet) for _ in range(n))


HEX = "0123456789abcdef"
ALNUM = string.ascii_letters + string.digits
B64 = ALNUM + "+/"
SK = "s" + "k-" + rand(40, string.ascii_letters, 1)                      # "sk-" + 40 letters
SK_PROJ = "s" + "k-proj-" + rand(120, ALNUM + "_-", 2)
AWS = "AK" + "IA" + rand(16, string.ascii_uppercase + string.digits, 3)
GH = "gh" + "p_" + rand(36, ALNUM, 4)
GH_PAT = "github" + "_pat_" + rand(82, ALNUM + "_", 5)
HFT = "h" + "f_" + rand(34, ALNUM, 6)
PEM = ("-----BEGIN " + "RSA PRIVATE KEY-----\n" + "\n".join(rand(64, B64, 7 + i) for i in range(4))
       + "\n-----END RSA PRIVATE KEY-----\n")
ELEVEN_VALUE = "s" + "k_" + rand(48, HEX, 11)
ELEVEN = "ELEVEN" + '_API_KEY = "' + ELEVEN_VALUE + '"\n'
XI = 'curl -H "xi-' + 'api-key: ' + rand(32, HEX, 12) + '" https://api.elevenlabs.io/v1/voices\n'
OPENAI = "export OPENAI" + "_API_KEY=" + rand(40, ALNUM, 13) + "\n"
ANTHROPIC = '{"env": {"ANTHROPIC' + '_API_KEY": "' + rand(40, ALNUM, 14) + '"}}\n'
SOURCE = "$env:CC_SOURCE" + "_KEY = '" + rand(43, ALNUM + "_-", 15) + "='\n"
NOTED = ("# Admin session\n\nADMIN_SESSION" + "_SECRET generated today:\n\n```\n" + rand(128, HEX, 16)
         + "\n```\n")
POSITIVE = {SK: "sk- key", SK_PROJ: "sk- key", AWS: "AWS key", GH: "GitHub token", GH_PAT: "GitHub token",
            HFT: "Hugging Face token", PEM: "private key", ELEVEN: "ELEVEN_API_KEY value", XI: "xi-api-key value",
            OPENAI: "OPENAI_API_KEY value", ANTHROPIC: "ANTHROPIC_API_KEY value", SOURCE: "CC_SOURCE_KEY value",
            NOTED: "ADMIN_SESSION_SECRET value"}
NEGATIVE = [
    "see task-lists-and-todo-files.md and the musk-share-notes-for-the-whole-weekend-trip file",
    "pip install s" + "k-learn-compatible-transformers-for-pipelines-and-more",
    "s" + "k-" + "x" * 40,
    "AK" + "IAIOSFODNN7EXAMPLE",
    'ELEVEN' + '_API_KEY = os.environ["ELEVEN' + '_API_KEY"]',
    'key = os.environ.get("ELEVEN' + '_API_KEY", "")',
    "ELEVEN" + "_API_KEY: <your key>",
    'curl -H "xi-' + 'api-key: $ELEVEN' + '_API_KEY"',
    '{"xi-' + 'api-key": ELEVEN' + '_API_KEY}',
    "-----BEGIN " + "PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
    'POSTHOG' + '_API_KEY = "ph' + 'c_' + rand(43, ALNUM, 21) + '"',
    'ELEVEN' + '_API_KEY = "test-key-for-the-unit"',
    "OPENAI" + "_API_KEY = get_secret_value_2024()",
    "TOPAZ" + "_API_KEY=ELEVEN" + "_API_KEY_BACKUP_2",
    "CC_SOURCE" + "_KEY lives in:\nstatic-studio/reference/02-creative-editorial-engine\n",
    "CC_SOURCE" + "_KEY notes\n" + "-" * 3000 + " x\n",
]


def _rmtree(path: Path) -> None:
    def onexc(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onexc=onexc) if sys.version_info >= (3, 12) else shutil.rmtree(path, onerror=onexc)


class Repo:
    """A throwaway allow-list repository shaped like ~/.claude, with one first commit."""

    def __init__(self, first_commit: bool = True) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="autocommit-test-")).resolve()
        assert self.base != REAL and REAL not in self.base.parents, self.base
        self.dir = self.base / "dot-claude"
        self.home = self.base / "home"
        self.dir.mkdir()
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
        self.env.update(CLAUDE_AUTOCOMMIT_ROOT=str(self.dir), CLAUDE_CONFIG_DIR=str(self.dir),
                        HOME=str(self.home), USERPROFILE=str(self.home))
        self.git("init", "-q", "-b", "pc", ".")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "core.autocrlf", "false")
        self.write(".gitignore", GITIGNORE)
        if first_commit:
            self.git("add", ".gitignore")
            self.git("commit", "-q", "-m", "init")

    def git(self, *args, env=None, input=None) -> str:
        cp = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=self.dir, capture_output=True,
                            env=env or self.env, input=input)
        if cp.returncode:
            raise AssertionError(f"git {args} failed: {cp.stderr.decode('utf-8', 'replace')}")
        return cp.stdout.decode("utf-8", "replace")

    def write(self, rel: str, data) -> None:
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)

    def run(self, event="Stop", payload=True, stdin: bytes | None = None, sid="abcd1234-test-session"):
        """Run the hook as Claude Code does; returns (exit code, systemMessage or None)."""
        assert self.env["CLAUDE_AUTOCOMMIT_ROOT"] == str(self.dir)
        if stdin is None:
            stdin = json.dumps({"hook_event_name": event, "session_id": sid}).encode() if payload else b""
        cp = subprocess.run([PY, "-B", str(HOOK), event], input=stdin, capture_output=True, env=self.env,
                            cwd=self.base, timeout=180)
        out = cp.stdout.decode("utf-8", "replace").strip()
        return cp.returncode, (json.loads(out.splitlines()[-1])["systemMessage"] if out else None)

    def head(self) -> str:
        return self.git("rev-parse", "HEAD").strip()

    def commits_since(self, base: str) -> list:
        """[(subject, body, [files])] oldest first."""
        out = []
        for c in self.git("rev-list", "--reverse", f"{base}..HEAD").split():
            subject = self.git("log", "-1", "--format=%s", c).strip()
            body = self.git("log", "-1", "--format=%b", c)
            files = [f for f in self.git("show", "--name-only", "--no-renames", "--format=", c).splitlines() if f]
            out.append((subject, body, files))
        return out

    def tracked(self) -> set:
        return set(self.git("ls-tree", "-r", "--name-only", "HEAD").splitlines())

    def close(self) -> None:
        _rmtree(self.base)


class HookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.r = Repo()

    def tearDown(self) -> None:
        self.r.close()

    # ---- one commit per area ---------------------------------------------------------------------
    def test_one_commit_per_area_in_stable_order(self):
        r = self.r
        files = {"settings.json": "{}\n", "CLAUDE.md": "# rules\n", "commands/a.md": "a\n", "commands/b.md": "b\n",
                 "hooks/h.py": "print(1)\n", "projects/C--x/memory/MEMORY.md": "- note\n",
                 "projects/C--x/memory/note.md": "note\n", "static-studio/s.py": "s = 1\n",
                 "skills/k/SKILL.md": "skill\n"}
        for rel, text in files.items():
            r.write(rel, text)
        base = r.head()
        code, msg = r.run()
        self.assertEqual(code, 0)
        commits = r.commits_since(base)
        areas = [s.split("[", 1)[1].split("]", 1)[0] for s, _, _ in commits]
        self.assertEqual(areas, ["commands", "config", "hooks", "memory", "skills", "static-studio"])
        for (subject, body, changed), area in zip(commits, areas):
            self.assertTrue(subject.startswith(f"auto(Stop) [{area}]: "), subject)
            self.assertIn("session: abcd1234", body)
            self.assertEqual({ac.area_of(f) for f in changed}, {area}, (area, changed))
        self.assertEqual(sorted(f for _, _, ch in commits for f in ch), sorted(files))
        self.assertEqual(r.git("status", "--porcelain"), "")
        self.assertTrue(msg.startswith("~/.claude versioned: "), msg)
        self.assertIn("[commands], ", msg)
        self.assertIn("(9 file(s): ", msg)
        code, msg = r.run()                                       # nothing changed: silent, no commit
        self.assertEqual((code, msg), (0, None))
        self.assertEqual(len(r.commits_since(base)), 6)

    def test_subject_lists_three_files_then_more_and_body_has_status_lines(self):
        r = self.r
        for i in range(1, 6):
            r.write(f"commands/{i}.md", f"{i}\n")
        base = r.head()
        r.run()
        (subject, body, _), = r.commits_since(base)
        self.assertEqual(subject, "auto(Stop) [commands]: commands/1.md, commands/2.md, commands/3.md +2 more")
        self.assertIn("A\tcommands/5.md", body)

    def test_move_between_areas_and_delete_split_by_area(self):
        r = self.r
        r.write("commands/x.md", "x\n")
        r.write("hooks/old.py", "old\n")
        r.run()
        base = r.head()
        (r.dir / "skills").mkdir()
        (r.dir / "commands" / "x.md").rename(r.dir / "skills" / "x.md")        # moved to another area
        (r.dir / "hooks" / "old.py").unlink()
        r.run()
        commits = r.commits_since(base)
        self.assertEqual([s.split(":")[0] for s, _, _ in commits],
                         ["auto(Stop) [commands]", "auto(Stop) [hooks]", "auto(Stop) [skills]"])
        self.assertIn("D\tcommands/x.md", commits[0][1])
        self.assertIn("D\thooks/old.py", commits[1][1])
        self.assertIn("A\tskills/x.md", commits[2][1])
        self.assertEqual(r.tracked(), {".gitignore", "skills/x.md"})

    def test_session_start_without_payload(self):
        r = self.r
        r.write("commands/a.md", "a\n")
        base = r.head()
        code, msg = r.run(event="SessionStart", payload=False)
        self.assertEqual(code, 0)
        (subject, body, _), = r.commits_since(base)
        self.assertEqual(subject, "auto(SessionStart) [commands]: commands/a.md")
        self.assertNotIn("session:", body)

    # ---- secret scan -------------------------------------------------------------------------------
    def test_secret_file_kept_out_reported_every_run_until_fixed(self):
        r = self.r
        enc = rand(3000, ALNUM + "_-", 30)
        enc = enc[:1000] + "-s" + "k-" + rand(60, ALNUM, 31) + enc[1000:]
        self.assertTrue(ac.find_secrets(enc), "the fake ciphertext must look like a key to prove the skip")
        r.write("hooks/leak.py", f'KEY = "{SK}"\n')
        r.write("commands/ok.md", "Read task-lists-and-todo-files.md, then musk-share-notes.md.\n")
        r.write("create-clips/scripts/cc_x.py.enc", enc)
        base = r.head()
        code, msg = r.run()
        self.assertEqual(code, 0)
        self.assertIn("NOT committed", msg)
        self.assertIn("hooks/leak.py (sk- key)", msg)
        self.assertNotIn(SK[3:13], msg)                          # never the value
        tracked = r.tracked()
        self.assertNotIn("hooks/leak.py", tracked)
        self.assertIn("commands/ok.md", tracked)
        self.assertIn("create-clips/scripts/cc_x.py.enc", tracked)
        self.assertNotIn("leak.py", (r.dir / ".git" / "info" / "exclude").read_text(encoding="utf-8"))
        self.assertIn("?? hooks/leak.py", r.git("status", "--porcelain", "--untracked-files=all"))
        self.assertEqual(r.git("diff", "--cached", "--name-only"), "")     # nothing left staged
        n = len(r.commits_since(base))
        code, msg = r.run()                                       # still there: reported again, nothing new
        self.assertIn("hooks/leak.py (sk- key)", msg)
        self.assertNotIn("versioned", msg)
        self.assertEqual(len(r.commits_since(base)), n)
        r.write("hooks/leak.py", 'KEY = os.environ["SERVICE_KEY"]\n')     # fixed: committed, no warning
        code, msg = r.run()
        self.assertNotIn("NOT committed", msg)
        self.assertIn("hooks/leak.py", r.tracked())

    def test_tracked_file_gaining_a_secret_keeps_its_last_clean_version(self):
        r = self.r
        r.write("commands/ok.md", "clean\n")
        r.run()
        r.write("commands/ok.md", "clean\n" + ELEVEN)
        r.write("hooks/other.py", "x = 1\n")
        base = r.head()
        code, msg = r.run()
        self.assertIn("commands/ok.md (sk_ key, ELEVEN_API_KEY value)", msg)
        self.assertNotIn(ELEVEN_VALUE[3:20], msg)
        self.assertEqual(r.git("show", "HEAD:commands/ok.md"), "clean\n")
        self.assertEqual([s for s, _, _ in r.commits_since(base)], ["auto(Stop) [hooks]: hooks/other.py"])
        self.assertIn(ELEVEN_VALUE, (r.dir / "commands" / "ok.md").read_text(encoding="utf-8"))  # file untouched

    def test_binary_files_are_not_scanned(self):
        r = self.r
        r.write("static-studio/blob.bin", b"\x00\x01\x02" + SK.encode() + b"\x00" * 64)
        code, msg = r.run()
        self.assertIn("static-studio/blob.bin", r.tracked())
        self.assertNotIn("NOT committed", msg)

    def test_utf16_text_is_scanned(self):
        r = self.r
        r.write("hooks/ps-notes.txt", ("$env:OPENAI" + "_API_KEY = '" + rand(40, ALNUM, 40) + "'\r\n")
                .encode("utf-16"))
        code, msg = r.run()
        self.assertIn("hooks/ps-notes.txt (OPENAI_API_KEY value)", msg)

    def test_literal_paths_and_unicode_names(self):
        r = self.r
        r.write("commands/notes[1].md", f"token {GH}\n")
        r.write("commands/notes1.md", "plain\n")
        r.write("commands/café.md", "plain\n")
        code, msg = r.run()
        self.assertIn("commands/notes[1].md (GitHub token)", msg)
        tracked = r.tracked()
        self.assertNotIn("commands/notes[1].md", tracked)
        self.assertIn("commands/notes1.md", tracked)
        self.assertIn("commands/café.md", tracked)

    def test_secret_scan_failure_commits_nothing(self):
        r = self.r
        r.write("commands/a.md", "a\n")
        base = r.head()
        saved = (ac.ROOT, ac.scan_staged, sys.argv, sys.stdin)
        buf = io.StringIO()

        def boom(_entries):
            raise RuntimeError("scanner broke")
        try:
            ac.ROOT, ac.scan_staged = r.dir, boom
            sys.argv, sys.stdin = ["autocommit.py", "Stop"], io.StringIO("")
            with contextlib.redirect_stdout(buf):
                ac.main()
        finally:
            ac.ROOT, ac.scan_staged, sys.argv, sys.stdin = saved
        self.assertIn("secret scan failed, nothing committed", buf.getvalue())
        self.assertEqual(r.head(), base)
        self.assertEqual(r.git("diff", "--cached", "--name-only"), "")

    # ---- rules kept from before --------------------------------------------------------------------
    def test_big_file_left_out_excluded_and_reported_once(self):
        r = self.r
        r.write("static-studio/huge.bin", b"\0" * ((ac.MAX_MB + 1) * 1024 * 1024))
        r.write("static-studio/small.py", "x = 1\n")
        code, msg = r.run()
        self.assertIn(f"left out 1 file(s) over {ac.MAX_MB} MB: static-studio/huge.bin", msg)
        self.assertIn("/static-studio/huge.bin", (r.dir / ".git" / "info" / "exclude").read_text(encoding="utf-8"))
        self.assertEqual(r.tracked(), {".gitignore", "static-studio/small.py"})
        code, msg = r.run()
        self.assertIsNone(msg)

    def test_new_untracked_top_level_folder_reported_once(self):
        r = self.r
        r.write("newfolder/x.txt", "x\n")
        code, msg = r.run()
        self.assertIn("not tracked", msg)
        self.assertIn("newfolder", msg)
        self.assertIn("newfolder", json.loads((r.dir / ".git" / "autocommit-state.json").read_text())
                      ["reported_untracked"])
        code, msg = r.run()
        self.assertIsNone(msg)

    def test_never_blocks(self):
        r = self.r
        r.write("commands/a.md", "a\n")
        base = r.head()
        lock = r.dir / ".git" / "index.lock"
        lock.write_text("")
        self.assertEqual(r.run(), (0, None))
        lock.unlink()
        merge = r.dir / ".git" / "MERGE_HEAD"
        merge.write_text(base + "\n")
        self.assertEqual(r.run(), (0, None))                    # a merge in progress: hands off
        merge.unlink()
        self.assertEqual(r.head(), base)
        code, msg = r.run(stdin=b"{not json")                     # broken payload: still runs, exit 0
        self.assertEqual(code, 0)
        (subject, body, _), = r.commits_since(base)
        self.assertEqual(subject, "auto(Stop) [commands]: commands/a.md")
        env = dict(r.env, CLAUDE_AUTOCOMMIT_ROOT=str(r.base / "nowhere"), CLAUDE_CONFIG_DIR=str(r.base / "nowhere"))
        cp = subprocess.run([PY, "-B", str(HOOK), "Stop"], input=b"", capture_output=True, env=env, timeout=60)
        self.assertEqual((cp.returncode, cp.stdout), (0, b""))

    def test_one_run_at_a_time(self):
        r = self.r
        r.write("commands/a.md", "a\n")
        base = r.head()
        lock = r.dir / ".git" / "autocommit.lock"
        lock.write_text("")                                       # another run is busy: this one skips
        self.assertEqual(r.run(), (0, None))
        self.assertEqual(r.head(), base)
        old = os.path.getmtime(lock) - ac.LOCK_STALE_S - 5        # left by a killed run: taken over
        os.utime(lock, (old, old))
        code, msg = r.run()
        self.assertIn("[commands]", msg)
        self.assertFalse(lock.exists())

    def test_first_commit_of_an_empty_repository(self):
        r = Repo(first_commit=False)
        try:
            r.write("commands/a.md", "a\n")
            r.write("hooks/b.py", "b\n")
            code, msg = r.run()
            self.assertEqual(code, 0)
            self.assertEqual(r.git("log", "--format=%s").splitlines(),
                             ["auto(Stop) [hooks]: hooks/b.py", "auto(Stop) [config]: .gitignore",
                              "auto(Stop) [commands]: commands/a.md"])
        finally:
            r.close()

    def test_head_moved_by_someone_else_is_kept(self):
        r = self.r
        r.write("commands/a.md", "a\n")
        r.write("hooks/b.py", "b\n")
        r.git("add", "-A")
        saved_root, real_git = ac.ROOT, ac.git
        moved = []

        def someone_else_commits():
            env = dict(r.env, GIT_INDEX_FILE=str(r.dir / ".git" / "other-index"))
            blob = r.git("hash-object", "-w", "--stdin", input=b"outside\n").strip()
            head = r.head()
            r.git("read-tree", head, env=env)
            r.git("update-index", "--add", "--cacheinfo", f"100644,{blob},skills/outside.md", env=env)
            tree = r.git("write-tree", env=env).strip()
            c = r.git("commit-tree", tree, "-p", head, "-m", "outside").strip()
            r.git("update-ref", "HEAD", c, head)

        def racing_git(*args, **kw):
            if args and args[0] == "update-ref" and not moved:
                moved.append(1)
                someone_else_commits()
            return real_git(*args, **kw)
        try:
            ac.ROOT = r.dir
            changes = ac.staged_changes()
            ac.git = racing_git
            made = ac.commit_by_area(changes, "Stop", "abcd1234", r.dir / ".git")
        finally:
            ac.ROOT, ac.git = saved_root, real_git
        self.assertEqual([a for a, _, _ in made], ["commands", "hooks"])
        self.assertEqual(r.git("log", "--format=%s").splitlines(),
                         ["auto(Stop) [hooks]: hooks/b.py", "auto(Stop) [commands]: commands/a.md", "outside", "init"])
        self.assertEqual(r.tracked(), {".gitignore", "commands/a.md", "hooks/b.py", "skills/outside.md"})


class ScannerTest(unittest.TestCase):
    def test_real_shapes_are_found(self):
        for text, name in POSITIVE.items():
            with self.subTest(name=name):
                self.assertIn(name, ac.find_secrets(text))

    def test_look_alikes_and_placeholders_are_not(self):
        for text in NEGATIVE:
            with self.subTest(text=text[:40]):
                self.assertEqual(ac.find_secrets(text), [])

    def test_areas(self):
        self.assertEqual(ac.area_of("settings.json"), "config")
        self.assertEqual(ac.area_of("projects/C--Users-x/memory/MEMORY.md"), "memory")
        self.assertEqual(ac.area_of("static-studio/scripts/static_core.py"), "static-studio")
        self.assertEqual(ac.area_of("plugins/installed_plugins.json"), "plugins")

    def test_the_hook_its_tests_and_docs_hold_no_credential_shape(self):
        for p in (HOOK, Path(__file__), HOOK.parent.parent / "VERSIONING.md"):
            if p.is_file():
                with self.subTest(file=p.name):
                    self.assertEqual(ac.find_secrets(p.read_text(encoding="utf-8")), [])


def tearDownModule() -> None:
    _rmtree(_SAFE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
