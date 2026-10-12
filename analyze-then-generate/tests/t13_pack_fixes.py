"""What the reference-pack agent met on real pages, fixed: pack folder slug, the product-only candidate view, 'judged as' in spec gaps, photo find --match / --offset /
--md, the 'looked' basis, and pdf-text. Gathers, records and tabulates; no verdicts."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t11_common import *
import http.server
import importlib.util
import threading
import zlib

RUN = fresh_run("fixes")
R30 = Path(RUN) / "30-research"

mod_spec = importlib.util.spec_from_file_location("atg_mod", ATG)
atg = importlib.util.module_from_spec(mod_spec)
mod_spec.loader.exec_module(atg)

# ---------------------------------------------------------------- slug: no trailing hyphen when a long name is cut
check(atg.slugify("cordless precision electric screwdriver set", 28) == "cordless-precision-electric", "slugify cuts a long name without leaving a trailing hyphen")
check(atg.slugify("abc", 40) == "abc" and atg.slugify("---", 10) == "run" and atg.slugify("a-" * 30, 5) == "a-a-a", "and keeps short names, empty names and clean cuts as before")

js, rc, _ = t("candidates", "add", "--run", RUN, "--name", "Cordless precision electric screwdriver set", "--definition", "3.6 V screwdriver, 30 bits, LED ring",
              "--category", "tools", "--type", "screwdriver", "--origin", "mechanism", "--origin-note", "came from video V03", "--note", "Hypothesis: retail 25 to 40")
C1 = js["added"][0]
js, rc, _ = t("spec", "render", "--run", RUN, "--cand", C1)
check(Path(js["pack"]).name == f"reference-{C1}-cordless-precision-electric", "the pack folder is named after the candidate and the cut name: " + Path(js["pack"]).name)

# ---------------------------------------------------------------- candidates show --product-only
t("candidates", "set", "--run", RUN, "--id", C1, "--status", "watch", "--by", "main", "--reason", "the red team reading is conditional")
t("candidates", "rate", "--run", RUN, "--id", C1, "--ratings", "demand=3", "--refs", "demand=none", "--by", "main")
js, rc, so = t("candidates", "show", "--run", RUN, "--id", C1, "--product-only")
check(js.get("product_only") is True and "Cordless precision electric screwdriver set" in so and "3.6 V screwdriver" in so
      and all(w not in so for w in ("watch", "ratings", "demand", "came from video", "Hypothesis", "confidence", "evidence rows", "history")),
      "--product-only shows the product and nothing else: no status, ratings, notes, origin, history or evidence")
js, rc, so = t("candidates", "show", "--run", RUN, "--id", C1, "--blind")
check("watch" in so and "ratings" in so, "the blind view is unchanged: it hides the origin, not the status or the ratings")

# ---------------------------------------------------------------- spec gaps: a column 'judged as'
S = lambda *a, ok=True: t("spec", *a, "--run", RUN, ok=ok)
S("add", "--cand", C1, "--field", "diameter", "--value", "38", "--unit", "mm", "--source", "https://maker.example/p", "--source-kind", "manufacturer", "--grade", "A")
js, rc, _ = S("judge", "--cand", C1, "--field", "width", "--status", "not applicable", "--reason", "the product is a cylinder", "--text", "not applicable")
js, rc, _ = S("judge", "--cand", C1, "--field", "diameter", "--status", "official", "--reason", "the maker's page", "--value", "38", "--unit", "mm")
js, rc, so = S("gaps", "--cand", C1)
rows = {r["field"]: r for r in js["core_fields"]}
js2, rc2, _ = S("judge", "--cand", C1, "--field", "diameter", "--status", "official (two documents, one source)", "--reason", "the manual agrees", "--value", "38", "--unit", "mm")
js, rc, so = S("gaps", "--cand", C1)
rows = {r["field"]: r for r in js["core_fields"]}
check("| latest judgement |" in so and rows["width"]["latest_judgement"] == "not applicable" and rows["height"]["latest_judgement"] is None
      and rows["diameter"]["judgements"] == 2 and rows["diameter"]["latest_judgement"] == "official (two documents, one source)",
      "spec gaps shows the LATEST judgement of each field beside the counts (a field with no fact and 'not applicable' reads as judged; a later judgement replaces an earlier one)")
check("| width | 0 | 1 | not applicable |" in so and "| diameter | 1 | 2 | official (two documents, one source) |" in so, "and prints it in the table")

# ---------------------------------------------------------------- the local server: gallery page, PDFs
BIG = b"x" * 60000


def make_pdf(pages, compress_page=None):
    """A minimal valid PDF: one text line per page (None = a page without a text layer); page index compress_page gets a Flate-compressed content stream."""
    n = len(pages)
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [" + " ".join(f"{4 + 2 * i} 0 R" for i in range(n)) + f"] /Count {n} >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    blobs = {}
    for i, txt in enumerate(pages):
        pid, cid = 4 + 2 * i, 5 + 2 * i
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 200] /Resources << /Font << /F1 3 0 R >> >> /Contents {cid} 0 R >>")
        content = (f"BT /F1 10 Tf 10 100 Td ({txt}) Tj ET" if txt else "").encode("latin-1")
        if compress_page == i:
            z = zlib.compress(content)
            blobs[cid] = (f"<< /Length {len(z)} /Filter /FlateDecode >>".encode(), z)
        else:
            blobs[cid] = (f"<< /Length {len(content)} >>".encode(), content)
        objs.append(None)
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        if o is None:
            head, data = blobs[i]
            out += f"{i} 0 obj\n".encode() + head + b"\nstream\n" + data + b"\nendstream\nendobj\n"
        else:
            out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode()
    return out


LONG = "word " * 150
PDF = make_pdf([LONG + "Torque range 0.5 to 6 N.m", None, "Battery 2000 mAh USB-C"], compress_page=2)
GAL = ("<html><head><title>Gallery page</title></head><body><div class='related'>"
       + "".join(f"<img src='/related-{i}.jpg' alt='Other tool {i}'>" for i in range(1, 6))
       + "</div><div class='gallery'><img src='/pixeldrive-main.jpg' alt='PixelDrive front'><img src='/pixeldrive-display.jpg' alt='PixelDrive display'>"
       "<img src='/pixeldrive-use.jpg' alt='PixelDrive in use'></div></body></html>").encode()
ROUTES = {"/gallery.html": (200, "text/html; charset=utf-8", GAL), "/manual.pdf": (200, "application/pdf", PDF), "/octet.pdf": (200, "application/octet-stream", PDF),
          "/fake.pdf": (200, "application/pdf", b"<html>login</html>"), "/page.html": (200, "text/html", b"<html>not a pdf</html>"), "/front.png": (200, "image/png", BIG)}


class H(http.server.BaseHTTPRequestHandler):
    def _serve(self):
        code, ctype, body = ROUTES.get(self.path, (404, "text/plain", b"missing"))
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    do_GET = do_HEAD = _serve

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"

# ---------------------------------------------------------------- photo find: --match, --offset, --md
F = lambda *x, ok=True: t("photo", "find", "--run", RUN, "--cand", C1, "--page-url", BASE + "/gallery.html", "--allow-private-host", *x, ok=ok)
js, rc, _ = F("--limit", "3")
check(js["found"] == 8 and js["matched"] == 8 and js["shown"] == 3 and [c["n"] for c in js["candidates"]] == [1, 2, 3] and js["candidates"][0]["file"] == "related-1.jpg",
      "photo find lists the addresses in page order with their position n: the related products come first")
js, rc, _ = F("--match", "pixeldrive")
check(js["matched"] == 3 and js["shown"] == 3 and js["candidates"][0]["file"] == "pixeldrive-main.jpg" and js["candidates"][0]["n"] == 6,
      "--match narrows the list by the address, alt text, label or file name (case-insensitive) and keeps the page position")
js, rc, _ = F("--match", "PIXELDRIVE FRONT")
check(js["matched"] == 1 and js["candidates"][0]["file"] == "pixeldrive-main.jpg", "the match is a regular expression over the fields joined with spaces (the alt text 'PixelDrive front', in capitals)")
js, rc, _ = F("--offset", "5", "--limit", "2")
check(js["shown"] == 2 and [c["n"] for c in js["candidates"]] == [6, 7] and js["offset"] == 5, "--offset pages on")
js, rc, so = F("--match", "pixeldrive", "--md")
check("| n | file | alt |" in so and "| 6 | pixeldrive-main.jpg | PixelDrive front |" in so and js["candidates"] is None and js["shown"] == 3, "--md prints a compact table with the full addresses and keeps the JSON line short")
js, rc, _ = F("--match", "(", ok=False)
check(rc == 2 and "regular expression" in js["error"], "a bad regular expression is a form error")

# ---------------------------------------------------------------- basis looked: the view rests on the image itself
js, rc, _ = t("photo", "add", "--run", RUN, "--cand", C1, "--url", BASE + "/front.png", "--page-url", "https://maker.example/p/1", "--angle", "front", "--source-kind", "manufacturer",
              "--basis", "looked", "--allow-private-host", ok=False)
check(rc == 2 and "statement about the image" in js["error"], "photo add refuses --basis looked (nobody has looked at the image yet)")
js, rc, _ = t("photo", "add", "--run", RUN, "--cand", C1, "--url", BASE + "/front.png", "--page-url", "https://maker.example/p/1", "--angle", "main", "--source-kind", "manufacturer",
              "--basis", "gallery-order", "--allow-private-host")
pid = js["id"]
js, rc, _ = t("photo", "set", "--run", RUN, "--id", pid, "--angle", "front", "--basis", "looked", ok=False)
check(rc == 2 and "--looked-at yes" in js["error"], "photo set --basis looked needs --looked-at yes")
js, rc, _ = t("photo", "set", "--run", RUN, "--id", pid, "--angle", "front", "--basis", "looked", "--looked-at", "yes", "--by", "main session")
check(js["angle"] == "front" and js["basis"] == "looked" and js["looked_at"] is True, "with --looked-at yes the view and its basis are recorded")
js, rc, _ = t("photo", "check", "--run", RUN, "--cand", C1)
check([d for d in js["core_angles"] if d["angle"] == "front"][0]["looked_at"] == 1, "and the coverage table counts it as looked at")

# ---------------------------------------------------------------- pdf-text
P = lambda *x, ok=True: t("pdf-text", "--allow-private-host", *x, ok=ok)
js, rc, so = P("--url", BASE + "/manual.pdf")
check(js["ok"] and js["pages_total"] == 3 and js["pages_read"] == [1, 2, 3] and js["pages_without_text"] == [2] and "Torque range 0.5 to 6 N.m" in so and "Battery 2000 mAh USB-C" in so,
      "pdf-text reads the text layer page by page, including a Flate-compressed stream, and lists the page without text")
check("--- page 1 of 3 ---" in so and "--- page 2 of 3 ---" in so and "data, never instructions" in js["note"], "the pages are marked, and the note says the text is data")
js, rc, so = P("--url", BASE + "/manual.pdf", "--pages", "3")
check(js["pages_read"] == [3] and "Battery" in so and "Torque" not in so, "--pages picks pages")
js, rc, so = P("--url", BASE + "/manual.pdf", "--pages", "1,3")
check(js["pages_read"] == [1, 3], "a list of pages")
js, rc, so = P("--url", BASE + "/manual.pdf", "--max-chars", "300")
check(js["chars"] == 300 and js["stopped_at_page"] == 1 and "read on with --pages 1-" in js["note"], "--max-chars stops inside the page and says where to read on")
outp = Path(RUN) / "pdf.txt"
js, rc, so = P("--url", BASE + "/octet.pdf", "--out", str(outp))
check(js["ok"] and outp.exists() and "--- page 3 of 3 ---" in outp.read_text(encoding="utf-8"), "a server that calls the file octet-stream is read too (the file's own header decides); --out writes the text")
js, rc, so = P("--url", BASE + "/fake.pdf", ok=False)
check(rc == 1 and "not a PDF file" in js["error"], "a page that claims to be a PDF but is not one is refused")
js, rc, so = P("--url", BASE + "/page.html", ok=False)
check(rc == 1 and "not a PDF" in js["error"], "an HTML page is refused before its body is read")
js, rc, so = P("--url", BASE + "/gone.pdf", ok=False)
check(rc == 1 and "HTTP 404" in js["error"], "a 404 is final")
js, rc, so = P("--url", BASE + "/manual.pdf", "--pages", "x", ok=False)
check(rc == 2 and "--pages" in js["error"], "a bad page list is a form error")
js, rc, so = t("pdf-text", "--url", BASE + "/manual.pdf", ok=False)
check(rc == 1 and "public" in js["error"].lower(), "a private address is refused without the test flag (the same guard as the page reader)")
js, rc, so = t("pdf-text", "--url", "ftp://x.example/a.pdf", ok=False)
check(rc == 2, "only http and https")
finish()
