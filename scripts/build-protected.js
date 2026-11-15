#!/usr/bin/env node
/**
 * build-protected.js - a separate, compiled copy of one pipeline's CLI for handing to someone outside, built from this same plain source with
 * PyInstaller (the actual source is Python; this driver is Node.js, not PowerShell, per the user, 2026-11-15).
 *
 * Never run as part of normal maintenance: Claude Code reads and edits the plain .py files under <pipeline>\scripts\ every session, by file path
 * and line number, with byte-exact patches; this script's output is a frozen copy for distribution only, and nothing here changes the maintained
 * source. PyInstaller still does the real work (it is what actually compiles the Python into bytecode-only form); this script only drives it,
 * copies the config template, writes the notice, and carries along any PowerShell helper scripts the pipeline ships (the user, 2026-11-15:
 * "if there are ps1 scripts to be run then include them as scripts ... to be run inside the obfuscated build" - they travel as plain .ps1 files
 * inside the build, unmodified; this script does not touch, obfuscate or rewrite them).
 *
 * What this protects: the Python source logic, bundled into compiled .pyc inside the output folder, not shipped as readable .py files.
 * What this does NOT solve (hiding the source was the ask; making the tool portable to someone else's machine is a separate, bigger job):
 *   - the destination machine still needs its own ffmpeg, and CapCut 9.7 + capcut-cli on PATH for any CapCut-building step;
 *   - config.json's paths are this PC's absolute paths: copied as config.example.json next to the build, to be edited by whoever receives it;
 *   - faster-whisper's `medium` model (1.4 GB) is not bundled: downloaded on first use, or copied by hand into the destination's HF cache;
 *   - create-static also needs an OpenAI or ElevenLabs API key, and a local FLUX Klein / ACE-Step install only if those options are used.
 * The output never goes in this repo: it is written to OUT_ROOT below, outside C:\Users\Bulzart\.claude, and is never committed.
 *
 * Usage:
 *   node build-protected.js --pipeline create-clips [--clean] [--skip-smoke-test]
 *   node build-protected.js --pipeline create-static [--clean]
 */
"use strict";

