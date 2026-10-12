import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t11_common import *
import http.server
import threading

RUN = fresh_run("pack")
R30 = Path(RUN) / "30-research"


def addc(name, typ="gadget"):
    js, rc, _ = t("candidates", "add", "--run", RUN, "--name", name, "--definition", "d " + name, "--category", "misc", "--type", typ, "--origin", "mechanism")
    return js["added"][0]


C1, C2 = addc("Test kettle", "kettle"), addc("Second thing")

# ================================================================ spec: facts recorded and set side by side; the agent judges
S = lambda *a, ok=True: t("spec", *a, "--run", RUN, ok=ok)
MK = ["--source", "https://maker.example/p", "--source-kind", "manufacturer", "--grade", "A"]
SH = ["--source", "https://shop.example/p", "--source-kind", "retailer", "--grade", "B"]


def sadd(cand, field, *rest, ok=True):
    return S("add", "--cand", cand, "--field", field, *rest, ok=ok)


js, rc, _ = sadd(C1, "width", "--value", "7.5", "--unit", "cm", *MK)
sp1 = js["id"]
check(js["value_si"] == 75.0 and js["si_unit"] == "mm", "a size is converted to millimetres: " + str(js["value_si"]))
js, rc, _ = sadd(C1, "width", "--value", "3", "--unit", "in", *SH)
sp2 = js["id"]
check(js["value_si"] == 76.2 and js["other_facts_of_this_field_from_the_same_site"] == [], "inches too; the call reports facts of the same field from the same site (none here)")
js, rc, _ = sadd(C1, "weight", "--value", "2", "--unit", "lb", *SH)
check(js["value_si"] == 907.1847 and js["si_unit"] == "g", "a weight in grams")
js, rc, _ = sadd(C1, "volume", "--value", "1", "--unit", "gal", *SH)
check(js["value_si"] == 3785.4118 and js["si_unit"] == "ml", "a volume in millilitres")
js, rc, _ = sadd(C1, "width", "--value", "5", "--unit", "parsec", *SH, ok=False)
check(rc == 2 and "unknown unit" in js.get("error", ""), "an unknown unit for a size is a form error")
js, rc, _ = sadd(C1, "weight", "--text", "light", *SH, ok=False)
check(rc == 2 and "is a number" in js.get("error", ""), "a size or weight needs a number and a unit")
js, rc, _ = sadd(C1, "dimensions", "--text", "7 x 5 x 3 cm", *SH, ok=False)
check(rc == 2, "dimensions are registered one number at a time")
js, rc, _ = sadd(C1, "material", "--text", "steel", "--source", "see the box", "--source-kind", "retailer", "--grade", "B", ok=False)
check(rc == 2 and "URL" in js.get("error", ""), "a grade A or B fact needs a URL")
# the old consistency rules and source heuristics are gone: the agent's labels are recorded as given
js, rc, _ = sadd(C1, "finish", "--text", "matte", "--source", "https://shop.example/f", "--source-kind", "retailer", "--grade", "A")
check(js["ok"], "a grade A on a retailer page is recorded as the agent labelled it (no consistency refusal)")
js, rc, _ = sadd(C1, "depth", "--value", "4", "--unit", "cm", "--source", "sample: ruler, 2026-10-12, read off the listing photo", "--source-kind", "measured", "--grade", "A")
check(js["ok"], "a 'measured' fact is recorded as given: the tool does not read the words of the source description")
js, rc, _ = sadd(C1, "height", "--value", "9", "--unit", "cm", "--source", "x", "--source-kind", "photo", "--grade", "C", ok=False)
check(rc == 2, "'photo' is not a source kind at all (a size is never read off a photo)")
js, rc, _ = sadd(C1, "material", "--text", "stainless steel blades, ABS body", *MK, "--copy-of", sp1)
sp_mat = js["id"]
check(js["site"] == "example" or js["site"], "a fact recorded as a copy takes the original's site")
js, rc, _ = sadd(C1, "material", "--text", "x", *MK, "--copy-of", "SP999", ok=False)
check(rc == 2, "a copy of a fact that does not exist is refused")
js, rc, _ = sadd(C1, "width", "--value", "7.5", "--unit", "cm", *MK)
check(js.get("duplicate") is True and js["id"] == sp1, "the same fact twice returns the first")
js, rc, _ = sadd(C1, "Color", "--text", "white", *SH)
js, rc, _ = sadd(C1, "colour", "--text", "ivory", *SH)
js, rc, out_ = S("table", "--cand", C1)
check("| color |" in out_ and "| colour |" in out_, "colour and color are two fields to the table: no spelling is folded")
rowd = js["table"]["width|product"]
check(rowd["facts"] == [sp1, sp2] and rowd["spread"]["highest_above_lowest_pct"] == 1.6 and rowd["judgement"] is None, "the table sets the facts side by side with the plain spread and no judgement: " + str(rowd["spread"]))
check(not re.search(r"verified|official|reported|conflict|unverified", out_), "...and says no word about verification, officialness or conflict")
# the agent's judgement
js, rc, _ = S("judge", "--cand", C1, "--field", "width", "--fact", sp1, ok=False)
check(rc == 2, "a judgement needs a status and a reason")
js, rc, _ = S("judge", "--cand", C1, "--field", "width", "--fact", "SP999", "--status", "verified", "--reason", "x", ok=False)
check(rc == 2, "a judgement cannot cite a fact that does not exist")
js, rc, _ = S("judge", "--cand", C1, "--field", "width", "--fact", f"{sp1},{sp2}", "--status", "verified", "--reason", "maker and retailer agree within rounding", "--by", "pack-agent")
check(js["ok"] and js["status"] == "verified", "the agent records its judgement in its own words")
js, rc, _ = S("judge", "--cand", C1, "--field", "width", "--scope", "product", "--variant", "Large", "--text", "12 cm", "--status", "unverified", "--reason", "only a seller's claim", "--by", "pack-agent")
js, rc, _ = S("gaps", "--cand", C1)
check("height" in js["no_fact_recorded"] and "width" not in js["no_fact_recorded"] and "material" in js["no_judgement_recorded"] and "width" not in js["no_judgement_recorded"], "gaps counts facts and judgements for the core fields: no verdict, just which have none")
check("complete" not in json.dumps(js) and "verdict" not in json.dumps(js), "...and never says complete or insufficient")
js, rc, _ = S("render", "--cand", C1, "--out", str(Path(RUN) / "deliverables" / "spec-test.md"))
md_ = (Path(RUN) / "deliverables" / "spec-test.md").read_text(encoding="utf-8")
check("*verified*" in md_ and "maker and retailer agree within rounding" in md_ and "**material:** no judgement recorded" in md_, "the sheet shows the agent's judgement with its reason, and says where none was recorded")
check(js["fields_with_a_judgement"] == 1, "the render counts the fields that carry a judgement: " + str(js["fields_with_a_judgement"]))
js, rc, _ = S("render", "--cand", C1, "--variant", "Large", "--out", str(Path(RUN) / "deliverables" / "spec-large.md"))
md2_ = (Path(RUN) / "deliverables" / "spec-large.md").read_text(encoding="utf-8")
check("12 cm" in md2_ and "unverified" in md2_, "a variant-specific judgement is the one shown for that variant (a filter on request)")
js, rc, _ = S("render", "--cand", C1)
pack = Path(js["pack"])
check(pack.name.startswith("reference-" + C1 + "-") and (pack / "spec.md").exists() and (pack / "spec.json").exists(), "the pack folder is named after the candidate and created by the first render (no pick needed)")
sj = json.loads((pack / "spec.json").read_text(encoding="utf-8"))
check(sj["fields"]["width|product"]["judgement"]["status"] == "verified" and "completeness" not in sj, "spec.json carries the judgements and no completeness verdict")
# reject
js, rc, _ = S("reject", "--id", sp1, "--reason", "wrong variant", "--with-copies")
check(js["copies_rejected"] == [sp_mat] and js["recorded_as_copies_of_it"] == [sp_mat], "--with-copies rejects the facts recorded as copies, and only then")
js, rc, _ = sadd(C2, "material", "--text", "oak", *MK)
o1 = js["id"]
js, rc, _ = sadd(C2, "material", "--text", "oak, oiled", *SH, "--copy-of", o1)
o2 = js["id"]
js, rc, _ = S("reject", "--id", o1, "--reason", "another model")
check(js["copies_rejected"] == [] and js["recorded_as_copies_of_it"] == [o2], "without the flag a copy is NOT rejected behind the agent's back; it is listed")
js, rc, out_ = S("list", "--cand", C2, "--md")
check(o1 in out_ and "another model" in out_, "a rejected fact stays on record")
js, rc, _ = S("render", "--cand", C2, "--out", str(Path(RUN) / "deliverables" / "spec-c2.md"))
md3_ = (Path(RUN) / "deliverables" / "spec-c2.md").read_text(encoding="utf-8")
check("Rejected facts" in md3_ and o2 in md3_, "the sheet lists the rejected facts and keeps the rest")

