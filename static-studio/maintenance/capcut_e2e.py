#!/usr/bin/env python3
"""Opt-in end-to-end check of scripts/capcut_tools.py in a SCRATCH CapCut store (never the real one).

The real CapCut MCP server and capcut-cli write a small project (three stills, a narration, two texts); the toolkit adds moves, a
join, a font and a text entrance, repairs the project, and it is read back from its files and through the MCP. Also checks that every
writer refuses while CapCut has the project open. Run it after a CapCut update or a change to capcut_tools.py:

    python "$HOME/.claude/static-studio/maintenance/capcut_e2e.py" [--keep]

Needs: node, capcut-cli on PATH, ffmpeg, Pillow, the capcut MCP server (found through ~/.claude.json) and the template draft in the real
store (copied read-only). CapCut must be closed. Exit 0 = every check passed; the real store is never written.
"""
import hashlib
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
STUDIO = Path(__file__).resolve().parent.parent
TOOL = STUDIO / "scripts" / "capcut_tools.py"
KEEP = "--keep" in sys.argv
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  [{'ok' if ok else 'FAIL'}] {name}" + (f"  - {detail}" if detail and not ok else ""))
    return bool(ok)


class Mcp:
    """a minimal MCP stdio client (newline-delimited JSON-RPC)"""

    def __init__(self, cmd, env, timeout=180):
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True,
                                     encoding="utf-8", errors="replace", bufsize=1)
        self.q, self.n, self.timeout, self.err = queue.Queue(), 0, timeout, []
        threading.Thread(target=self._pump, args=(self.proc.stdout, True), daemon=True).start()
        threading.Thread(target=self._pump, args=(self.proc.stderr, False), daemon=True).start()
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "capcut-e2e", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def _pump(self, stream, is_out):
        for line in stream:
            if is_out and line.strip().startswith("{"):
                try:
                    self.q.put(json.loads(line))
                except ValueError:
                    pass
            elif not is_out:
                self.err.append(line.rstrip())

    def _send(self, obj):
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _rpc(self, method, params):
        self.n += 1
        self._send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params})
        while True:
            msg = self.q.get(timeout=self.timeout)
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result")

    def call(self, name, args=None):
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        text = "\n".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        try:
            return json.loads(text)
        except ValueError:
            return {"raw": text, "isError": res.get("isError")}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            self.proc.kill()


def last_json(text):
    for line in reversed((text or "").strip().splitlines()):
        if line.strip().startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return {}


def main():
    cfg = json.loads((STUDIO / "config.json").read_text(encoding="utf-8"))["capcut"]
    real_store = Path(cfg["drafts_dir"])
    template = cfg["template_draft"]
    claude_json = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
    server = ((claude_json.get("mcpServers") or {}).get("capcut") or {}).get("args", [None])[0]
    if not server or not Path(server).is_file() or not shutil.which("node") or not shutil.which("capcut") or not shutil.which("ffmpeg"):
        print("SKIPPED: needs node, capcut-cli, ffmpeg and the capcut MCP server (~/.claude.json mcpServers.capcut)")
        return 0
    if not (real_store / template).is_dir():
        print(f"SKIPPED: the template draft {template} is not in {real_store}")
        return 0
    tmp = Path(tempfile.mkdtemp(prefix="capcut-e2e-"))
    store, home = tmp / "store", tmp / "home"
    print("scratch folder:", tmp)
    try:
        run(tmp, store, home, real_store, template, server)
    finally:
        if not KEEP:
            shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} checks passed" + (f"; FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


