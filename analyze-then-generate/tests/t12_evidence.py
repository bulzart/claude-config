"""Evidence ledger round 2: page-opened field, batch add from JSON (all or none), copy rows to other candidates, note/opened columns, the blind
candidate view, and the extra-cost line of `econ`. Records, copies and calculates; no verdicts."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t11_common import *

RUN = fresh_run("evidence2")
R30 = Path(RUN) / "30-research"

add = lambda name, cat, typ, origin="mechanism", *x: t("candidates", "add", "--run", RUN, "--name", name, "--definition", "d " + name, "--category", cat, "--type", typ,
                                                    "--origin", origin, "--origin-note", "came from somewhere", "--mechanisms", "M1,M2", "--note", "Hypothesis: retail 25 to 40; a mature product", *x)
for nm, cat, ty in (("Alpha thing", "tools", "alpha"), ("Beta thing", "tools", "beta"), ("Gamma thing", "pets", "gamma")):
    js, rc, _ = add(nm, cat, ty)
    check(js.get("ok"), f"candidate {nm} added")
ids = [c["id"] for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"]]
c1, c2, c3 = ids[:3]

ev = lambda cand, lane, claim, src, grade, sig, ind="yes", *x, ok=True: t("evidence", "add", "--run", RUN, "--cand", cand, "--lane", lane, "--claim", claim, "--source", src,
                                                                           "--grade", grade, "--signal", sig, "--independent", ind, "--opened", "yes", *x, ok=ok)
rows = lambda: json.loads((R30 / "evidence.json").read_text(encoding="utf-8"))["items"]

# ---------------------------------------------------------------- opened: recorded, tabulated, never judged
js, rc, _ = ev(c1, "economics", "fee 2.9 percent", "https://www.example.com/pricing", "A", "neutral", "yes", "--opened", "yes", "--value", "2.9", "--unit", "%", "--market", "US")
js2, rc2, _ = ev(c1, "demand", "a summary said it is rising", "https://news.example.org/x", "B", "positive", "yes", "--opened", "no")
js3, rc3, _ = t("evidence", "add", "--run", RUN, "--cand", c1, "--lane", "commercial", "--claim", "not stated", "--source", "see notes", "--grade", "D", "--signal", "positive", "--independent", "yes")
r = {e["id"]: e for e in rows()}
check(r["EV001"]["opened"] is True and r["EV002"]["opened"] is False and r["EV003"]["opened"] is None, "opened is recorded as yes / no / not recorded")
js, rc, so = t("evidence", "list", "--run", RUN, "--counts")
check("pages opened" in so and "no 1" in so and "yes 1" in so and "unrecorded 1" in so, "the counts table tabulates the pages opened (no verdict on what that means)")
check("A and B rows by page opened" in so and "A: yes 1" in so and "B: no 1" in so, "and tabulates the A and B rows by page opened, per lane")
js, rc, _ = t("evidence", "add", "--run", RUN, "--cand", c1, "--lane", "demand", "--claim", "x", "--source", "https://a.example", "--grade", "B", "--signal", "positive", "--independent", "yes", ok=False)
check(rc == 2 and "--opened" in js["error"] and "search summary" in js["error"], "a grade B row without the opened declaration is refused (a declaration, not a judgement)")
js, rc, _ = t("evidence", "add", "--run", RUN, "--cand", c1, "--lane", "demand", "--claim", "x", "--source", "https://a.example", "--grade", "A", "--signal", "positive", "--independent", "yes", ok=False)
check(rc == 2 and "--opened" in js["error"], "and so is a grade A row (a grade C or D row needs no declaration: the batch below holds one)")
js, rc, so = t("evidence", "list", "--run", RUN, "--md")
check("| unit |" in so and "| opened |" in so and "| note |" in so and "| % |" in so, "the markdown list shows the unit, the opened flag and the note")
js, rc, _ = ev(c1, "demand", "x", "https://a.example", "B", "positive", "yes", "--opened", "maybe", ok=False)
check(rc != 0, "opened takes yes or no only (argparse)")
js, rc, _ = t("evidence", "add", "--run", RUN, "--cand", c1, "--claim", "x", "--source", "https://a.example", "--grade", "B", "--signal", "positive", "--independent", "yes", ok=False)
check(rc == 2 and "--lane" in js["error"], "the old form check message is kept: evidence add needs --lane")
js, rc, _ = ev(c1, "demand", "x", "see notes", "A", "positive", "yes", ok=False)
check(rc == 2 and "URL" in js["error"], "an independent grade A row without a URL is still refused (the one form rule)")
n0 = len(rows())

# ---------------------------------------------------------------- batch add from JSON: all or none
good = [
    {"cand": c2, "lane": "economics", "claim": "freight table", "source": "https://freight.example/rates", "grade": "B", "signal": "neutral", "independent": "yes",
     "value": "80", "unit": "USD per CBM", "market": "US", "opened": "yes", "note": "it's a quoted rate, with an apostrophe and a \"quote\""},
    {"cand": c2, "lane": "compliance", "claim": "duty of an EU address", "source": "https://eur-lex.europa.eu/x", "grade": "A", "signal": "mixed", "independent": True, "opened": "no"},
    {"cand": c3, "lane": "voice", "claim": "buyers say it is loud", "source": "method: read 20 reviews", "grade": "C", "signal": "negative", "independent": "yes"},
]
gp = Path(RUN) / "batch-good.json"
gp.write_text(json.dumps(good), encoding="utf-8")
js, rc, _ = t("evidence", "add", "--run", RUN, "--from-json", str(gp), "--by", "research agent test")
check(js.get("count") == 3 and len(rows()) == n0 + 3, "a JSON list of rows is written in one go")
r = {e["id"]: e for e in rows()}
last = [r[i] for i in js["ids"]]
check(last[0]["by"] == "research agent test" and last[0]["opened"] is True and "apostrophe" in last[0]["note"] and last[1]["independent"] is True and last[1]["opened"] is False and last[2]["opened"] is None,
      "the batch keeps the fields, the --by default, quotes inside notes, a boolean independent flag, a stated opened flag and no opened flag on a grade C row")
bad = good + [{"cand": "C99", "lane": "demand", "claim": "x", "source": "https://x.example", "grade": "B", "signal": "positive", "independent": "yes"},
              {"cand": c1, "lane": "demand", "claim": "y", "source": "see notes", "grade": "A", "signal": "positive", "independent": "yes"},
              {"cand": c1, "lane": "demand", "claim": "z", "grade": "B", "signal": "positive", "independent": "yes"},
              {"cand": c1, "lane": "demand", "claim": "w", "source": "https://w.example", "grade": "A", "signal": "positive", "independent": "yes"}]
bp = Path(RUN) / "batch-bad.json"
bp.write_text(json.dumps(bad), encoding="utf-8")
n1 = len(rows())
js, rc, _ = t("evidence", "add", "--run", RUN, "--from-json", str(bp), ok=False)
check(rc == 2 and len(rows()) == n1 and "row 4" in js["error"] and "row 5" in js["error"] and "row 6" in js["error"] and "row 7" in js["error"] and "--opened" in js["error"] and "nothing was written" in js["error"],
      "a batch with a bad row writes NOTHING and names every bad row")
js, rc, _ = t("evidence", "add", "--run", RUN, "--from-json", str(Path(RUN) / "nope.json"), ok=False)
check(rc == 2 and len(rows()) == n1, "a missing batch file is a form error")

# ---------------------------------------------------------------- copy: the facts that do not depend on the product
src_ids = ["EV001", "EV004"]
js, rc, _ = t("evidence", "copy", "--run", RUN, "--ids", ",".join(src_ids), "--to", f"{c2},{c3}", "--by", "research agent 2")
check(js.get("count") == 3 and set(js["copies"]) == set(src_ids) and set(js["copies"]["EV004"]) == {c3}, "each row is copied to each target candidate except its own")
r = {e["id"]: e for e in rows()}
cp = r[js["copies"]["EV001"][c2]]
check(cp["cand"] == c2 and cp["claim"] == r["EV001"]["claim"] and cp["source"] == r["EV001"]["source"] and cp["grade"] == "A" and cp["copy_of"] == "EV001"
      and cp["by"] == "research agent 2" and cp["note"].startswith("copy of EV001") and cp["opened"] is True and cp["value"] == "2.9", "a copy keeps the claim, source, grade, value and opened flag and says it is a copy")
js, rc, _ = t("evidence", "copy", "--run", RUN, "--ids", src_ids[0], "--to", f"{c1},{c2}", "--by", "research agent 2")
check(js.get("count") == 1 and c1 not in js["copies"]["EV001"], "a row is never copied onto its own candidate")
cc = js["copies"]["EV001"][c2]
js, rc, _ = t("evidence", "copy", "--run", RUN, "--ids", cc, "--to", c3, "--by", "x")
r = {e["id"]: e for e in rows()}
check(r[js["copies"][cc][c3]]["copy_of"] == "EV001", "a copy of a copy points at the original row")
js, rc, _ = t("evidence", "retract", "--run", RUN, "--id", "EV003", "--reason", "wrong id", "--by", "x")
js, rc, _ = t("evidence", "copy", "--run", RUN, "--ids", "EV003", "--to", c2, "--by", "x", ok=False)
check(rc == 2 and "retracted" in js["error"], "a retracted row is not copied")
js, rc, _ = t("evidence", "copy", "--run", RUN, "--ids", "EV001", "--to", "C99", "--by", "x", ok=False)
check(rc == 2 and "unknown candidate" in js["error"], "an unknown target candidate is refused")
js, rc, _ = t("evidence", "copy", "--run", RUN, "--ids", "EV999", "--to", c2, "--by", "x", ok=False)
check(rc == 2 and "unknown evidence row" in js["error"], "an unknown row is refused")
js, rc, _ = t("evidence", "copy", "--run", RUN, "--ids", "EV001", "--to", c2, ok=False)
check(rc == 2, "copy needs --by")
js, rc, so = t("evidence", "list", "--run", RUN, "--counts")
n_sites = len(set(e["domain"] for e in rows() if e["cand"] == c2 and e["lane"] == "economics"))
check("sites" in so, "the counts still tabulate sites (copies share the original's site, so they add no distinct source)")

# ---------------------------------------------------------------- listing flags: --no-retracted, candidates show --no-copies
js, rc, so = t("evidence", "list", "--run", RUN, "--cand", c1, "--md")
check("wrong id" in so, "the list shows a withdrawn row with its reason")
js, rc, so = t("evidence", "list", "--run", RUN, "--cand", c1, "--md", "--no-retracted")
check("wrong id" not in so and js["count"] == len([e for e in rows() if e["cand"] == c1 and not e.get("retracted")]), "--no-retracted leaves the withdrawn rows out")
js, rc, so = t("candidates", "show", "--run", RUN, "--id", c2)
n_all = js["evidence_rows"]
js, rc, so = t("candidates", "show", "--run", RUN, "--id", c2, "--no-copies")
check(js["copied_rows_not_listed"] >= 1 and js["evidence_rows"] == n_all - js["copied_rows_not_listed"] and "copy of EV001" not in so and "copied shared row" in so,
      "candidates show --no-copies leaves the copied shared rows out and says how many")

# ---------------------------------------------------------------- the blind view: only the product
js, rc, so = t("candidates", "show", "--run", RUN, "--id", c1, "--blind")
txt = so
check(all(w not in txt for w in ("came from somewhere", "Hypothesis", "mature product", "mechanisms", "origin", "history")), "the blind view hides the origin, the mechanisms, the builder's notes and the history")
js, rc, so = t("candidates", "show", "--run", RUN, "--id", c1)
check("Hypothesis" in so and "came from somewhere" in so, "the plain view still shows them (the main session reads it)")
js, rc, so = t("candidates", "list", "--run", RUN, "--blind", "--md")
check("Hypothesis" not in so and "mechanisms" not in so, "the blind list hides them too")

# ---------------------------------------------------------------- econ: the extra line, the formulas
base = ["econ", "--retail", "30", "--vat-pct", "0", "--landed", "8", "--fulfil", "7", "--payment-fee-pct", "2.9", "--payment-fixed", "0.30", "--fees-on", "gross",
        "--returns-pct", "8", "--return-cost", "5", "--currency", "USD", "--stress"]
js, rc, so = t(*base)
check(js["contribution_per_order"] == 11.03 and js["extra_per_unit"] == 0.0 and "extra per unit" not in so, "econ without the extra line is unchanged (contribution 11.03 by hand)")
js, rc, so = t(*base, "--extra-per-unit", "2", "--extra-label", "amortised test and authorised-representative fee")
check(js["contribution_per_order"] == 9.03 and "extra per unit (amortised test and authorised-representative fee)" in so, "the extra cost per unit is subtracted and shown on its own row")
check(js["stress"]["landed +15%"]["contribution_per_order"] == round(9.03 - 8 * 0.15, 2), "the stress cases carry the extra cost and raise only the landed cost")
js, rc, so = t(*base, "--extra-per-unit", "2", "--extra-label", "test fee", "--cand", c2, "--market", "US", "--run", RUN)
cand = [c for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"] if c["id"] == c2][0]
check(cand["economics_by_market"]["us"]["inputs"]["extra_per_unit"] == 2.0 and cand["economics_by_market"]["us"]["inputs"]["extra_label"] == "test fee", "the extra cost and its label are stored with the result's inputs")
check("extra=2.0" in [e for e in rows() if e["id"] == js["evidence_id"]][0]["source"], "and in the method of the grade C economics row")
cp = subprocess.run([PY, "-X", "utf8", ATG, "econ", "--help"], capture_output=True, text=True, encoding="utf-8")
check("return loss" in cp.stdout and "break-even ROAS" in cp.stdout and "capital at the MOQ" in cp.stdout, "the help text shows the formulas")
js, rc, so = t(*base, "--prices", "30,40")
check([x["retail_price"] for x in js["ladder"]] == [30.0, 40.0] and js["ladder"][0]["contribution_per_order"] == js["contribution_per_order"] == 11.03
      and js["ladder"][1]["contribution_per_order"] == 19.94 and "| 40.0 | 40.0 | 19.94 |" in so,
      "econ --prices: the contribution at other retail prices on the same inputs (11.03 at 30 as the main result, 19.94 at 40 by hand)")
js, rc, so = t(*base, "--prices", "30,abc", ok=False)
check(rc == 2 and "--prices" in js["error"], "a price that is not a number is a form error")
js, rc, so = t(*base, "--prices", "35,45", "--cand", c1, "--market", "DE", "--run", RUN)
cand = [c for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"] if c["id"] == c1][0]
check([x["retail_price"] for x in cand["economics_by_market"]["de"]["ladder"]] == [35.0, 45.0], "the ladder is kept with the stored result of that market")

# ---------------------------------------------------------------- econ --shipping-charge: the shipping policy as an input
js, rc, so = t(*base, "--shipping-charge", "4")
check(js["net_revenue"] == 34.0 and js["shipping_net"] == 4.0 and js["contribution_per_order"] == 14.59 and js["contribution_pct_of_net"] == 42.9 and "shipping paid by the customer" in so,
      "a shipping charge of 4 counts as revenue: net revenue 34, fee on 34 gross, return loss on 34 + 5, contribution 14.59 (42.9 % of net) by hand")
js, rc, so = t("econ", "--retail", "25", "--vat-pct", "25", "--landed", "8", "--fulfil", "7", "--payment-fee-pct", "2.9", "--payment-fixed", "0.30", "--fees-on", "gross",
               "--returns-pct", "8", "--return-cost", "5", "--currency", "EUR", "--shipping-charge", "5")
check(js["net_revenue"] == 24.0 and js["shipping_net"] == 4.0 and js["contribution_per_order"] == 5.51 and js["contribution_pct_of_net"] == 23.0 and js["break_even_roas_gross"] == 5.44,
      "with VAT 25 % the charge is taken net of VAT (5 paid = 4 net), the card fee is on the amount paid (30), the contribution is 5.51 by hand")
js, rc, so = t(*base, "--shipping-charge", "4", "--target-pct", "25")
js2, rc2, _ = t(*[x if x != "30" else str(js["price_for_target"]["retail_price"]) for x in base], "--shipping-charge", "4")
check(abs(js2["contribution_pct_of_net"] - 25.0) < 0.1, "the price for a 25 % target with a shipping charge round-trips: feeding it back gives 25 % of the order's net revenue")
js, rc, so = t(*base)
check("shipping_charge" in js and js["shipping_charge"] == 0.0 and js["contribution_per_order"] == 11.03, "free shipping (no flag) leaves every result as before")
js, rc, so = t(*base, "--shipping-charge", "4", "--cand", c3, "--market", "US", "--run", RUN)
cand = [c for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"] if c["id"] == c3][0]
js2, rc2, so2 = t("candidates", "table", "--run", RUN, "--md")
check(cand["economics_by_market"]["us"]["inputs"]["shipping_charge"] == 4.0 and "+ 4 shipping" in so2 and "shipping_charge=4.0" in [e for e in rows() if e["id"] == js["evidence_id"]][0]["source"],
      "the shipping charge is stored with the result's inputs, shown in the candidates table cell and in the method of the grade C row")

# ---------------------------------------------------------------- econ --target-pct: algebra on the same formulas, round trip
us = ["econ", "--retail", "29.99", "--vat-pct", "0", "--landed", "8.92", "--fulfil", "13.5", "--payment-fee-pct", "2.9", "--payment-fixed", "0.30", "--returns-pct", "10",
      "--return-cost", "12.5", "--currency", "USD"]
js, rc, so = t(*us, "--target-pct", "25")
check(js["price_for_target"]["retail_price"] == 38.6 and "reaches 25.0 % of net revenue" in so, "the price for a 25 % contribution on C05's US inputs is 38.60 (hand algebra)")
js2, rc2, _ = t(*[x if x != "29.99" else str(js["price_for_target"]["retail_price"]) for x in us])
check(abs(js2["contribution_pct_of_net"] - 25.0) < 0.1, "feeding that price back gives a contribution of 25 % of net: the solver and the calculation agree")
eu = ["econ", "--retail", "29.99", "--vat-pct", "19", "--landed", "6.08", "--fulfil", "8.89", "--payment-fee-pct", "2.1", "--payment-fixed", "0.30", "--returns-pct", "14",
      "--return-cost", "8.19", "--currency", "EUR"]
js, rc, _ = t(*eu, "--target-pct", "25")
js2, rc2, _ = t(*[x if x != "29.99" else str(js["price_for_target"]["retail_price"]) for x in eu])
check(js["price_for_target"]["retail_price"] == 33.39 and abs(js2["contribution_pct_of_net"] - 25.0) < 0.1, "the same round trip with 19 % VAT included in the price (33.39 EUR)")
js, rc, _ = t(*us, "--target-pct", "95")
check(js["price_for_target"]["retail_price"] is None and "no price reaches" in js["price_for_target"]["note"], "a target no price can reach is reported as such, not as a number")
js, rc, _ = t(*us)
check("price_for_target" not in js, "without --target-pct the output is unchanged")

# ---------------------------------------------------------------- the stored result keeps the price for the target; the table shows it
js, rc, _ = t(*eu, "--target-pct", "25", "--cand", c3, "--market", "EU", "--run", RUN, "--note", "scenario at the ceiling")
cand3 = [c for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"] if c["id"] == c3][0]
check(cand3["economics_by_market"]["eu"]["price_for_target"]["retail_price"] == 33.39 and cand3["economics_by_market"]["eu"]["note"] == "scenario at the ceiling",
      "the stored EU result keeps the price for 25 % and the note")
js, rc, so = t("candidates", "table", "--run", RUN, "--md", "--blind")
check("25 % needs 33.39" in so and "[note]" in so, "the candidates table shows what the target needs beside the contribution, and that a note exists")
js, rc, so = t("candidates", "table", "--run", RUN, "--json", "--blind")
check(any(r["economics"].get("eu", {}).get("retail_for_target") == 33.39 for r in js["rows"]), "and the JSON rows carry it")

# ---------------------------------------------------------------- landed: arithmetic, and a grade C row when asked
lb = ["landed", "--fob", "4.5", "--freight-per-cbm", "260", "--units-per-cbm", "120", "--duty-pct", "3.7", "--duty-extra-pct", "37.5", "--duty-base", "fob", "--other-per-unit", "0.4"]
js, rc, so = t(*lb)
check(js["landed_cost"] == 8.92 and js["freight_per_unit"] == 2.1667 and js["duty"] == 1.854 and "evidence_id" not in js, "landed: 4.50 + 2.17 freight + 1.85 duty (41.2 % of the FOB price) + 0.40 = 8.92; nothing is recorded without --cand")
n_before = len(rows())
js, rc, so = t(*lb, "--cand", c2, "--market", "US", "--run", RUN, "--by", "agent x", "--note", "stack assumed: ordinary 3.7 + 25 + 12.5")
r = {e["id"]: e for e in rows()}
row = r[js["evidence_id"]]
check(len(rows()) == n_before + 1 and row["lane"] == "economics" and row["grade"] == "C" and row["signal"] == "calculation" and row["value"] == "8.92" and row["source"].startswith("method: landed")
      and row["by"] == "agent x" and "stack assumed" in row["note"], "with --cand the build-up is one grade C economics row (signal calculation) with its method")
js, rc, _ = t(*lb, "--cand", c2, "--run", RUN, ok=False)
check(rc == 2 and "--market" in js["error"], "landed --cand without --market is a form error")
js, rc, _ = t(*lb, "--cand", "C99", "--market", "US", "--run", RUN, ok=False)
check(rc == 2 and "unknown candidate" in js["error"], "an unknown candidate is refused")

# ---------------------------------------------------------------- from the scorers: --refs none, retracted rows hidden in show, list --no-copies
js, rc, so = t("candidates", "rate", "--run", RUN, "--id", c2, "--ratings", "demand=1,commercial=2", "--refs", "demand=none commercial=EV004", "--confidence", "low", "--by", "scorer")
cand2 = [c for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"] if c["id"] == c2][0]
check(js.get("ok") and cand2["rating_refs"]["demand"] == [] and cand2["rating_refs"]["commercial"] == ["EV004"], "a rating can say that no evidence row backs it (--refs demand=none): stored as an empty list, not as a missing key")
js, rc, so = t("candidates", "show", "--run", RUN, "--id", c1)
check("EV003" not in so.split("evidence rows:")[1] and js["retracted_rows_not_listed"] == 1 and "retracted row(s) are not listed" in so, "candidates show leaves retracted rows out and says how many")
check("opened yes" in so.split("evidence rows:")[1] and "opened no" in so.split("evidence rows:")[1], "and shows whether each page was opened (the row recorded without the flag is the retracted one, so it is not listed)")
js, rc, so = t("candidates", "set", "--run", RUN, "--id", c2, "--price-fit", "variant", "--compliance", "open", "--by", "scorer", "--reason", "weakest market read")
check(js["stored"][c2]["price_fit"] == "variant" and js["stored"][c2]["compliance"] == "open" and js["stored"][c2]["excluded"] == "no" and js["status"][c2] == js["stored"][c2]["status"],
      "candidates set echoes the fields it stored (gate fields, status, confidence, red team, pick rank, role), so nobody re-reads the record to see them")
js, rc, so = t("candidates", "set", "--run", RUN, "--id", c2, "--price-fit", "unknown", "--by", "scorer", "--reason", "no price read in a market")
check(js["stored"][c2]["price_fit"] == "unknown", "price-fit also takes unknown (no price read in a market)")
js, rc, so = t("evidence", "list", "--run", RUN, "--cand", c3)
n_all = js["count"]
js, rc, so = t("evidence", "list", "--run", RUN, "--cand", c3, "--no-copies")
check(0 < js["count"] < n_all and all(not e.get("copy_of") for e in js["items"]), "evidence list --no-copies leaves out the rows recorded as copies")

# ---------------------------------------------------------------- econ --fixed-annual: a fixed yearly cost spread over a stated volume, on its own row
js, rc, so = t(*base, "--fixed-annual", "11423", "--units-per-year", "3000")
check(js["fixed_cost_per_unit"] == 3.81 and js["contribution_per_order"] == 7.22 and "fixed yearly cost 11423 / 3000 units a year" in so, "a fixed yearly cost is spread over the stated volume (11423 / 3000 = 3.81 per unit) and shown on its own row")
js, rc, so = t(*base, "--fixed-annual", "11423", ok=False)
check(rc == 2 and "--units-per-year" in js["error"], "without the volume it is a form error: the volume is the agent's stated assumption")
js, rc, so = t(*base, "--fixed-annual", "11423", "--units-per-year", "3000", "--target-pct", "25")
js2, rc2, _ = t(*[x if x != "30" else str(js["price_for_target"]["retail_price"]) for x in base], "--fixed-annual", "11423", "--units-per-year", "3000")
check(abs(js2["contribution_pct_of_net"] - 25.0) < 0.1, "the price for a target accounts for the fixed yearly cost (round trip)")

# ---------------------------------------------------------------- evidence list --ids: rows of any candidate, nothing else
js, rc, so = t("evidence", "list", "--run", RUN, "--ids", "EV001,EV004")
check(js["count"] == 2 and {e["id"] for e in js["items"]} == {"EV001", "EV004"} and {e["cand"] for e in js["items"]} == {c1, c2}, "evidence list --ids returns exactly those rows, whichever candidate holds them")
js, rc, so = t("evidence", "list", "--run", RUN, "--ids", "EV001,EV004", "--cand", c2)
check(js["count"] == 1 and js["items"][0]["id"] == "EV004", "and combines with the other plain filters")

# ---------------------------------------------------------------- the code still decides nothing
src = Path(ATG).read_text(encoding="utf-8")
ev_src = src[src.index("def _ev_row_problem"):src.index("# ---- candidate ledger")]
check(not re.search(r"\b(verdict|passes|passed|too (low|high|thin)|weak|strong)\b", ev_src), "the new evidence code hands out no verdict")
finish()