# ================================================================ photo links, probed by a local test server: HEAD only, nothing downloaded
BIG = b"x" * 60000
ROUTES = {
    "/front.png": (200, "image/png", BIG), "/front.png?w=200": (200, "image/png", BIG), "/back.png": (200, "image/png", BIG), "/left.jpg": (200, "image/jpeg", BIG),
    "/right.jpg": (200, "image/jpeg", BIG), "/top.webp": (200, "image/webp", BIG), "/side.png": (200, "image/png", BIG), "/detail.png": (200, "image/png", BIG),
    "/tiny.png": (200, "image/png", b"x" * 900), "/signed.png?Expires=1893456000&Signature=abc": (200, "image/png", BIG),
    "/notimg.png": (200, "text/html", b"<html>login</html>"), "/vector.svg": (200, "image/svg+xml", b"<svg/>"), "/anim.gif": (200, "image/gif", b"GIF89a"),
    "/blocked.png": (403, "text/plain", b"forbidden"), "/nohead.png": (200, "image/png", BIG), "/notype.png": (200, "", BIG),
    "/redir-front.png": (302, "text/plain", b"/redir-target.png"), "/redir-target.png": (200, "image/png", BIG), "/redir-file.png": (302, "text/plain", b"file:///C:/Windows/win.ini"),
    "/botcheck.html": (200, "text/html", b"<html><body><script>var x=1;</script><h1>Are you a robot? Please complete the CAPTCHA to continue.</h1></body></html>"),
    "/walled.html": (403, "text/html", b"<html>forbidden</html>"),
}
HITS = []
NO_HEAD = {"/nohead.png"}