const { execFileSync, spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const { parseArgs } = require("node:util");

const PY = "C:\\Users\\Bulzart\\AppData\\Local\\Programs\\Python\\Python312\\python.exe";
const CLAUDE = "C:\\Users\\Bulzart\\.claude";
const OUT_BASE = "C:\\Users\\Bulzart\\ProtectedBuilds"; // outside ~/.claude on purpose: never part of the git repo

const PIPELINES = {
  "create-clips": { entry: "cc.py", toolName: "cc", collect: ["numpy", "PIL", "faster_whisper", "ctranslate2", "rapidocr_onnxruntime", "onnxruntime"],
    note: "CapCut 9.7 and capcut-cli on PATH for any CapCut-building step; the faster-whisper 'medium' model (downloaded on first use, or copied by hand into the Hugging Face cache)." },
  "create-static": { entry: "cs.py", toolName: "cs", collect: ["numpy", "PIL", "faster_whisper", "ctranslate2", "rapidocr_onnxruntime", "onnxruntime", "cv2", "librosa", "requests", "pypdf"],
    note: "CapCut 9.7 and capcut-cli on PATH; an OpenAI or ElevenLabs API key; faster-whisper 'medium' for transcription; a local FLUX Klein / ACE-Step install only if those image or music options are used." },
};

function main() {
  const { values } = parseArgs({
    options: {
      pipeline: { type: "string" },
      clean: { type: "boolean", default: false },
      "skip-smoke-test": { type: "boolean", default: false },
    },
  });
  const pipeline = values.pipeline;
  if (!pipeline || !PIPELINES[pipeline]) {
    console.error(`--pipeline must be one of: ${Object.keys(PIPELINES).join(", ")}`);
    process.exit(2);
  }
  const cfg = PIPELINES[pipeline];
  const src = path.join(CLAUDE, pipeline, "scripts");
  const entryPath = path.join(src, cfg.entry);
  if (!fs.existsSync(entryPath)) {
    console.error(`entry script not found: ${entryPath}`);
    process.exit(2);
  }

  const outRoot = path.join(OUT_BASE, pipeline);
  if (values.clean && fs.existsSync(outRoot)) {
    fs.rmSync(outRoot, { recursive: true, force: true });
  }
  fs.mkdirSync(outRoot, { recursive: true });
  const dist = path.join(outRoot, "dist");
  const work = path.join(outRoot, "build");

  const args = ["-m", "PyInstaller", "--onedir", "--noconfirm", "--clean", "--name", `${cfg.toolName}-tool`,
    "--distpath", dist, "--workpath", work, "--specpath", outRoot];
  for (const pkg of cfg.collect) args.push("--collect-all", pkg);
  args.push(entryPath);

  console.log(`Building ${pipeline} -> ${dist} (collect-all: ${cfg.collect.join(", ")})`);
  const t0 = Date.now();
  const build = spawnSync(PY, args, { cwd: src, encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
  const buildLog = `${build.stdout || ""}${build.stderr || ""}`;
  console.log(buildLog.split("\n").slice(-40).join("\n"));
  const seconds = Math.round((Date.now() - t0) / 1000);

  const exeDir = path.join(dist, `${cfg.toolName}-tool`);
  const exePath = path.join(exeDir, `${cfg.toolName}-tool.exe`);
  const ok = fs.existsSync(exePath);
  console.log(`\nBuild finished in ${seconds}s. Exe present: ${ok} (${exePath})`);
  if (!ok) {
    console.error("PyInstaller did not produce the exe; see the build log above.");
    process.exit(1);
  }

  // the config next to the build is a template, not the real paths-filled config: whoever uses this build edits it for their own machine
  fs.copyFileSync(path.join(CLAUDE, pipeline, "config.json"), path.join(exeDir, "config.example.json"));

  // PowerShell helper scripts the pipeline ships (the user, 2026-11-15): carried along as plain .ps1 files, unmodified, so they can still be run
  const ps1Files = fs.existsSync(src) ? fs.readdirSync(src).filter((f) => f.toLowerCase().endsWith(".ps1")) : [];
  let ps1Note = "none";
  if (ps1Files.length) {
    const scriptsOut = path.join(exeDir, "scripts");
    fs.mkdirSync(scriptsOut, { recursive: true });
    for (const f of ps1Files) fs.copyFileSync(path.join(src, f), path.join(scriptsOut, f));
    ps1Note = ps1Files.map((f) => `scripts\\${f}`).join(", ");
  }
  console.log(`PowerShell helper scripts bundled: ${ps1Note}`);

  const notice = [
    "Compiled from a private source repository. All rights reserved: no redistribution, reverse engineering or reuse without the owner's permission.",
    "This package bundles the Python logic only. It still needs, on the machine that runs it:",
    "  - ffmpeg on PATH;",
    `  - ${cfg.note}`,
    `  - a config.json next to ${cfg.toolName}-tool.exe with paths valid on THAT machine (start from config.example.json, which still holds this PC's paths).`,
    ps1Files.length ? `This build also carries the PowerShell helper script(s) it ships with (${ps1Note}); run them from a PowerShell prompt as the pipeline's own docs describe, pointed at this folder.` : null,
    `Built ${new Date().toISOString()}.`,
  ].filter(Boolean).join("\n");
  fs.writeFileSync(path.join(exeDir, "NOTICE.txt"), notice, "utf-8");

  const size = dirSizeBytes(exeDir);
  console.log(`Output size: ${Math.round(size / (1024 * 1024))} MB`);

  if (!values["skip-smoke-test"]) {
    console.log(`\nSmoke test: ${cfg.toolName}-tool.exe --help`);
    const t = spawnSync(exePath, ["--help"], { encoding: "utf-8" });
    console.log((t.stdout || "").split("\n").slice(0, 8).join("\n"));
    console.log(`exit code: ${t.status}`);
  }
}

function dirSizeBytes(dir) {
  let total = 0;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    total += entry.isDirectory() ? dirSizeBytes(p) : fs.statSync(p).size;
  }
  return total;
}

main();