def run(tmp, store, home, real_store, template, server):
    from PIL import Image
    # a scratch store: the template (read-only copy) and the index file a real store has
    store.mkdir()
    shutil.copytree(real_store / template, store / template)
    (store / "root_meta_info.json").write_text(json.dumps({"all_draft_store": [], "draft_ids": 0, "root_path": str(store).replace("\\", "/")}))
    (home / "data").mkdir(parents=True)
    shutil.copyfile(STUDIO / "data" / "capcut-catalogue.json", home / "data" / "capcut-catalogue.json")
    shutil.copyfile(STUDIO / "data" / "capcut-catalogue.md", home / "data" / "capcut-catalogue.md")
    (home / "config.json").write_text(json.dumps({"capcut": {"drafts_dir": str(store).replace("\\", "/"), "template_draft": template, "pro": False,
                                                              "store_lock": str(tmp / "scratch.lock").replace("\\", "/")}}))
    env = {**os.environ, "STUDIO_HOME": str(home), "CAPCUT_DRAFTS_DIR": str(store), "CAPCUT_TEMPLATE_DRAFT": template}
    for i, colour in enumerate(((200, 90, 60), (60, 120, 200)), 1):
        Image.new("RGB", (1920, 1080), colour).save(tmp / f"still{i}.png")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=8", str(tmp / "narration.wav")],
                   check=True)

    def tool(*args):
        cp = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace",
                            env=env, timeout=900)
        return cp.returncode, last_json(cp.stdout)

    cat = json.loads((home / "data" / "capcut-catalogue.json").read_text(encoding="utf-8"))
    free_tr = next(x["slug"] for x in cat["transitions"] if x.get("visible_transition") and not x.get("pro"))
    hidden_tr = next(x["slug"] for x in cat["transitions"] if not x.get("visible_transition"))
    free_in = next(x["slug"] for x in cat["text_intros"] if x.get("visible_animation") and not x.get("pro"))
    pro_in = next(x["slug"] for x in cat["text_intros"] if x.get("pro"))

    print("1. name, clone, prep")
    code, res = tool("capcut-name", "--video", 1, "--date", "2026-11-19", "--store", store)
    name, draft = res.get("name"), Path(res.get("path", ""))
    check("capcut-name gives a free name", code == 0 and name == "19_Nov_2026_v01", res)
    mcp_cmd = ["node", server]
    with Mcp(mcp_cmd, env) as m:
        r = m.call("capcut_clone_draft", {"base": template, "newName": name, "empty": True})
        check("MCP clones the template", draft.is_dir(), r)
        code, res = tool("capcut-prep", "--draft", draft, "--canvas", "1920x1080")
        check("capcut-prep sets the canvas", code == 0 and (res.get("canvas") or {}).get("width") == 1920, res)
        for at, dur, f in ((0, 4, "still1.png"), (4, 4, "still2.png"), (8, 4, "still1.png")):
            m.call("capcut_add_image", {"draft": name, "file": str(tmp / f).replace("\\", "/"), "atSec": at, "durSec": dur})
        m.call("capcut_add_audio", {"draft": name, "file": str(tmp / "narration.wav").replace("\\", "/"), "atSec": 0})
        m.call("capcut_add_text", {"draft": name, "text": "Caption one", "atSec": 1, "durSec": 2, "fontSize": 8, "color": "#FFFFFF"})
        m.call("capcut_add_text", {"draft": name, "text": "Caption two", "atSec": 5, "durSec": 2, "fontSize": 8, "color": "#FFFFFF"})
        v = m.call("capcut_validate", {"draft": name})
        check("MCP validates the built project", v.get("ok") is True, v)
        s = m.call("capcut_save", {"draft": name})
        check("MCP saves it", s.get("saved") == name, s)

    print("2. moves, joins, fonts, text entrances")
    images = tmp / "images.json"
    images.write_text(json.dumps({"fps": 30, "images": [
        {"image": 1, "start": 0.0, "motion": "zoom-in", "amount": 0.06},
        {"image": 2, "start": 4.0, "motion": "pan-right", "amount": 0.05, "transition": free_tr, "trans_s": 0.5},
        {"image": 3, "start": 8.0, "motion": "custom", "scale": [1.0, 1.08], "x": [0.0, 0.03], "y": [0.0, 0.0]}]}))
    code, res = tool("capcut-motion", "--draft", draft, "--timeline", images)
    check("capcut-motion keys every image", code == 0 and res.get("images_without_a_clip") == [], res)
    code, res = tool("capcut-transitions", "--draft", draft, "--timeline", images)
    check("capcut-transitions writes the free join", code == 0 and len(res.get("transitions", [])) == 1, res)
    bad = tmp / "images-bad.json"
    bad.write_text(json.dumps({"images": [{"image": 1, "start": 0.0}, {"image": 2, "start": 4.0, "transition": hidden_tr}]}))
    code, res = tool("capcut-transitions", "--draft", draft, "--timeline", bad)
    check("a transition CapCut does not draw is refused", code == 1 and res.get("failed"), res)
    code, res = tool("capcut-font", "--list")
    fonts = res.get("fonts") or []
    check("capcut-font --list finds fonts", code == 0 and len(fonts) > 0, res)
    if fonts:
        code, res = tool("capcut-font", "--draft", draft, "--font-file", fonts[0]["file"])
        check("capcut-font sets the font on both texts", code == 0 and res["files"][0]["texts_set"] == 2, res)
    code, res = tool("capcut-text-anim", "--draft", draft, "--intro", free_in, "--intro-duration", "0.4")
    check("capcut-text-anim animates both texts", code == 0 and res.get("animated") == 2, res)
    code, res = tool("capcut-text-anim", "--draft", draft, "--intro", pro_in)
    check("a Pro text entrance is refused (this PC has no CapCut Pro)", code == 2, res)

    print("3. repair, then read the project back")
    code, res = tool("capcut-repair", "--draft", draft)
    steps = {s["step"]: s for s in res.get("steps", [])}
    check("capcut-repair: register, link, sync, lint all ran", code == 0 and res.get("ok") and set(steps) >= {"register", "link", "sync-timelines", "lint"}, res)
    check("the media links were written for every clip", (steps.get("link", {}).get("result") or {}).get("linked", 0) > 0
          and (steps.get("link", {}).get("result") or {}).get("media_without_entry") == [], steps.get("link"))
    check("lint found no errors", ((steps.get("lint", {}).get("result") or {}).get("summary") or {}).get("errors") == 0, steps.get("lint"))
    content = json.loads((draft / "draft_content.json").read_text(encoding="utf-8"))
    main_track = next(t for t in content["tracks"] if t["type"] == "video")
    kf = [[k.get("property_type") for k in s.get("common_keyframes") or []] for s in main_track["segments"]]
    check("the moves are keyframed (scale on image 1, scale and position on images 2 and 3)",
          "KFTypeScaleX" in kf[0] and "KFTypePositionX" in kf[1] and "KFTypeScaleX" in kf[2] and "KFTypePositionX" in kf[2], kf)
    mats = content["materials"]
    check("every media material has its local_material_id", all(x.get("local_material_id") for k in ("videos", "audios") for x in mats.get(k) or []))
    check("the join is in the project", [x.get("name") for x in mats.get("transitions") or []] != [])
    check("both texts carry the entrance", len([a for m_ in mats.get("material_animations") or [] for a in m_.get("animations") or []]) == 2)
    index = json.loads((store / "root_meta_info.json").read_text(encoding="utf-8-sig"))
    check("the scratch store's index lists the project", name in [d.get("draft_name") for d in index.get("all_draft_store", [])])
    with Mcp(["node", server], env) as m:
        back = m.call("capcut_read_timeline", {"draft": name})
        kinds = {t["type"]: len(t["segments"]) for t in back.get("tracks", [])}
        check("a fresh MCP reads the repaired project back", kinds == {"video": 3, "audio": 1, "text": 2} and back.get("durationSec") == 12, back)

    print("4. every writer refuses while CapCut has the project open")
    before = {n: hashlib.sha256((draft / n).read_bytes()).hexdigest() for n in ("draft_content.json", "draft_meta_info.json")}
    (draft / ".locked").write_text("")
    codes = [tool(*a)[0] for a in (("capcut-prep", "--draft", draft), ("capcut-motion", "--draft", draft, "--timeline", images),
                                  ("capcut-transitions", "--draft", draft, "--timeline", images), ("capcut-font", "--draft", draft, "--font-file", "x.ttf"),
                                  ("capcut-text-anim", "--draft", draft, "--intro", free_in), ("capcut-repair", "--draft", draft))]
    (draft / ".locked").unlink()
    after = {n: hashlib.sha256((draft / n).read_bytes()).hexdigest() for n in before}
    check("all six refuse", all(c != 0 for c in codes), codes)
    check("and change nothing", before == after)
    check("the real store was not written", not (real_store / name).exists())


if __name__ == "__main__":
    sys.exit(main())