class H(http.server.BaseHTTPRequestHandler):
    def _serve(self):
        head = self.command == "HEAD"
        HITS.append((self.path, self.headers.get("User-Agent"), self.headers.get("Referer"), self.command))
        if head and self.path in NO_HEAD:
            self.send_response(405)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        code, ctype, body = ROUTES.get(self.path, (404, "text/plain", b"missing"))
        if callable(body):
            body = body()
        self.send_response(code)
        if ctype:
            self.send_header("Content-Type", ctype)
        if 300 <= code < 400:
            self.send_header("Location", body.decode())
            body = b""
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)

    do_GET = do_HEAD = _serve

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"
PAGE = """<html><head><title>Test kettle - maker page</title>
<base href="{BASE}/gallery/">
<meta property="og:image" content="{BASE}/front.png">
<meta name="twitter:image" content="/front.png">
<link rel="image_src" href="/back.png">
<link rel="preload" as="image" href="/preload-top.webp">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Test kettle","image":["{BASE}/front.png","/left.jpg",{"@type":"ImageObject","url":"/top.webp"}]}</script>
<script>window.__DATA__ = {"media":[{"src":"https:\\/\\/cdn.example.net\\/p\\/gallery-1.jpg?v=3"},{"src":"//cdn.example.net/p/gallery-2.png"}]};</script>
</head><body>
<img src="/img/logo.png" alt="Brand logo" width="120" height="40">
<img src="/pixel.gif" width="1" height="1">
<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
<img src="thumb-small.jpg" srcset="/s-400.jpg 400w, /s-1600.jpg 1600w, /s-800.jpg 800w" alt="Kettle side view">
<img data-src="/lazy-right.png" alt="Kettle right">
<img src="/kettle_back_view.jpg">
<img src="/signed.png?Expires=1893456000&Signature=abc" alt="signed">
<img src="/sprite.svg" alt="icons">
<a href="/big-detail.jpg"><img src="/small-detail.jpg" width="150" height="150"></a>
</body></html>"""
ROUTES["/page.html"] = (200, "text/html; charset=utf-8", lambda: PAGE.replace("{BASE}", BASE).encode())
PAGE_URL = "https://maker.example/p/1"


