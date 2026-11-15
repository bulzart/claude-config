"""Test of the chat heat (cc_heat.py, `cc.py heat`): 4-second bins of rec time against the stream's own baseline, the bursts, one span, a block file's unmentioned bursts.

    python tests/test_heat.py

A synthetic run: a chat that starts 20 s late (not connected yet), a chunk that starts at a fractional rec time (180.04), an ad-marked chunk with no chat file, a capture dropout (60 s of exact zeros while the
chat is normally busy), a burst full of `!` commands, a burst right after the ad, and a short last chunk. Numbers only: the test checks the facts, never a verdict.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import cc_crypto_loader  # noqa: E402,F401

failed = 0


def check(cond, msg):
    global failed
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failed += 1


QUIET = [1, 1, 2, 1]            # 5 messages per 4 s
LOUD = [8, 8, 7, 7]             # 30 messages per 4 s


def per_second(n, bursts=(), zeros=(), lead_zero=0):
    """n seconds of the quiet pattern; `bursts` = offsets (multiples of 4) of a loud bin; `zeros` = (from, to) offsets with no message at all."""
    v = [QUIET[i % 4] for i in range(n)]
    for b in bursts:
        v[b:b + 4] = LOUD
    for a, z in zeros:
        v[a:z] = [0] * (z - a)
    for i in range(lead_zero):
        v[i] = 0
    return v


def chat_file(i, per, tokens=None, samples=None):
    return {"schema": "tcr-chat/1", "chunk": i, "t0_utc": "2026-11-15T00:00:00Z", "duration_s": len(per), "bin_s": 1, "lag_hint_s": 8, "per_second": per,
            "tokens_per_10s": tokens or [[] for _ in range((len(per) + 9) // 10)], "samples": samples or []}


def make_run(tmp: Path, with_chat=True) -> Path:
    run = tmp / "run"
    (run / "00-inventory").mkdir(parents=True)
    (run / "state.json").write_text(json.dumps({"schema": "cc/1", "channel": "tester", "session": "heat-test"}), encoding="utf-8")
    spec = [("C0001", 1, 0.0, 180.0, None), ("C0002", 2, 180.04, 179.96, None), ("C0003", 3, 360.0, 30.0, "ad"), ("C0004", 4, 390.0, 180.0, None),
            ("C0005", 5, 570.0, 180.0, None), ("C0006", 6, 750.0, 12.0, None)]
    rows = []
    for cid, idx, rec0, dur, kind in spec:
        row = {"id": cid, "index": idx, "rec_start_s": rec0, "duration_s": dur, "status": "done"}
        if kind:
            row["kind"] = kind
        rows.append(row)
    (run / "00-inventory" / "chunks.json").write_text(json.dumps(rows), encoding="utf-8")
    chats = {
        "C0001": chat_file(1, per_second(180, bursts=(100,), lead_zero=20),
                           tokens=[[] for _ in range(10)] + [[["KEKW", 40], ["!join", 25], ["LUL", 9]]] + [[] for _ in range(7)],
                           samples=[{"t": 101.0, "text": "KEKW KEKW"}, {"t": 102.5, "text": "!join now"}, {"t": 103.0, "text": "no way"}, {"t": 50.0, "text": "early message"}]),
        "C0002": chat_file(2, per_second(180)),
        "C0004": chat_file(4, per_second(180, bursts=(10,)), tokens=[[["F", 30], ["LUL", 4]]] + [[["F", 30], ["LUL", 4]]] + [[] for _ in range(16)]),
        "C0005": chat_file(5, per_second(180, zeros=[(30, 90)])),
        "C0006": chat_file(6, per_second(12)),
    }
    if with_chat:
        for cid, ch in chats.items():
            d = run / "10-media" / cid
            d.mkdir(parents=True)
            (d / "chat.json").write_text(json.dumps(ch), encoding="utf-8")
    else:
        for cid in chats:
            (run / "10-media" / cid).mkdir(parents=True)
    return run


def cc(*args):
    cp = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "cc.py"), *args], capture_output=True, text=True, encoding="utf-8")
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    return json.loads(lines[-1]) if lines else {}, cp.stdout, cp.returncode


def main():
    import cc_heat as H

    with tempfile.TemporaryDirectory(prefix="cc-heat-test-") as tmp:
        tmp = Path(tmp)
        run = make_run(tmp)
        P = H.params()
        check(P["bin_s"] == 4 and P["burst_min_z"] == 4 and P["baseline_half_bins"] == 37, f"the settings come from config.json -> chat (4 s bins, z >= 4, +-37 bins): {P['bin_s']}, {P['burst_min_z']}, {P['baseline_half_bins']}")

        h = H.build(run, P)
        S = h["series"]
        n = S["n"]
        check(h["has_chat"] and len(n) == 191, f"one series for the whole run: {len(n)} bins of 4 s (762 s)")
        check(all(x is None for x in n[:5]) and n[5] is not None, "the 20 s before the first message are no data (the chat was not connected yet), not a quiet chat")
        check(h["capture"]["first_msg_rec"] == 20.0, f"the first message is at rec 20 s: {h['capture']['first_msg_rec']}")
        check(n[25] is not None and abs(n[25] - 30) < 1e-6, f"the loud bin at rec 100 holds its 30 messages: {n[25]}")
        # conservation: the messages of all the covered bins match the per-second counts (a fractional chunk start loses and doubles nothing)
        total_chat = sum(sum(json.loads((run / '10-media' / c / 'chat.json').read_text(encoding='utf-8'))['per_second']) for c in ("C0001", "C0002", "C0004", "C0005", "C0006"))
        got = sum(x for x in n if x is not None)
        check(abs(got - total_chat) <= 6, f"no message lost or counted twice across the chunk joins: {got:.1f} in the bins, {total_chat} in the files (the 2 s partial last bin has no data)")
        check(n[45] is not None and 4 <= n[45] <= 6 and n[46] is not None, f"the bins over the fractional chunk start (rec 180.04) stay at the quiet level: {n[44]:.1f} {n[45]:.1f} {n[46]:.1f}")
        check(n[190] is None, "the last 2 s of the run are too short for a bin: no data")

        # the ad chunk and the dropout
        check(any(m["chunk"] == "C0003" and "ad-marked" in m["why"] for m in h["capture"]["no_chat_chunks"]) and all(x is None for x in n[90:97]), "the ad-marked chunk has no chat and its bins are no data")
        gaps = h["capture"]["gaps"]
        check(len(gaps) == 1 and gaps[0]["rec_from"] == 600.0 and gaps[0]["rec_to"] == 660.0 and gaps[0]["seconds"] == 60.0, f"a capture dropout of 60 s is listed and left out: {gaps}")
        check(all(x is None for x in n[150:165]) and n[165] is not None, "the dropout's bins are no data and the chat after it is read against the baseline from before")

        # the bursts
        B = h["bursts"]
        check([b["id"] for b in B] == ["H001", "H002"], f"two bursts, in time order: {[b['id'] for b in B]}")
        b1, b2 = B
        check(b1["peak_rec"] == 100.0 and b1["onset_rec"] == 100.0 and b1["end_rec"] == 104.0 and b1["chunk"] == "C0001" and b1["peak_offset_s"] == 100.0, f"burst 1 is the loud bin at rec 100: {b1['onset_rec']}-{b1['end_rec']} peak {b1['peak_rec']}")
        check(b1["n_peak"] == 30.0 and b1["base"] == 5.0 and abs(b1["z"] - (30 - 5) / 6 ** 0.5) < 0.02 and abs(b1["ratio"] - 31 / 6) < 0.01 and b1["pct"] > 95, f"n 30 vs base 5: z {b1['z']}, ratio {b1['ratio']}, pct {b1['pct']}")
        check(b1["tokens"][0] == ["KEKW", 40] and b1["command_tokens"] == 25 and b1["commands"] == [["!join", 25]], f"what chat said: tokens {b1['tokens'][:2]}, {b1['command_tokens']} command messages {b1['commands']}")
        check(b1["top_token_per_msg"] == round(40 / 30, 2) and [s["text"] for s in b1["samples"]] == ["KEKW KEKW", "!join now", "no way"], f"samples inside the span only, in time order, and the share of the top token: {b1['top_token_per_msg']}")
        check(b1["sample_n"] == 3 and b1["avg_words"] == 2.0 and b2["avg_words"] is None and h["stream"]["avg_words"] == 2.0, f"the length of what was typed (a published clue: short messages are reactions): {b1['sample_n']} sampled messages, {b1['avg_words']} words each, none sampled in burst 2")
        check(b1["after_ad_s"] is None and b2["after_ad_s"] == 10.0, f"a burst 10 s after an ad-marked chunk says so, one far from any ad does not: {b2['after_ad_s']}")
        check(b2["peak_rec"] == 400.0 and b2["chunk"] == "C0004" and b2["tokens"][0] == ["F", 30], f"burst 2 is in C0004 at rec 400 with F x30 (the 10 s window 400-410 over it; the window that ends at 400 does not overlap it): {b2['peak_rec']} {b2['tokens'][:1]}")

        # the per-chunk table
        T = {c["chunk"]: c for c in h["chunks"]}
        check(T["C0003"]["msgs"] is None and "ad-marked" in (T["C0003"]["note"] or ""), "the ad-marked chunk has no chat in the table")
        check(T["C0001"]["bursts"] == 1 and T["C0004"]["bursts"] == 1 and T["C0002"]["bursts"] == 0 and 0 <= T["C0001"]["hot_share"] <= 1, "the table counts the bursts per chunk and the hot share")
        check(T["C0001"]["max_n"] == 30.0 and T["C0001"]["max_n_rec"] == 100.0, "the table names the busiest bin of a chunk")

        # the files, and the command end to end
        res, stdout, rc = cc("heat", "--run", str(run))
        md = (run / "20-analysis" / "heat.md").read_text(encoding="utf-8")
        check(rc == 0 and res.get("ok") and res["has_chat"] and res["bursts"] == 2 and res["capture_gaps"] == 1 and res["no_chat_chunks"] == ["C0003"], f"`cc.py heat` builds the files and answers with the counts: {res.get('bursts')} bursts")
        check((run / "20-analysis" / "heat.json").is_file() and "| H001 |" in md and "| H002 |" in md and "10 s after an ad-marked chunk" in md and "commands !join x25" in md and "Capture gaps" in md,
              "heat.md lists the bursts with what chat said, the commands, the ad and the capture gap")
        check("good moment" not in md.lower() and "hot!" not in md.lower(), "no row calls anything good or hot: numbers only")
        res2, _, _ = cc("heat", "--run", str(run), "--min-z", "20")
        check(res2["bursts"] == 0, "another setting (--min-z 20) lists no burst: the settings are the caller's")
        cc("heat", "--run", str(run))                      # back to the defaults

        # one span
        res, stdout, rc = cc("heat", "--run", str(run), "--from", "96", "--to", "112")
        check(res["peak_rec"] == 100.0 and res["bursts"] == ["H001"] and res["tokens"][0] == ["KEKW", 40] and res["covered_bins"] == 4 and abs(res["msgs"] - (5 + 30 + 5 + 5)) <= 1, f"a span: peak at 100, burst H001, tokens, {res['msgs']} messages in {res['covered_bins']} bins")
        check("sample" in stdout and "chat says: KEKW x40" in stdout and "words per sampled message: 2.0 over 3" in stdout, "the span view prints the numbers, what chat said, the message length and the sample lines")
        res, stdout, _ = cc("heat", "--run", str(run), "--from", "0", "--to", "540", "--rows")
        check("per chunk:" in stdout and "| C0001 |" in stdout and "| C0004 |" in stdout and "| H001 |" in stdout and "| H002 |" in stdout and "| C0005 |" not in stdout,
              "--rows prints the heat.md rows of the chunks and bursts inside the span only (a block's rows without the whole file)")
        res, stdout, _ = cc("heat", "--run", str(run), "--from", "200", "--to", "230", "--rows")
        check("(none in this span)" in stdout, "--rows on a span with no burst says so")
        res, _, _ = cc("heat", "--run", str(run), "--from", "200", "--to", "230")
        check(res["bursts"] == [] and res["z_peak"] < 3, "a quiet span has no burst and a small z")
        res, _, _ = cc("heat", "--run", str(run), "--from", "C0004+10", "--to", "C0004+20")
        check(res["peak_rec"] == 400.0, "a span can be given as chunk + offset")

        # the block file: what nobody mentioned
        block = {"block": 1, "rec_from": 0, "rec_to": 540, "moments": [{"id": "B01-M01", "rec_from": 90.0, "rec_to": 108.0, "setup_from": 84.0}], "heat_review": []}
        bp = tmp / "block-01.json"
        bp.write_text(json.dumps(block), encoding="utf-8")
        res, stdout, _ = cc("heat", "--run", str(run), "--coverage", str(bp))
        check(res["bursts_in_block"] == ["H001", "H002"] and [c["id"] for c in res["covered"]] == ["H001"] and [u["id"] for u in res["unmentioned"]] == ["H002"],
              f"a moment that spans the burst covers it; the other is unmentioned: {res['covered']} / {[u['id'] for u in res['unmentioned']]}")
        check("unmentioned H002" in stdout, "the unmentioned bursts are printed with their numbers")
        block["heat_review"] = [{"burst": "H002", "why": "the ad return"}]
        bp.write_text(json.dumps(block), encoding="utf-8")
        res, _, _ = cc("heat", "--run", str(run), "--coverage", str(bp))
        check(res["unmentioned"] == [] and {c["id"]: c["by"] for c in res["covered"]}["H002"] == "named", "a heat_review entry that names the burst covers it")
        block["heat_review"] = [{"rec": 402.0, "why": "same, by time"}]
        bp.write_text(json.dumps(block), encoding="utf-8")
        res, _, _ = cc("heat", "--run", str(run), "--coverage", str(bp))
        check(res["unmentioned"] == [], "a heat_review entry that gives a rec time inside the burst covers it too")
        block.update({"heat_review": [], "moments": [{"id": "B01-M02", "rec_from": 300.0, "rec_to": 330.0, "heat": {"burst": "H001"}}]})
        bp.write_text(json.dumps(block), encoding="utf-8")
        res, _, _ = cc("heat", "--run", str(run), "--coverage", str(bp))
        check([u["id"] for u in res["unmentioned"]] == ["H002"] and {c["id"]: c["by"] for c in res["covered"]}["H001"] == "named", "a moment that names its burst in `heat.burst` covers that burst wherever the moment lies")
        game = {"block": 2, "rec_from": 0, "rec_to": 540, "units": [{"id": "R01", "rec_from": 95.0, "rec_to": 120.0}], "non_play": [{"kind": "ad", "rec_from": 395.0, "rec_to": 420.0}]}
        bp.write_text(json.dumps(game), encoding="utf-8")
        res, _, _ = cc("heat", "--run", str(run), "--coverage", str(bp))
        check(res["unmentioned"] == [], "a game unit and a non-play span cover the bursts that lie in them")

        # the blocks list carries the ids
        res, _, _ = cc("blocks", "--run", str(run), "--chunks", "3")
        check([b["bursts"] for b in res["blocks"]] == [["H001"], ["H002"]], f"`cc.py blocks` lists each block's bursts: {[b['bursts'] for b in res['blocks']]}")

    # a run with no chat at all
    with tempfile.TemporaryDirectory(prefix="cc-heat-test-") as tmp:
        run = make_run(Path(tmp), with_chat=False)
        res, _, rc = cc("heat", "--run", str(run))
        md = (run / "20-analysis" / "heat.md").read_text(encoding="utf-8")
        check(rc == 0 and res["has_chat"] is False and "No heat" in md, "a run with no chat files says so and makes no heat")
        res, _, _ = cc("heat", "--run", str(run), "--from", "10", "--to", "40")
        check(res["has_chat"] is False, "a span of a run with no chat answers that there is no heat")
        res, _, _ = cc("blocks", "--run", str(run), "--chunks", "3")
        check(all(b["bursts"] == [] for b in res["blocks"]), "the blocks of a run with no chat have no bursts")

    # a chat that was never connected (all zeros) is no heat either
    with tempfile.TemporaryDirectory(prefix="cc-heat-test-") as tmp:
        run = make_run(Path(tmp))
        for c in ("C0001", "C0002", "C0004", "C0005", "C0006"):
            p = run / "10-media" / c / "chat.json"
            j = json.loads(p.read_text(encoding="utf-8"))
            j["per_second"] = [0] * len(j["per_second"])
            p.write_text(json.dumps(j), encoding="utf-8")
        res, _, _ = cc("heat", "--run", str(run))
        check(res["has_chat"] is False, "chat files that hold no message at all are no heat")

    print("ALL PASSED" if not failed else f"FAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
