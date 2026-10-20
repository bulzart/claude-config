"""Shared helpers of the /analyze-with-loupe test suites. The toolkit is called through its command line on scratch fixtures: a temp
library copy (config.json with its own runs root, models/index.json) is pointed at by AWL_HOME, so nothing under the real library's
runs/ is ever touched. Loupe's data folder is a temp folder too (LOUPE_DATA)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE.parent                                   # ~/.claude/analyze-with-loupe
HOME = LIB.parent                                   # ~/.claude
PY = sys.executable
AWL = os.environ.get("AWL_UNDER_TEST") or str(LIB / "scripts" / "awl.py")

fails = []


def check(cond, msg):
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def finish():
    print("\nFAILED:" if fails else "\nALL CHECKS PASSED", fails if fails else "")
    sys.exit(1 if fails else 0)


def temp_library(name="t") -> Path:
    """A throwaway library copy: config.json (runs_root inside it), models/index.json, models/_generic-fallback.md. AWL_HOME points here."""
    tmp = Path(tempfile.mkdtemp(prefix=f"awl-{name}-"))
    home = tmp / "awl"
    (home / "models").mkdir(parents=True)
    (home / "runs").mkdir()
    cfg = json.loads((LIB / "config.json").read_text(encoding="utf-8"))
    cfg["runs_root"] = str(home / "runs").replace("\\", "/")
    cfg["awl_home"] = str(home).replace("\\", "/")
    (home / "config.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    shutil.copy(LIB / "models" / "index.json", home / "models" / "index.json")
    fb = LIB / "models" / "_generic-fallback.md"
    if fb.is_file():
        shutil.copy(fb, home / "models" / "_generic-fallback.md")
    return home


def t(*args, env=None, ok=True, timeout=600):
    """Run the toolkit; (last-line JSON, exit code, stdout). The last stdout line must be one JSON object (the pipelines' contract)."""
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    if env:
        e.update(env)
    cp = subprocess.run([PY, "-X", "utf8", AWL, *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=e, timeout=timeout)
    last = [l for l in cp.stdout.strip().splitlines() if l.strip()]
    js = {}
    if last:
        try:
            js = json.loads(last[-1])
        except ValueError:
            js = {"raw": last[-1]}
    if ok and cp.returncode != 0:
        print("UNEXPECTED FAILURE:", args, cp.stdout[-600:], cp.stderr[-600:])
        sys.exit(1)
    return js, cp.returncode, cp.stdout


def ffmpeg() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def make_clip(path: Path, seconds: float = 4.0, flash=(2.0, 2.3), audio: bool = True, size="360x640"):
    """A synthetic clip: dark grey, a white flash between the given seconds, a 440 Hz tone when audio is True."""
    path.parent.mkdir(parents=True, exist_ok=True)
    vf = f"drawbox=enable='between(t,{flash[0]},{flash[1]})':x=0:y=0:w=iw:h=ih:color=white:t=fill" if flash else "null"
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=0x303030:s={size}:r=30:d={seconds}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += ["-vf", vf, "-pix_fmt", "yuv420p", str(path)]
    cp = subprocess.run(cmd, capture_output=True)
    assert cp.returncode == 0, cp.stderr[-300:]
    return path


def make_text_pdf(path: Path, text: str = "Hello G1 rule: no gore"):
    """A minimal one-page PDF with a real text layer (Helvetica), built by hand so no extra library is needed."""
    content = f"BT /F1 18 Tf 40 700 Td ({text}) Tj ET".encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))
    return path


def make_image_pdf(path: Path):
    """A two-page image-only PDF (no text layer), made with Pillow."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (400, 300), (250, 250, 250))
    ImageDraw.Draw(im).rectangle((40, 40, 360, 260), outline=(0, 0, 0), width=4)
    im2 = Image.new("RGB", (400, 300), (230, 240, 250))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, save_all=True, append_images=[im2])
    return path