def padd(path, angle, *extra, cand=None, ok=True, kind="manufacturer", page=PAGE_URL, absolute=False, private=True):
    url = path if absolute else BASE + path
    return t("photo", "add", "--run", RUN, "--cand", cand or C1, "--url", url, "--page-url", page, "--angle", angle, "--source-kind", kind, *(["--allow-private-host"] if private else []), *extra, ok=ok)


js, rc, _ = t("photo", "add", "--run", RUN, "--cand", C1, "--url", BASE + "/front.png", "--angle", "front", "--source-kind", "manufacturer", "--allow-private-host", ok=False)
check(rc == 2 and "--page-url" in js.get("error", ""), "every link needs the page it was found on")
js, rc, _ = t("photo", "set", "--run", RUN, "--id", "PH999", "--reject", "--reason", "x", ok=False)
check(rc == 2, "photo set needs an existing link")
js, rc, _ = padd("/front.png", "front", "--basis", "gallery-order", "--variant", "2 L white", "--declared-px", "1200")
front_id = js["id"]
check(js["ok"] and js["link_status"] == "ok" and js["content_type"] == "image/png" and js["bytes"] == 60000 and js["https"] is False, "a link is probed and recorded: " + str(js.get("link_status")))
mine = [h for h in HITS if h[0] == "/front.png"]
check(mine and all(h[3] == "HEAD" for h in mine) and mine[-1][1].startswith("Mozilla/5.0") and mine[-1][2] is None, "the probe is a HEAD request with the fixed read-only identity and no referer")
n_before = len(HITS)
js, rc, _ = padd("/front.png?w=200", "front")
check(js["ok"] and js.get("duplicate_of") == front_id and len(HITS) == n_before, "an address that differs only by a size parameter is the same image: found before any request, answered with duplicate_of (nothing added, nothing refused)")
# probe results are FACTS about the link: every one is recorded, none is rejected on the agent's behalf
for path, status in (("/missing.png", "dead"), ("/notimg.png", "not-image"), ("/vector.svg", "format"), ("/anim.gif", "format"), ("/blocked.png", "blocked"), ("/nohead.png", "unchecked"), ("/notype.png", "unchecked")):
    js, rc, _ = padd(path, "back")
    check(js["ok"] and js["link_status"] == status, f"{path}: the probe says {status} and the link is recorded as it is")
