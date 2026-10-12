import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t11_common import *

RUN = fresh_run("ledgers")
R30 = Path(RUN) / "30-research"
A20 = Path(RUN) / "20-analysis"

# ---------------------------------------------------------------- the code decides nothing: static checks
src = Path(ATG).read_text(encoding="utf-8")
vb_src = src[src.index("Viral-Browser (analyze_submode=viral-browser)"):src.index("def main():")]
gone = ["_cd_rank", "_cd_pool", "_dominant", "_word_concentration", "_name_overlaps", "_spec_resolve", "_spec_check", "_photo_reference_set", "_photo_summary", "_similar",
        "_tokens", "_is_distinct", "_vocab_signature", "gate_failures", "SequenceMatcher", "difflib", "_photo_angle_hint", "_page_looks_blocked", "ASSET_HINTS"]
word_in = lambda g, text: re.search(r"(?<![A-Za-z0-9_])" + re.escape(g) + r"(?![A-Za-z0-9_])", text)
check(not [g for g in gone if word_in(g, vb_src)], "the helpers that compared texts, counted words, gated or ranked are gone from the Viral-Browser code: " + str([g for g in gone if word_in(g, vb_src)]))
check("ASSET_HINTS" not in src and "name_hints" not in src and "kind_hint" not in src and "likely_noise" not in src and "quick_picks" not in src, "the file-name guesses, the OCR labels and the quick picks are gone from the whole toolkit")
check(not re.search(r"""["']verdict["']\s*[:=]""", src) and not re.search(r"""["']passed_automatic_checks["']""", src), "no command hands out a 'verdict' key any more")
names = ["pet", "pets", "dog", "kitchen", "beauty", "skincare", "fitness", "toys", "gadgets", "jewelry", "fashion", "supplements", "furniture", "garden", "luggage", "stationery", "laundry", "baby", "department"]
hits = [n for n in names if re.search(rf"\b{n}\b", vb_src, re.I)]
check(not hits, f"no niche, product or category name is built into the Viral-Browser code (found: {hits})")
cfgtxt = (LIB / "config.json").read_text(encoding="utf-8")
check(not re.search(r"\b(pets?|kitchen|department|alias)", cfgtxt, re.I), "none in the configuration either")
for old_cmd in (["candidates", "rank"], ["candidates", "pool"], ["candidates", "shortlist"], ["candidates", "score"], ["niches", "distinct"], ["spec", "check"]):
    js, rc, _ = t(old_cmd[0], old_cmd[1], "--run", RUN, ok=False)
    check(rc == 2, f"`{' '.join(old_cmd)}` no longer exists (the decision is the agent's)")

# ---------------------------------------------------------------- niches: a record, no opinions
js, rc, _ = t("niches", "add", "--run", RUN, "--name", "kitchen tools", "--members", "cooking gadgets, kitchen helpers", "--by", "main")
check(js["niches"] == {"kitchen tools": ["cooking gadgets", "kitchen helpers"]}, "a niche is recorded with its labels")
js, rc, _ = t("niches", "add", "--run", RUN, "--name", "kitchen gear")
check(js["notes"] == [], "a look-alike name raises no note: the tool does not compare names")
js, rc, _ = t("niches", "add", "--run", RUN, "--name", "drinkware", "--members", "cooking gadgets")
check(any("moved from niche" in n for n in js["notes"]) and js["niches"]["kitchen tools"] == ["kitchen helpers"] and js["niches"]["drinkware"] == ["cooking gadgets"], "a label an agent re-files MOVES, and the move is noted")
js, rc, _ = t("niches", "map", "--run", RUN, "--label", "pressure washing", "--to", "no such niche", ok=False)
check(rc == 2, "mapping to an unknown niche is refused (a form error)")
js, rc, _ = t("niches", "map", "--run", RUN, "--label", "kitchen gear", "--to", "drinkware", ok=False)
check(rc == 2 and "merge" in js.get("error", ""), "a label that is another niche's name points to merge")
t("niches", "add", "--run", RUN, "--name", "pets", "--members", "pet tools, dog care, pet")
t("niches", "map", "--run", RUN, "--label", "dog toys", "--to", "pets", "--by", "main", "--reason", "same owners")
js, rc, _ = t("niches", "merge", "--run", RUN, "--from", "kitchen gear", "--to", "kitchen tools", ok=False)
check(rc == 2 and "reason" in js.get("error", ""), "a merge needs its reason (any sentence: the tool does not count characters)")
js, rc, _ = t("candidates", "add", "--run", RUN, "--name", "Gear thing", "--definition", "d", "--category", "kitchen gear", "--type", "thing", "--origin", "mechanism")
c_gear = js["added"][0]
js, rc, _ = t("niches", "merge", "--run", RUN, "--from", "kitchen gear", "--to", "kitchen tools", "--reason", "same shelf", "--by", "main")
check("kitchen gear" not in js["niches"] and "kitchen gear" in js["niches"]["kitchen tools"] and any("1 candidate" in n for n in js["notes"]), "merge folds the niche in, keeps its name as a label and renames the candidates")
rec = json.loads((A20 / "niche-vocabulary.json").read_text(encoding="utf-8"))
check(rec["merges"][0]["by"] == "main" and rec["merges"][0]["reason"] == "same shelf" and len(rec["history"]) >= 5, "every decision is on record with who and why")
js, rc, _ = t("niches", "audit", "--run", RUN, "--by", "audit-agent", "--result", "no more merges", "--report", str(R30 / "niche-audit.md"))
check(js["ok"] and (json.loads((A20 / "niche-vocabulary.json").read_text(encoding="utf-8"))["audit"]["by"] == "audit-agent"), "an audit is recorded as given: no file, date or name check")
js, rc, _ = t("niches", "list", "--run", RUN)
check(js["ok"] and "unmapped_labels" in js and "audits" in js, "list tabulates; it reports unmapped labels as a plain list")

