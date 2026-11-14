"""Tests of the ad marker (the user, 2026-11-14: "just do not skip anything, whether ad or not ad, and the agents then exclude batches of ads when they analyse").

    "C:\\Users\\Bulzart\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" tests\\test_ads.py

The recorder saves the segments Twitch marks as ads as chunks of their own and puts `kind: "ad"` (and `ad: {...}`) in their sidecar. The toolkit passes that
marker on as a FACT (the chunk table, stream.md, `T chunks`, `T blocks`, the reporter's prompt) and never acts on it: the agents judge the batches.
No media is needed: only tables and text.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
CC = SCRIPTS / "cc.py"
PY = sys.executable

failed = 0


def check(cond, msg):
    global failed
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failed += 1


def cc(*args, env=None):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
    last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
    return (json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-400:]}), cp.stdout


def rows_for(kinds, dur=180.0):
    """Chunk rows 1..n: kinds[i] is 'live' or 'ad' (an ad chunk carries kind/ad like the recorder's sidecar says)."""
    rows, t = [], 0.0
    for i, k in enumerate(kinds, 1):
        d = 50.0 if k == "ad" else dur
        r = {"id": f"C{i:04d}", "index": i, "file": f"10-media/C{i:04d}/chunk.mp4", "rec_start_s": round(t, 3), "duration_s": d, "t0_utc": f"2026-11-14T00:{i:02d}:00.000Z",
             "t1_utc": f"2026-11-14T00:{i:02d}:50.000Z", "gap_before_s": 0, "ads_skipped_s": 0, "ended_by": "gap", "status": "done",
             "stages": {s: True for s in ("move", "probe", "audio", "sheets", "transcript", "digest")}}
        if k == "ad":
            r["kind"] = "ad"
            r["ad"] = {"segments_by_range": int(d // 2), "segments_by_title": 0, "titles": ["Amazon|2474283100495.0"] if i % 2 else ["Amazon|2474283100495.0", "Brand|1.0"]}
        rows.append(r)
        t += d
    return rows


def main():
    import cc_common
    import cc_proc
    import cc_report
    import cc_tables

    # 1. batches: consecutive ad-marked chunks are one ad break
    rows = rows_for(["live", "live", "ad", "ad", "live", "ad", "live"])
    b = cc_common.ad_batches(rows)
    check(len(b) == 2 and b[0]["chunks"] == ["C0003", "C0004"] and b[1]["chunks"] == ["C0006"], f"two batches: C0003+C0004 (one break) and C0006: {[x['chunks'] for x in b]}")
    check(b[0]["rec_from"] == 360.0 and b[0]["rec_to"] == 460.0 and b[0]["seconds"] == 100.0 and b[1]["rec_from"] == 640.0 and b[1]["rec_to"] == 690.0,
          f"rec span and seconds come from the chunk table: {[(x['rec_from'], x['rec_to'], x['seconds']) for x in b]}")
    check(b[0]["titles"] == ["Amazon|2474283100495.0", "Brand|1.0"] and b[0]["batch"] == 1 and b[1]["batch"] == 2 and all("_last" not in x for x in b), f"titles merged once, batch numbers: {b[0]['titles']}")
    check(cc_common.ad_batches(rows_for(["live", "live", "live"])) == [] and cc_common.ad_batches([]) == [], "no ad-marked chunk: no batch")
    check(cc_common.ad_batches(rows_for(["ad", "live", "ad"]))[1]["chunks"] == ["C0003"] and len(cc_common.ad_batches(rows_for(["ad", "live", "ad"]))) == 2,
          "an ad chunk at the start (a pre-roll) and one later are two batches")

    # 2. the sidecar's marker goes into the table row, as a fact; a stream sidecar adds nothing
    row = {}
    cc_proc._apply_sidecar(row, {"t0_utc": "x", "kind": "ad", "ad": {"segments_by_range": 5, "segments_by_title": 0, "titles": ["Amazon|1.0"]}, "ended_by": "gap"})
    check(row.get("kind") == "ad" and row["ad"]["segments_by_range"] == 5 and row["ended_by"] == "gap", "_apply_sidecar copies kind and ad into the row")
    row = {}
    cc_proc._apply_sidecar(row, {"t0_utc": "x", "ended_by": "duration"})
    check("kind" not in row and "ad" not in row, "a stream chunk's sidecar has no kind: the row has none")

    with tempfile.TemporaryDirectory(prefix="cc-ads-test-") as tmp:
        tmp = Path(tmp)
        env = {**os.environ, "CC_RUNS_ROOT": str(tmp / "runs"), "CC_NOTIFY": "0"}
        run = tmp / "runs" / "20261114-000000-testch"
        (run / "00-inventory").mkdir(parents=True)
        (run / "state.json").write_text(json.dumps({"schema": "cc/1", "channel": "testch", "session": run.name, "run": str(run)}), encoding="utf-8")
        rows = rows_for(["live", "live", "ad", "ad", "live", "ad", "live", "live"])
        (run / "00-inventory" / "chunks.json").write_text(json.dumps(rows), encoding="utf-8")

        # 3. T blocks: the marker per block and the batches, nothing excluded
        r, _ = cc("blocks", "--run", run, "--chunks", 4, env=env)
        check(r.get("ok") and [x["chunks"] for x in r["blocks"]] == [["C0001", "C0002", "C0003", "C0004"], ["C0005", "C0006", "C0007", "C0008"]],
              "T blocks: every chunk is in a block, the ad-marked ones too (nothing is excluded by a script)")
        check([x["ad_chunks"] for x in r["blocks"]] == [["C0003", "C0004"], ["C0006"]] and [x["chunks"] for x in r["ad_batches"]] == [["C0003", "C0004"], ["C0006"]],
              "T blocks: `ad_chunks` per block and `ad_batches` for the run (facts for the agents)")
        check(r["total_s"] == sum(x["duration_s"] for x in rows), "T blocks: the total length counts every chunk")

        # 4. T chunks marks them
        _, out = cc("chunks", "--run", run, env=env)
        lines = {ln.split()[0]: ln for ln in out.splitlines() if ln.startswith("C0")}
        check("AD-MARKED" in lines["C0003"] and "AD-MARKED" in lines["C0006"] and "AD-MARKED" not in lines["C0001"] and "AD-MARKED" not in lines["C0008"],
              "T chunks prints AD-MARKED on the marked chunks only")

        # 5. stream.md: a marker after the id, the batches below the table, ten-largest lists tagged, nothing left out
        cc_tables.build_stream_md(run, rows, {"session": run.name, "channel": "testch"})
        md = (run / "00-inventory" / "stream.md").read_text(encoding="utf-8")
        check("| C0003 (ad-marked) |" in md and "| C0006 (ad-marked) |" in md and "| C0001 |" in md and "| C0008 |" in md, "stream.md: (ad-marked) after the marked chunk ids, every chunk still has its row")
        check("## Chunks the recorder marked as ads" in md and "| 1 | C0003, C0004 |" in md and "| 2 | C0006 |" in md and "a fact, not a verdict" in md, "stream.md: the batches table says they are a fact, not a verdict")
        check("every recorded chunk counts, an ad-marked one too" in md, "stream.md: rec time counts every chunk")
        cc_tables.build_stream_md(run, rows_for(["live", "live"]), {"session": run.name, "channel": "testch"})
        md2 = (run / "00-inventory" / "stream.md").read_text(encoding="utf-8")
        check("## Chunks the recorder marked as ads" not in md2 and "(ad-marked)" in md2.split("\n")[2] and "| C0001 |" in md2, "stream.md without a marked chunk has no batches section")

        # 6. the reporter's prompt: a marked chunk gets a note that says the marker is a fact and not a verdict; a stream chunk gets none
        inp = {"files": {}, "sheets": []}
        pa = cc_report.build_prompt(run, rows[2], inp, run.name, "testch")
        pl = cc_report.build_prompt(run, rows[0], inp, run.name, "testch")
        check("marked this chunk's segments as ads" in pa and "not a verdict" in pa and "marked this chunk" not in pl, "the reporter's prompt carries the marker as a fact for a marked chunk only")

        # 7. nothing in the toolkit leaves a marked chunk out of the rec axis or the pieces: scripts gather, agents decide
        pieces = cc_common.split_across_chunks(rows, 350.0, 470.0)
        check([p["chunk"] for p in pieces] == ["C0002", "C0003", "C0004", "C0005"], f"a span over ad-marked chunks still resolves to all its pieces (the agents decide what to cut): {[p['chunk'] for p in pieces]}")

        # 8. the real ingest path (no Whisper): a tiny ad-marked chunk from an inbox session reaches the chunk table and stream.md with its marker
        inbox = tmp / "inbox"
        sess = inbox / "testch" / "20261114-010000-testch"
        sess.mkdir(parents=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30", "-f", "lavfi", "-i", "sine=frequency=880:sample_rate=48000",
                        "-t", "6", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "60", "-c:a", "aac", str(sess / "chunk-0001.mp4")], check=True)
        side = {"schema": "tcr/1", "channel": "testch", "session": sess.name, "chunk": 1, "file": "chunk-0001.mp4", "t0_utc": "2026-11-14T01:00:00.000Z", "t1_utc": "2026-11-14T01:00:06.000Z",
                "duration_s": 6.0, "segments": 3, "bytes": 1, "quality": {"name": "720p60"}, "gap_before_s": 0, "ads_skipped_s": 0, "ended_by": "gap", "kind": "ad",
                "ad": {"segments_by_range": 3, "segments_by_title": 0, "titles": ["Amazon|2474283100495.0"]}, "stream": {"id": "1", "title": "t", "game": "g", "viewers": 1, "uptime_s": 5, "started_at": None},
                "tool": {"name": "Twitch Chunk Recorder", "version": "1.1.0"}}
        (sess / "chunk-0001.json").write_text(json.dumps(side), encoding="utf-8")
        env2 = {**env, "CC_INBOX": str(inbox)}
        r, _ = cc("ingest", "--chunk", sess / "chunk-0001.mp4", "--skip-whisper", "--no-refresh", env=env2)
        run2 = tmp / "runs" / sess.name
        got = json.loads((run2 / "00-inventory" / "chunks.json").read_text(encoding="utf-8")) if (run2 / "00-inventory" / "chunks.json").is_file() else []
        check(bool(got) and got[0].get("kind") == "ad" and got[0]["ad"]["titles"] == ["Amazon|2474283100495.0"] and got[0]["stages"]["move"] is True and got[0]["stages"]["sheets"] is True,
              f"a real ingest: the ad-marked chunk is processed like any chunk (sheets made) and its row carries kind and ad: {json.dumps(r)[:200]}")
        check((run2 / "10-media" / "C0001" / "chunk.json").is_file() and json.loads((run2 / "10-media" / "C0001" / "chunk.json").read_text(encoding="utf-8")).get("kind") == "ad",
              "the chunk's own chunk.json (what the reporter reads) keeps the marker")
        md3 = (run2 / "00-inventory" / "stream.md").read_text(encoding="utf-8") if (run2 / "00-inventory" / "stream.md").is_file() else ""
        check("C0001 (ad-marked)" in md3 and "## Chunks the recorder marked as ads" in md3, "stream.md of that run shows the marker and the batch")

    print("ALL PASSED" if not failed else f"FAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