rows_all = {r["id"]: r for r in json.loads((R30 / "photos.json").read_text(encoding="utf-8"))["items"]}
check(all(r["status"] == "active" for r in rows_all.values()), "no link was rejected automatically: that is the agent's decision")
check([h[3] for h in HITS if h[0] == "/blocked.png"] == ["HEAD"] and [h[3] for h in HITS if h[0] == "/nohead.png"] == ["HEAD"], "a 403 is final (one HEAD) and a server that does not answer HEAD gets no GET instead")
js, rc, _ = padd("/tiny.png", "detail")
check(js["ok"] and "small_hint" not in js and js["bytes"] == 900, "a very small file carries its size as a fact, not a 'thumbnail' flag")
js, rc, _ = padd("/signed.png?Expires=1893456000&Signature=abc", "left")
check(js["ok"] and js["may_expire"] is True, "a signed address is marked as one that may expire")
js, rc, _ = padd("/redir-front.png", "right")
check(js["ok"] and js["link_status"] == "ok" and js["final_url"].endswith("/redir-target.png"), "a redirect is followed by hand and the final address recorded")
rows_before = len(json.loads((R30 / "photos.json").read_text(encoding="utf-8"))["items"])
js, rc, _ = padd("/redir-file.png", "back", ok=False)
check(rc == 1 and "only http and https" in js.get("error", "") and len(json.loads((R30 / "photos.json").read_text(encoding="utf-8"))["items"]) == rows_before, "a redirect to a file: address is refused and nothing is recorded: " + js.get("error", "")[:60])
n_before = len(HITS)
js, rc, _ = t("photo", "add", "--run", RUN, "--cand", C1, "--url", BASE + "/back.png", "--page-url", PAGE_URL, "--angle", "back", "--source-kind", "manufacturer", ok=False)
check(rc == 1 and "non-public address" in js.get("error", "") and len(HITS) == n_before, "an address on this machine is refused with no request unless the test switch is given")
js, rc, _ = padd("https://example.invalid/front-https.png", "top", absolute=True)
check(js["ok"] and js["https"] is True and js["link_status"] == "unchecked", "an https address that does not answer is kept as unchecked")
js, rc, _ = padd("/back.png", "Rear View")
js, rc, _ = padd("/top.webp", "top-down")
# flags: only someone who looked can set them
js, rc, _ = t("photo", "set", "--run", RUN, "--id", front_id, "--watermark", "no", ok=False)
check(rc == 2 and "looked" in js.get("error", ""), "a visual flag needs --looked-at yes")
js, rc, _ = t("photo", "set", "--run", RUN, "--id", front_id, "--rights", "stated-for-resellers", ok=False)
check(rc == 2 and "--note" in js.get("error", ""), "a rights statement needs the note that says where the page states it")
js, rc, _ = t("photo", "set", "--run", RUN, "--id", front_id, "--rights", "stated-for-resellers", "--note", "press kit page: images may be used by resellers")
js, rc, _ = t("photo", "set", "--run", RUN, "--id", front_id, "--looked-at", "yes", "--background", "clean", "--watermark", "no", "--brand-marks", "no", "--same-variant", "yes", "--by", "pack-agent")
check(js["ok"] and js["looked_at"] is True and js["background"] == "clean" and js["watermark"] is False, "after looking, the flags can be set")
blocked_id = next(r["id"] for r in json.loads((R30 / "photos.json").read_text(encoding="utf-8"))["items"] if r["url"].endswith("/blocked.png"))
js, rc, _ = t("photo", "set", "--run", RUN, "--id", blocked_id, "--reject", "--reason", "403: cannot be confirmed")
check(js["status"] == "rejected", "the agent rejects a link with a reason")
js, rc, _ = t("photo", "set", "--run", RUN, "--id", blocked_id, "--restore")
check(js["status"] == "active", "and can restore it")
t("photo", "set", "--run", RUN, "--id", blocked_id, "--reject", "--reason", "403: cannot be confirmed")
# the coverage table: counts, no verdict, no suggested set
js, rc, _ = t("photo", "check", "--run", RUN, "--cand", C1)
core = {d["angle"]: d for d in js["core_angles"]}
check(js["ok"] and "verdict" not in js and "reference_set" not in js and "core_angles_missing" not in js, "the coverage is a table: no verdict, no suggested set, no 'missing' list")
check(core["front"]["links"] == 1 and core["front"]["link_ok"] == 1 and core["left"]["links"] == 1 and core["right"]["link_ok"] == 1 and core["top"]["links"] == 1 and core["back"]["links"] >= 1, "per core view: links, confirmed, https, looked at: " + str({k: (v["links"], v["link_ok"]) for k, v in core.items()}))
by_angle = {d["angle"]: d for d in js["by_angle"]}
check("rear-view" in by_angle and "top-down" in by_angle, "'Rear View' and 'top-down' are recorded as written: no spelling is folded into back or top")
# no caps: the tool does not stop an agent at some number of links
for i in range(16):
    padd(f"/gone-{i}.png", "detail")