# ---------------------------------------------------------------- candidates: decisions recorded, never made
add = lambda name, cat, typ, origin="reference", *x: t("candidates", "add", "--run", RUN, "--name", name, "--definition", "d " + name, "--category", cat, "--type", typ, "--origin", origin, *x)
js, rc, _ = t("candidates", "add", "--run", RUN, "--name", "x", "--definition", "d", "--category", "pets", "--origin", "mechanism", ok=False)
check(rc == 2 and "missing type" in js.get("error", ""), "a missing type is a form error")
js, rc, _ = t("candidates", "add", "--run", RUN, "--name", "x", "--definition", "d", "--category", "pets", "--type", "x", "--origin", "nowhere", ok=False)
check(rc == 2, "an unknown origin is a form error")
js, rc, _ = add("Chip slicer", "cooking gadgets", "slicer")
c1 = js["added"][0]
check(js["niche_not_recorded_in_the_vocabulary"] == [], "a label the agents recorded is stored under their niche")
js, rc, _ = add("Oil sprayer", "spaceships", "sprayer", "mechanism")
c2 = js["added"][0]
check(js["niche_not_recorded_in_the_vocabulary"] == [f"{c2}: spaceships"], "a label nobody recorded is NOT refused: it is stored as written and reported")
js, rc, _ = add("Dog harness", "dog care", "harness", "trend-feed")
c3 = js["added"][0]
js, rc, _ = add("Nozzle kit", "pressure washing", "nozzle kit", "problem-scan")
c4 = js["added"][0]
js, rc, _ = t("candidates", "show", "--run", RUN, "--id", c1)
check(js["ok"], "show prints the record")
# any status from any status, several at once, with who and why
js, rc, _ = t("candidates", "set", "--run", RUN, "--ids", f"{c1},{c2},{c3}", "--status", "researching", "--by", "main", "--reason", "balanced by my reading")
check(js["status"] == {c1: "researching", c2: "researching", c3: "researching"}, "several candidates go to research in one call")
js, rc, _ = t("candidates", "set", "--run", RUN, "--id", c3, "--status", "long", "--by", "main", "--reason", "back to the long list: I want the pool wider")
check(js["status"][c3] == "long", "a candidate in research can go back (no transition guard)")
js, rc, _ = t("candidates", "set", "--run", RUN, "--id", c4, "--status", "eliminated", "--by", "main", "--reason", "margin too thin at the landed cost")
cand_json = json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"]
c4rec = next(c for c in cand_json if c["id"] == c4)
check(c4rec["eliminated_by"] == "margin too thin at the landed cost" and c4rec["history"][-1]["by"] == "main" and c4rec["history"][-1]["changes"]["status"]["to"] == "eliminated", "an elimination keeps the reason and the history")
js, rc, _ = t("candidates", "set", "--run", RUN, "--id", c2, "--name", "Refillable oil sprayer", "--by", "main", "--reason", "clearer name")
check(next(c for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"] if c["id"] == c2)["name"] == "Refillable oil sprayer", "a researched candidate can be edited; the history keeps what changed (no --force)")
js, rc, _ = t("candidates", "set", "--run", RUN, "--id", "C99", "--status", "long", ok=False)
check(rc == 2, "an unknown candidate is refused")
# evidence has no research-status gate; form checks only
ev = lambda cand, lane, claim, src, grade, sig, ind="yes", *x: t("evidence", "add", "--run", RUN, "--cand", cand, "--lane", lane, "--claim", claim, "--source", src, "--grade", grade, "--signal", sig, "--independent", ind, "--opened", "yes", *x, ok=True)
js, rc, _ = t("evidence", "add", "--run", RUN, "--cand", c1, "--lane", "demand", "--claim", "x", "--source", "see notes", "--grade", "B", "--signal", "positive", "--independent", "yes", ok=False)
check(rc == 2 and "URL" in js.get("error", ""), "an independent grade A or B row needs a URL: the one form rule of the ledger")
js, rc, _ = ev(c1, "demand", "search interest up", "https://trends.example.com/x", "B", "positive")
e1 = js["id"]
js, rc, _ = ev(c4, "demand", "eliminated candidate may still get a row", "https://trends.example.com/y", "C", "neutral", "no")
check(js["ok"], "evidence is accepted for a candidate in any status")
js, rc, _ = ev(c1, "competition", "12 sellers", "https://shop.example.org/y", "A", "negative")
e2 = js["id"]
js, rc, _ = ev(c1, "demand", "a method row", "method: price x quantity", "C", "mixed")
js, rc, _ = ev(c1, "economics", "sourced input", "https://supplier.example.net/price", "B", "positive")
js, rc, _ = t("evidence", "list", "--run", RUN, "--cand", c1, "--counts")
cnt = js["counts"]
check(cnt["demand"]["rows"] == 2 and cnt["competition"]["signal"] == {"negative": 1} and cnt["demand"]["sites_behind_positive_grade_A_or_B_rows"] == 1, "list --counts tabulates rows by lane, signal, grade and sites; nothing is weighed: " + str(cnt["demand"]))
js, rc, _ = t("evidence", "retract", "--run", RUN, "--id", e2, "--reason", "the page is a 2019 snapshot", "--by", "red-team")
js, rc, _ = t("evidence", "list", "--run", RUN, "--cand", c1, "--counts")
check("competition" not in js["counts"], "a retracted row stays on record but leaves the counts")
js, rc, _ = t("evidence", "retract", "--run", RUN, "--id", e1, ok=False)
check(rc == 2, "a retraction needs its reason")

# ratings: the agent's own numbers, recorded as given
js, rc, _ = t("candidates", "rate", "--run", RUN, "--id", c1, "--ratings", "demand=6", ok=False)
check(rc == 2, "a rating outside 1-5 is a form error")
js, rc, _ = t("candidates", "rate", "--run", RUN, "--id", c1, "--ratings", "charm=3", ok=False)
check(rc == 2 and "criteria" in js.get("error", ""), "an unknown criterion is a form error")
js, rc, _ = t("candidates", "rate", "--run", RUN, "--id", c1, "--ratings", "demand=4", "--refs", "demand=EV999", ok=False)
check(rc == 2, "a rating cannot cite an evidence row that does not exist for the candidate")
js, rc, _ = t("candidates", "rate", "--run", RUN, "--id", c1, "--ratings", "demand=5,commercial=3,fit=5", "--refs", f"demand={e1}", "--confidence", "high", "--by", "scorer", "--note", "my reading")
check(js["ratings"] == {"demand": 5, "commercial": 3, "fit": 5} and js["weighted_sum_of_rated"] == 44.0 and js["criteria_rated"] == 3, "ratings are stored as given (a 5 on a thin evidence base is NOT capped): weighted sum " + str(js["weighted_sum_of_rated"]))
js, rc, _ = t("candidates", "rate", "--run", RUN, "--id", c2, "--ratings", "demand=2,fit=3", "--by", "scorer")
check(js["weighted_sum_of_rated"] == 18.0 and "economics" in js["criteria_not_rated"], "unrated criteria add nothing; the missing ones are listed, not penalised")
js, rc, _ = t("candidates", "rate", "--run", RUN, "--id", c3, "--ratings", "demand=3,commercial=3,fit=3,economics=3,competition=3,compliance=3,logistics=3,timing=3,producibility=3")
check(js["weighted_sum_of_rated"] == 60.0, "all nine criteria at 3: the weights sum to 100, so 60.0")
check(next(c for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"] if c["id"] == c1)["status"] == "researching", "rating does not move a candidate's status")

# economics per market, side by side
E = ["econ", "--retail", "39.99", "--vat-pct", "19", "--landed", "9.5", "--fulfil", "4", "--platform-fee-pct", "2", "--payment-fee-pct", "2.9", "--payment-fixed", "0.3",
     "--returns-pct", "8", "--currency", "EUR"]
js, rc, _ = t(*E, "--stress", "--moq", "500")
check(js["net_revenue"] == 33.61 and js["fees"] == 2.26 and js["expected_return_loss"] == 2.69 and js["contribution_per_order"] == 15.16 and js["contribution_pct_of_net"] == 45.1, "the arithmetic: " + str((js["net_revenue"], js["fees"], js["contribution_per_order"])))
check(js["break_even_roas_net"] == 2.22 and js["break_even_roas_gross"] == 2.64 and js["capital_at_moq"] == 4750.0 and js["stress"]["all three"]["contribution_per_order"] == 5.79, "break-even ROAS on both bases, capital at the MOQ, the stress case")
check("warnings" not in js and js["inputs_left_at_zero"] == ["return_cost", "resale_pct"], "no warning judges the result; only the inputs left at zero are listed: " + str(js["inputs_left_at_zero"]))
js, rc, _ = t("econ", "--retail", "20", "--landed", "30")
check(js["contribution_per_order"] < 0 and js["break_even_cpa"] == js["contribution_per_order"] and js["break_even_roas_net"] is None, "a losing price is shown as it is: negative contribution, no ROAS, no verdict")
js, rc, _ = t(*E, "--cand", c1, "--run", RUN, ok=False)
check(rc == 2 and "--market" in js.get("error", ""), "--cand needs --market (a form rule)")
t(*E, "--cand", c1, "--run", RUN, "--market", "EU")
t("econ", "--retail", "35", "--landed", "9.5", "--fulfil", "4", "--returns-pct", "8", "--currency", "USD", "--cand", c1, "--run", RUN, "--market", "us")
t("econ", "--retail", "35", "--landed", "9.5", "--fulfil", "4", "--returns-pct", "8", "--currency", "USD", "--cand", c1, "--run", RUN, "--market", "US")
rec1 = next(c for c in json.loads((R30 / "candidates.json").read_text(encoding="utf-8"))["items"] if c["id"] == c1)
check(sorted(rec1["economics_by_market"]) == ["eu", "us"] and "contribution_pct" not in rec1, "each market keeps its own result side by side; no 'lowest counts' number is computed")
evs = json.loads((R30 / "evidence.json").read_text(encoding="utf-8"))["items"]
check([e["signal"] for e in evs if e["lane"] == "economics" and e["grade"] == "C"] == ["calculation"] * 3, "the calculation rows carry no positive/negative signal: the tool does not say whether a margin is good")

# the table
js, rc, out_ = t("candidates", "table", "--run", RUN, "--sort", "rating:demand", "--desc", "--json")
ids = [r["id"] for r in js["rows"]]
check(ids[:3] == [c1, c3, c2] and ids[-2:] and js["sorted_by"] == "rating:demand", "table --sort rating:demand --desc orders by the agent's rating, the unrated last: " + str(ids))
r1 = next(r for r in js["rows"] if r["id"] == c1)
check(r1["economics"]["eu"]["contribution_pct_of_net"] == 45.1 and r1["economics"]["us"]["currency"] == "USD" and r1["evidence"]["rows"] >= 3 and "origin" in r1, "the row carries economics per market, the evidence cell and the origin")
check("winner" not in out_.lower() and "eligible" not in out_.lower() and "gate" not in out_.lower() and "pick" in out_.lower(), "the table marks no winner, no eligibility and no gate")
js, rc, out_ = t("candidates", "table", "--run", RUN, "--blind", "--json", "--exclude-criteria", "fit")
r1 = next(r for r in js["rows"] if r["id"] == c1)
check("origin" not in r1 and "origin" not in out_.splitlines()[0].lower() and r1["weighted_sum_of_rated"] == 24.0 and "without fit" in out_, "--blind hides the origin and --exclude-criteria fit recomputes the plain sum (44 - 20 = 24): " + str(r1["weighted_sum_of_rated"]))
js, rc, _ = t("candidates", "table", "--run", RUN, "--sort", "economics:EU", "--json")
check(js["rows"][0]["id"] == c1, "sorted by a market's contribution")
js, rc, _ = t("candidates", "table", "--run", RUN, "--statuses", "eliminated", "--json")
check([r["id"] for r in js["rows"]] == [c4], "a selection by status is a plain filter")
js, rc, _ = t("candidates", "summary", "--run", RUN, "--exclude-eliminated")
check(js["n"] == 4 and js["statuses"] == {"researching": 2, "long": 2} and sum(js["niches"].values()) == 4 and "flags" not in js, "summary counts by niche, type, origin and status, with no flag: " + str(js["statuses"]))
js, rc, _ = t("candidates", "set", "--run", RUN, "--id", c1, "--status", "picked", "--pick-rank", "1", "--by", "main", "--reason", "highest independent evidence in my reading", "--defence", "x" * 5, "--redteam", "weakened")
js, rc, _ = t("candidates", "table", "--run", RUN, "--json")
check(next(r for r in js["rows"] if r["id"] == c1)["pick_rank"] == 1, "the pick order is the agent's, recorded with --pick-rank")
# a damaged ledger stops the command and is never overwritten
good = (R30 / "candidates.json").read_text(encoding="utf-8")
(R30 / "candidates.json").write_text(good[:200], encoding="utf-8")
js, rc, _ = t("candidates", "set", "--run", RUN, "--id", c1, "--status", "long", ok=False)
check(rc == 1 and "unreadable" in js.get("error", "") and (R30 / "candidates.json").read_text(encoding="utf-8") == good[:200], "a damaged ledger stops the command and is left untouched")
(R30 / "candidates.json").write_text(good, encoding="utf-8")

# ---------------------------------------------------------------- viral-stats: measurements and counts, nothing flagged
for n_, lab in (("V01", "pet tools"), ("V02", "dog care"), ("V03", "cooking gadgets"), ("V04", "a label nobody recorded")):
    p_ = A20 / "cards" / f"{n_}.md"
    txt = p_.read_text(encoding="utf-8")
    p_.write_text(re.sub(r'"category":"[^"]*"', f'"category":"{lab}"', txt, count=1), encoding="utf-8")
js, rc, _ = t("viral-stats", "--run", RUN, "--set", "references")
stats = json.loads((A20 / "corpus-stats.json").read_text(encoding="utf-8"))
refs = stats["sets"]["references"]
txt_stats = json.dumps(stats)
check(not re.search(r"dominant|concentration|hhi|effective_n|small_n|share_music_bed|unresolved|word_concentration", txt_stats), "the statistics file holds no dominance, concentration, small-sample or music-bed verdict")
tab = {r["niche"]: r for r in refs["labels"]["category"]["table"]}
check(tab["pets"]["count"] == 2 and tab["pets"]["recorded_in_vocabulary"] and tab["pets"]["labels"] == {"pet tools": 1, "dog care": 1} and tab["a label nobody recorded"]["recorded_in_vocabulary"] is False,
      "the category table folds labels through the agents' vocabulary and leaves an unrecorded label as written: " + str(sorted(tab)))
check("share_words_found" in refs and "speech_starts_confident_s" in refs and refs["n_videos"] == 4, "the measured profile and the shares are there")
md_stats = (A20 / "corpus-stats.md").read_text(encoding="utf-8")
check("Nothing here is a verdict" in md_stats and "DOMINANT" not in md_stats, "the markdown says that nothing in it is a verdict")
js, rc, _ = t("viral-stats", "--run", RUN, "--set", "references", "--no-niche")
prof = json.loads((A20 / "corpus-profile.json").read_text(encoding="utf-8"))["sets"]["references"]
check("category" not in prof["labels"] and "product_form" not in prof["labels"], "Create's profile leaves the product layer out")

finish()