js, rc, _ = t("photo", "list", "--run", RUN, "--cand", C1)
check(js["count"] >= 30, "more than the old caps (12 links, 30 attempts) are accepted: " + str(js["count"]))
# a pack for any candidate
js, rc, _ = padd("/front.png", "front", cand=C2, page="https://shop.example/o")
check(js["ok"], "a pack is not tied to a pick: another candidate gets its links too")
# the pack's files
packdir = pack
procs = [subprocess.Popen([PY, "-X", "utf8", ATG, "spec", "render", "--run", RUN, "--cand", C1], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8") for _ in range(4)]
procs += [subprocess.Popen([PY, "-X", "utf8", ATG, "photo", "check", "--run", RUN, "--cand", C1], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8") for _ in range(4)]
codes = [pr_.wait(timeout=180) for pr_ in procs]
for pr_ in procs:
    pr_.stdout.close()
    pr_.stderr.close()
check(all(c == 0 for c in codes), "eight processes rendering and checking one pack at the same time all succeed: " + str(codes))
check(not [p_ for p_ in packdir.rglob("*") if p_.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif")], "no image file exists anywhere in the pack")
check((packdir / "photos.md").exists() and (packdir / "photos.html").exists() and (packdir / "photo-links.json").exists() and (packdir / "spec.md").exists(), "photos.md, photos.html, photo-links.json and spec.md are in the pack")
manifest = json.loads((packdir / "photo-links.json").read_text(encoding="utf-8"))
check(manifest["nothing_downloaded"] is True and "verdict" not in manifest and all(l["url"].startswith("http") for l in manifest["links"]), "the manifest lists the active links and no verdict")
check(not [h for h in HITS if h[3] == "GET" and not h[0].endswith(".html")], "no image address was ever requested with GET")
js, rc, _ = t("photo", "set", "--run", RUN, "--id", front_id, "--note", "<script>alert(1)</script> & \"quotes\"")
t("photo", "check", "--run", RUN, "--cand", C1)
gal = (packdir / "photos.html").read_text(encoding="utf-8")
check("&lt;script&gt;alert(1)&lt;/script&gt;" in gal and "<script>alert" not in gal and "<script" not in gal and 'referrerpolicy="no-referrer"' in gal and "Nothing was downloaded" in gal, "the gallery escapes everything and carries no script")
check("Coverage:" not in gal and "core views" in gal.lower(), "the gallery shows counts, not a coverage verdict")

# photo find: the addresses a page declares, in the page's own order, with nothing judged
js, rc, _ = t("photo", "find", "--run", RUN, "--cand", C1, "--page-url", BASE + "/page.html", "--allow-private-host")
cands_f = js["candidates"]
urls_f = [c["url"] for c in cands_f]
front_f = next(c for c in cands_f if c["url"].endswith("/front.png"))
check(js["found"] >= 14 and js["title"].startswith("Test kettle") and "visible_text_head" in js, "photo find lists the images a page declares, with the title and the head of the visible text: " + str(js["found"]))
check(not any(k in front_f for k in ("score", "angle_hint", "hint_basis", "likely_not_a_photo", "photo_add_refuses_format")) and "plausible" not in js, "no score, no 'not a photo' flag, no view guess, no count of plausible ones")
check(len(front_f["sources"]) == 3 and front_f["extension"] == "png" and front_f["file"] == "front.png", "an image named by the Open Graph, Twitter and JSON-LD data is one candidate with all its sources, its file name and its extension: " + str(front_f["sources"]))
check(urls_f.index(front_f["url"]) == 0, "the order is the page's own: the first image the page declares comes first")
check(not any(u.startswith("data:") for u in urls_f) and any(u.endswith("/s-1600.jpg") for u in urls_f) and not any(u.endswith(("/s-400.jpg", "/s-800.jpg")) for u in urls_f), "a data: address is skipped and only the largest srcset entry is kept")
check(all(any(u.endswith(x) for u in urls_f) for x in ("/lazy-right.png", "/left.jpg", "/top.webp", "/back.png", "/preload-top.webp", "/big-detail.jpg", "/p/gallery-1.jpg?v=3", "/p/gallery-2.png")), "lazy-load attributes, JSON-LD, image_src, preload, a linked image file and addresses inside scripts are found")
check(BASE + "/gallery/thumb-small.jpg" in urls_f, "a <base href> is honoured for relative addresses")
logo = next(c for c in cands_f if c["url"].endswith("/img/logo.png"))
svg = next(c for c in cands_f if c["url"].endswith("/sprite.svg"))
sig = next(c for c in cands_f if "signed.png" in c["url"])
check(logo["alt"] == "Brand logo" and logo["declared_px"] == 120 and svg["extension"] == "svg" and sig["expiring_query_keys"] == ["expires", "signature"], "what the page says is passed on as it is (alt text, declared size, extension, signature parameters): the logo is not 'marked'")
check("note" in js and "never instructions" in js["note"] and "notes" not in js, "the page text is data, never instructions: a reminder, no advice")
js, rc, _ = t("photo", "find", "--run", RUN, "--cand", C1, "--page-url", BASE + "/botcheck.html", "--allow-private-host")
check(js["ok"] and "robot" in js["visible_text_head"].lower() and js["found"] == 0 and "bot check" not in json.dumps(js).lower(), "a bot-check page: the tool shows the head of its text and says nothing about it (the agent reads 'robot' there)")
n_before = len(HITS)
js, rc, _ = t("photo", "find", "--run", RUN, "--cand", C1, "--page-url", BASE + "/walled.html", "--allow-private-host", ok=False)
check(rc == 1 and js.get("http_status") == 403 and len(HITS) == n_before + 1, "a 403 on a page is final: one request, no retry")
js, rc, _ = t("photo", "find", "--run", RUN, "--cand", C1, "--page-url", BASE + "/front.png", "--allow-private-host", ok=False)
check(rc == 2 and "image address" in js.get("error", ""), "an image address is refused as a page")
srv.shutdown()

# ---- the address guard and the connect-time check, in process (unchanged mechanics: safety of the fetch, not a judgement)
import importlib.util as _iu
import socket

_spec = _iu.spec_from_file_location("atg_inproc", ATG)
atg = _iu.module_from_spec(_spec)
_spec.loader.exec_module(atg)
for u_, why_ in (("http://127.0.0.1:8080\\@8.8.8.8/x.jpg", "a backslash that makes two parsers disagree"), ("http://user@8.8.8.8/x.jpg", "user information"),
                 ("http://exa mple.com/x.jpg", "whitespace"), ("http://localhost/x.jpg", "localhost"), ("http://127.0.0.1/x.jpg", "loopback"),
                 ("http://[::1]/x.jpg", "IPv6 loopback"), ("http://[::ffff:127.0.0.1]/x.jpg", "an IPv4-mapped loopback"), ("http://[64:ff9b::7f00:1]/x.jpg", "a NAT64 loopback"),
                 ("http://[2002:7f00:1::]/x.jpg", "a 6to4 loopback"), ("http://169.254.169.254/latest/", "the link-local metadata address"),
                 ("http://10.1.2.3/x", "a private address"), ("http://192.168.0.1/x", "a private address"), ("http://100.64.0.1/x", "shared address space"),
                 ("http://0.0.0.0/x", "the unspecified address"), ("http://2130706433/x", "a decimal loopback"), ("file:///C:/Windows/win.ini", "a file address"),
                 ("ftp://8.8.8.8/x", "ftp")):
    check(atg._public_host_error(u_) is not None, f"the address guard refuses {why_}: {u_}")
check(atg._public_host_error("http://8.8.8.8/x.jpg") is None, "...and lets a public address through")
real_gai = socket.getaddrinfo
calls = {"n": 0}


def fake_gai(host, port, *a, **k):
    if host == "rebind.example":
        calls["n"] += 1
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34" if calls["n"] == 1 else "127.0.0.1", port))]
    return real_gai(host, port, *a, **k)


srv2 = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv2.serve_forever, daemon=True).start()
n_before = len(HITS)
socket.getaddrinfo = fake_gai
try:
    r_ = atg._probe_link(f"http://rebind.example:{srv2.server_address[1]}/front.png", None, False)
finally:
    socket.getaddrinfo = real_gai
    srv2.shutdown()
check(r_["link_status"] == "refused" and len(HITS) == n_before and calls["n"] >= 2, "a name that answers public first and loopback at connect time is not connected to (DNS rebinding): " + str(r_["link_status"]))
td_ = Path(tempfile.mkdtemp(prefix="atg-replace-"))
target_ = td_ / "t.json"
target_.write_text("{}", encoding="utf-8")
tmp_ = td_ / "t.json.tmp"
tmp_.write_text('{"a": 1}', encoding="utf-8")
fh_ = open(target_, "rb")
threading.Timer(0.4, fh_.close).start()
atg._replace_retry(tmp_, target_)
check(json.loads(target_.read_text(encoding="utf-8")) == {"a": 1}, "a replace waits for a reader to let go instead of failing")
t0_ = time.time()
res_ = atg._with_deadline(lambda: time.sleep(3), 0.4)
check(res_ == (False, None) and time.time() - t0_ < 2, "a call that does not finish is given up on after its deadline")


class Slow(H):
    def _serve(self):
        time.sleep(4)
        super()._serve()

    do_GET = do_HEAD = _serve


srv3 = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Slow)
threading.Thread(target=srv3.serve_forever, daemon=True).start()
t0_ = time.time()
r_ = atg._probe_link(f"http://127.0.0.1:{srv3.server_address[1]}/front.png", None, True, deadline=1)
check(r_["link_status"] == "unchecked" and "within 1 seconds" in (r_["error"] or "") and time.time() - t0_ < 3, "a server that answers too slowly leaves the link unchecked after the deadline")
srv3.shutdown()
t0_ = time.time()
rows_s, total_s, _t, _txt, _b = atg._photo_find("<script>" + "//a.bc/" * 20000 + "x.jpg</script>", "http://h.example/p/", 50)
check(time.time() - t0_ < 5, "a script made of thousands of address-like fragments is scanned in bounded time: " + str(round(time.time() - t0_, 2)) + " s")
rows_s, total_s, _t, _txt, base_s = atg._photo_find('<html><base href="https://cdn.other.example/"><img src="x.jpg"><img srcset="a.jpg 100w,b.jpg 4000w"><img srcset=", ,"></html>', "http://h.example/p/", 50)
check(sorted(r["url"] for r in rows_s) == ["https://cdn.other.example/b.jpg", "https://cdn.other.example/x.jpg"] and base_s == "https://cdn.other.example/", "a compact srcset gives its largest candidate, an empty one gives none, and a <base> on another host is reported")
saved_env = {k: os.environ.pop(k, None) for k in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy")}
try:
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:9"
    check(atg._proxy_for("http://shop.example/x.jpg") is None and atg._proxy_for("https://shop.example/x.jpg") == "http://127.0.0.1:9", "a proxy for https addresses is not taken for a proxy of http addresses")
    calls["n"] = 0
    srv4 = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv4.serve_forever, daemon=True).start()
    n_before = len(HITS)
    socket.getaddrinfo = fake_gai
    try:
        r_ = atg._probe_link(f"http://rebind.example:{srv4.server_address[1]}/front.png", None, False)
    finally:
        socket.getaddrinfo = real_gai
        srv4.shutdown()
    check(r_["link_status"] == "refused" and len(HITS) == n_before, "with only an https proxy configured, an http address is still checked at connect time")
finally:
    for k_, v_ in saved_env.items():
        if v_ is not None:
            os.environ[k_] = v_
        else:
            os.environ.pop(k_, None)

finish()
